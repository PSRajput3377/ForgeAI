"use client";

import type { ForgeEvent } from "@/lib/api";

/**
 * The Agent Timeline ⭐ — a timestamped, human-readable activity log that
 * streams in live (e.g. "09:01:14  Planner Started").
 */
export function AgentTimeline({ events }: { events: ForgeEvent[] }) {
  if (events.length === 0) {
    return <p className="text-sm text-neutral-500">No events yet.</p>;
  }
  return (
    <ol className="space-y-1 font-mono text-xs">
      {events.map((e) => (
        <li key={e.tick} className="flex gap-3">
          <span className="w-20 shrink-0 text-neutral-600">{clock(e.timestamp)}</span>
          <span className={`w-1.5 shrink-0 ${dotColor(e.type)}`}>●</span>
          <span className="text-neutral-200">{label(e)}</span>
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
  if (type.includes("failed")) return "text-red-400";
  if (type.includes("completed") || type.includes("passed") || type.includes("resolved"))
    return "text-green-400";
  if (type.includes("requested") || type.includes("approval")) return "text-yellow-400";
  if (type.includes("started")) return "text-blue-400";
  return "text-neutral-400";
}
