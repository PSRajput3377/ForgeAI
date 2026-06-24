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
}

export async function getMetrics() {
  const res = await fetch(`${API_URL}/observability/metrics`);
  return res.json();
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
  if (!res.ok) throw new Error((await res.json()).detail ?? `${action} failed`);
  return res.json();
}

export const approvePR = (id: string) => prAction(id, "approve");
export const rejectPR = (id: string) => prAction(id, "reject");
export const executePR = (id: string) => prAction(id, "execute");
