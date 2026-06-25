/** API + WebSocket base URLs derived from NEXT_PUBLIC_API_URL. */
export const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export const WS_URL = API_URL.replace(/^http/, "ws");

/** Bearer auth header from the persisted access token (empty if signed out). */
export function authHeaders(): Record<string, string> {
  const token =
    typeof window !== "undefined" ? window.localStorage.getItem("forge.access") : null;
  return token ? { Authorization: `Bearer ${token}` } : {};
}

// --- Projects & onboarding (Phase 13) ---

export interface Project {
  id: string;
  workspace_id: string;
  name: string;
  description: string | null;
  path: string | null;
  repo: string | null;
  starter: string | null;
}

export interface Starter {
  id: string;
  name: string;
  description: string;
  tags: string[];
}

export async function listStarters(): Promise<Starter[]> {
  const res = await fetch(`${API_URL}/projects/starters`);
  if (!res.ok) return [];
  return (await res.json()).starters ?? [];
}

export async function listProjects(workspaceId: string): Promise<Project[]> {
  const res = await fetch(`${API_URL}/projects?workspace_id=${workspaceId}`, {
    headers: authHeaders(),
  });
  if (!res.ok) return [];
  return (await res.json()).projects ?? [];
}

/** Ensure the signed-in user has a workspace; create a default org if not.
 *  Returns the workspace id. */
export async function ensureWorkspace(): Promise<string | null> {
  // Try to reuse a workspace the user already owns by creating an org only once.
  const res = await fetch(`${API_URL}/orgs`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({ name: "My Workspace" }),
  });
  if (!res.ok) return null;
  return (await res.json()).workspace_id ?? null;
}

export async function createProject(
  workspaceId: string,
  name: string
): Promise<Project | null> {
  const res = await fetch(`${API_URL}/projects`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({ workspace_id: workspaceId, name }),
  });
  if (!res.ok) return null;
  return res.json();
}

export async function bootstrapProject(
  workspaceId: string,
  name: string,
  starter: string
): Promise<(Project & { scaffolded_files: string[] }) | null> {
  const res = await fetch(`${API_URL}/projects/bootstrap`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({ workspace_id: workspaceId, name, starter }),
  });
  if (!res.ok) return null;
  return res.json();
}

export interface ForgeEvent {
  type: string;
  run_id: string | null;
  agent: string | null;
  payload: Record<string, unknown>;
  tick: number;
  timestamp: string | null;
}

export interface RunResult {
  final_response: string;
  review_verdict: string;
  tasks: number;
  files_changed: string[];
  generated_files: Record<string, string>;
  retries: number;
  pr_approval_id?: string | null;
  project_id?: string | null;
  written_files?: string[];
}

/** Kick off the multi-agent workflow for a task. Resolves when the run finishes;
 *  the timeline/agents/metrics panels update live over the WebSocket meanwhile. */
export async function runAgents(
  userRequest: string,
  projectId?: string
): Promise<RunResult> {
  const res = await fetch(`${API_URL}/agents/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({ user_request: userRequest, project_id: projectId ?? null }),
  });
  if (!res.ok) {
    const detail = (await res.json().catch(() => ({}))).detail;
    throw new Error(detail ?? `Run failed (${res.status})`);
  }
  return res.json();
}

export async function getMetrics() {
  const res = await fetch(`${API_URL}/observability/metrics`);
  return res.json();
}

// --- Agent Analytics (Phase 12.8) ---

export interface Stats {
  runs: number;
  success_rate: number;
  mean_score: number;
  avg_retries: number;
  avg_time_s: number;
  accepted_pr_rate: number | null;
}

export interface PromptVersionStats {
  active_version: string | null;
  versions: Record<string, Stats>;
}

export async function getAnalyticsOverview(): Promise<Stats> {
  const res = await fetch(`${API_URL}/analytics/overview`);
  return res.json();
}

export async function getPromptComparison(): Promise<Record<string, PromptVersionStats>> {
  const res = await fetch(`${API_URL}/analytics/prompts`);
  if (!res.ok) return {};
  return (await res.json()).roles ?? {};
}

export async function getBenchmarkTrend(): Promise<
  { forge_version: string; pass_rate: number }[]
> {
  const res = await fetch(`${API_URL}/analytics/benchmarks/trend`);
  if (!res.ok) return [];
  return (await res.json()).trend ?? [];
}

export async function getTimeline(runId: string) {
  const res = await fetch(`${API_URL}/observability/timeline/${runId}`);
  return res.json();
}

// --- GitHub PR approval center ---

export interface PRProposal {
  approval_id: string;
  status: "pending" | "approved" | "rejected";
  repo: string;
  task: string;
  branch: string;
  pr_title: string;
  pr_summary: string;
  files_changed: string[];
  testing: string;
  pr_url: string | null;
}

export interface DiffFile {
  path: string;
  content: string;
}

export async function listPendingPRs(): Promise<PRProposal[]> {
  const res = await fetch(`${API_URL}/github/pr/pending`);
  if (!res.ok) return [];
  return (await res.json()).pending ?? [];
}

export async function getPRDiff(approvalId: string): Promise<DiffFile[]> {
  const res = await fetch(`${API_URL}/github/pr/${approvalId}/diff`);
  if (!res.ok) return [];
  return (await res.json()).files ?? [];
}

async function prAction(approvalId: string, action: string) {
  const res = await fetch(`${API_URL}/github/pr/${approvalId}/${action}`, {
    method: "POST",
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    const detail = typeof body.detail === "string" ? body.detail : undefined;
    throw new Error(detail ?? `${action} failed (${res.status})`);
  }
  return res.json();
}

export const approvePR = (id: string) => prAction(id, "approve");
export const rejectPR = (id: string) => prAction(id, "reject");
export const executePR = (id: string) => prAction(id, "execute");
