"use client";

import type { ForgeEvent } from "@/lib/api";

const AGENTS = [
  "planner",
  "research",
  "memory",
  "coder",
  "execute",
  "tests",
  "review",
  "git",
];

type State = "waiting" | "running" | "done";

/** Agent visualization — per-agent status derived from the event stream. */
export function AgentStatus({ events }: { events: ForgeEvent[] }) {
  const state: Record<string, State> = {};
  for (const e of events) {
    if (!e.agent) continue;
    if (e.type === "agent.started") state[e.agent] = "running";
    if (e.type === "agent.completed") state[e.agent] = "done";
  }

  return (
    <div className="space-y-1">
      {AGENTS.map((a) => {
        const s = state[a] ?? "waiting";
        return (
          <div key={a} className="flex items-center gap-2 text-sm">
            <span>{icon(s)}</span>
            <span className="capitalize text-neutral-300">{a}</span>
            <span className="text-xs text-neutral-500">{s}</span>
          </div>
        );
      })}
    </div>
  );
}

function icon(s: State): string {
  return s === "done" ? "✓" : s === "running" ? "⟳" : "…";
}
