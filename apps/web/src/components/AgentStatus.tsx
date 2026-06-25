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
    <div className="relative">
      {/* vertical rail */}
      <div className="absolute bottom-3 left-[5px] top-3 w-px bg-[var(--panel-border)]" />
      <div className="space-y-2.5">
        {AGENTS.map((a) => {
          const s = state[a] ?? "waiting";
          return (
            <div key={a} className="relative flex items-center gap-3 text-sm">
              <Dot state={s} />
              <span
                className={`capitalize ${
                  s === "waiting" ? "text-[var(--faint)]" : "text-[var(--foreground)]"
                }`}
              >
                {a}
              </span>
              <span
                className={`ml-auto text-[11px] ${
                  s === "running"
                    ? "text-[var(--accent)]"
                    : s === "done"
                      ? "text-[var(--green)]"
                      : "text-[var(--faint)]"
                }`}
              >
                {s}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function Dot({ state }: { state: State }) {
  if (state === "running") {
    return (
      <span className="relative z-10 grid h-[11px] w-[11px] place-items-center">
        <span className="absolute h-[11px] w-[11px] rounded-full bg-[var(--accent)] pulse-ring" />
        <span className="spin-slow h-2 w-2 rounded-full border border-white/60 border-t-transparent" />
      </span>
    );
  }
  const color = state === "done" ? "var(--green)" : "var(--faint)";
  return (
    <span
      className="relative z-10 h-[11px] w-[11px] rounded-full"
      style={{
        background: state === "done" ? color : "transparent",
        border: state === "done" ? "none" : `1.5px solid ${color}`,
        boxShadow: state === "done" ? `0 0 10px -2px ${color}` : "none",
      }}
    />
  );
}
