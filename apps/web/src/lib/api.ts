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
