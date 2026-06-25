"use client";

import type { ForgeEvent } from "@/lib/api";

/**
 * The Agent Timeline ⭐ — a timestamped, human-readable activity log that
 * streams in live (e.g. "09:01:14  Planner Started").
 */
export function AgentTimeline({ events }: { events: ForgeEvent[] }) {
  if (events.length === 0) {
    return (
      <div className="flex h-40 items-center justify-center text-sm text-[var(--faint)]">
        Waiting for a run…
      </div>
    );
  }
  return (
    <ol className="max-h-[420px] space-y-0.5 overflow-y-auto font-mono text-xs">
      {events.map((e) => (
        <li
          key={e.tick}
          className="rise flex items-center gap-3 rounded-lg px-2 py-1.5 transition hover:bg-white/[0.03]"
        >
          <span className="w-[68px] shrink-0 text-[var(--faint)]">{clock(e.timestamp)}</span>
          <span
            className="h-2 w-2 shrink-0 rounded-full"
            style={{ background: dotColor(e.type), boxShadow: `0 0 8px -1px ${dotColor(e.type)}` }}
          />
          <span className="text-[var(--foreground)]/90">{label(e)}</span>
        </li>
      ))}
    </ol>
  );
}

/** Render an event as "Planner Started" / "Review Approved" / "PR Proposal Created". */
function label(e: ForgeEvent): string {
  const actor = e.agent ? title(e.agent) : "";
  switch (e.type) {
    case "run.started":
      return "Run Started";
    case "run.completed":
      return "Run Completed";
    case "agent.started":
      return `${actor} Started`;
    case "agent.completed":
      return `${actor} Completed`;
    case "agent.failed":
      return `${actor} Failed`;
    case "build.failed":
      return "Build Failed";
    case "build.passed":
      return "Build Passed";
    case "approval.requested":
      return "PR Proposal — Awaiting Approval";
    case "approval.resolved":
      return "Approval Resolved";
    default:
      return `${title(e.type.replace(/[._]/g, " "))}${actor ? ` (${actor})` : ""}`;
  }
}

function clock(ts: string | null): string {
  if (!ts) return "--:--:--";
  try {
    return new Date(ts).toLocaleTimeString("en-GB"); // HH:MM:SS
  } catch {
    return "--:--:--";
  }
}

function title(s: string): string {
  return s.replace(/\b\w/g, (c) => c.toUpperCase());
}

function dotColor(type: string): string {
  if (type.includes("failed")) return "var(--red)";
  if (type.includes("completed") || type.includes("passed") || type.includes("resolved"))
    return "var(--green)";
  if (type.includes("requested") || type.includes("approval")) return "var(--amber)";
  if (type.includes("started")) return "var(--accent)";
  return "var(--faint)";
}
