/** API + WebSocket base URLs derived from NEXT_PUBLIC_API_URL. */
export const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export const WS_URL = API_URL.replace(/^http/, "ws");

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
}

/** Kick off the multi-agent workflow for a task. Resolves when the run finishes;
 *  the timeline/agents/metrics panels update live over the WebSocket meanwhile. */
export async function runAgents(
  userRequest: string,
  projectId?: string
): Promise<RunResult> {
  const res = await fetch(`${API_URL}/agents/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
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
