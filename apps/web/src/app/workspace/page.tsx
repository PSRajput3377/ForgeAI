"use client";

/**
 * Developer Workspace — the live observability screen (Phase 6).
 *
 * Three panels: agent status (left), live timeline (center), metrics (right) —
 * all driven by the backend event WebSocket. Think Cursor + GitHub Actions +
 * LangSmith in one view.
 */
import { useEventStream } from "@/hooks/useEventStream";
import { AgentStatus } from "@/components/AgentStatus";
import { AgentTimeline } from "@/components/AgentTimeline";
import { MetricsPanel } from "@/components/MetricsPanel";

export default function WorkspacePage() {
  const { events, status } = useEventStream();

  return (
    <main className="min-h-screen p-6">
      <header className="mb-6 flex items-center justify-between">
        <h1 className="text-xl font-semibold">ForgeAI Workspace</h1>
        <span className="flex items-center gap-2 text-xs">
          <span
            className={`h-2 w-2 rounded-full ${
              status === "open" ? "bg-green-500" : status === "connecting" ? "bg-yellow-500" : "bg-red-500"
            }`}
          />
          {status === "open" ? "live" : status}
        </span>
      </header>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[220px_1fr_280px]">
        <Panel title="Agents">
          <AgentStatus events={events} />
        </Panel>
        <Panel title="Timeline">
          <AgentTimeline events={events} />
        </Panel>
        <Panel title="Metrics">
          <MetricsPanel />
        </Panel>
      </div>
    </main>
  );
}

function Panel({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="rounded-lg border border-neutral-800 p-4">
      <h2 className="mb-3 text-xs uppercase tracking-wide text-neutral-500">{title}</h2>
      {children}
    </section>
  );
}
