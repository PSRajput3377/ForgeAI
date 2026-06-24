"use client";

/**
 * Developer Workspace (Phase 6 + 11).
 *
 * The PR Approval Center is the centerpiece: pending proposals from the agent
 * pipeline, with Review (diff) → Approve (one-click → creates the GitHub PR) /
 * Reject. Below it, the live observability panels (agents, timeline, metrics)
 * driven by the backend event WebSocket.
 */
import { useEventStream } from "@/hooks/useEventStream";
import { AgentStatus } from "@/components/AgentStatus";
import { AgentTimeline } from "@/components/AgentTimeline";
import { ApprovalCenter } from "@/components/ApprovalCenter";
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

      {/* Centerpiece: PR Approval Center */}
      <Panel title="Pending Approvals">
        <ApprovalCenter />
      </Panel>

      <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-[220px_1fr_280px]">
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
