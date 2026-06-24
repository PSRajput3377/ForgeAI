"use client";

import type { ForgeEvent } from "@/lib/api";

/** The Agent Timeline ⭐ — ordered list of events as they stream in. */
export function AgentTimeline({ events }: { events: ForgeEvent[] }) {
  if (events.length === 0) {
    return <p className="text-sm text-neutral-500">No events yet.</p>;
  }
  return (
    <ol className="space-y-1 font-mono text-xs">
      {events.map((e) => (
        <li key={e.tick} className="flex gap-3">
          <span className="w-10 text-neutral-600">#{e.tick}</span>
          <span className={eventColor(e.type)}>{e.type}</span>
          {e.agent && <span className="text-neutral-400">{e.agent}</span>}
        </li>
      ))}
    </ol>
  );
}

function eventColor(type: string): string {
  if (type.includes("failed") || type.includes("build.failed"))
    return "text-red-400";
  if (type.includes("completed") || type.includes("passed"))
    return "text-green-400";
  if (type.includes("started")) return "text-blue-400";
  return "text-neutral-300";
}
