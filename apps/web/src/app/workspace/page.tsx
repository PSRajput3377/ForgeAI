"use client";

/**
 * Developer Workspace (Phase 6 + 11).
 *
 * The PR Approval Center is the centerpiece: pending proposals from the agent
 * pipeline, with Review (diff) → Approve (one-click → creates the GitHub PR) /
 * Reject. Below it, the live observability panels (agents, timeline, metrics)
 * driven by the backend event WebSocket.
 */
import { useEffect } from "react";
import { useEventStream } from "@/hooks/useEventStream";
import { AgentStatus } from "@/components/AgentStatus";
import { AgentTimeline } from "@/components/AgentTimeline";
import { ApprovalCenter } from "@/components/ApprovalCenter";
import { MetricsPanel } from "@/components/MetricsPanel";
import { TaskInput } from "@/components/TaskInput";
import { useAppStore } from "@/store/useAppStore";

export default function WorkspacePage() {
  const { events, status } = useEventStream();
  const projectId = useAppStore((s) => s.activeProjectId);
  const projectName = useAppStore((s) => s.activeProjectName);

  // No project selected → send the user to the chooser (the front door).
  useEffect(() => {
    if (!projectId) window.location.href = "/projects";
  }, [projectId]);

  const live = status === "open";
  return (
    <main className="mx-auto min-h-screen max-w-7xl p-6">
      <header className="mb-8 flex items-center justify-between">
        <div>
          <a
            href="/projects"
            className="mb-1 inline-block text-xs text-[var(--faint)] transition hover:text-[var(--muted)]"
          >
            ← All projects
          </a>
          <h1 className="text-2xl font-semibold tracking-tight">
            {projectName ?? "Workspace"}
          </h1>
        </div>
        <div className="flex items-center gap-3">
          <a href="/analytics" className="btn-ghost px-3 py-1.5 text-xs">
            Analytics →
          </a>
          <span className="chip inline-flex items-center gap-2 px-3 py-1.5 text-xs">
            <span
              className={`h-2 w-2 rounded-full ${
                live ? "bg-[var(--green)] pulse-ring" : status === "connecting" ? "bg-[var(--amber)]" : "bg-[var(--red)]"
              }`}
            />
            <span className="text-[var(--muted)]">{live ? "live" : status}</span>
          </span>
        </div>
      </header>

      {/* Entry point: describe a task and run the agent team */}
      <Panel title="New task" accent="var(--accent)" delay="0s">
        <TaskInput />
      </Panel>

      <div className="mt-6">
        <Panel title="Pending approvals" accent="var(--amber)" delay="0.05s">
          <ApprovalCenter />
        </Panel>
      </div>

      <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-[240px_1fr_300px]">
        <Panel title="Agents" accent="var(--accent-3)" delay="0.1s">
          <AgentStatus events={events} />
        </Panel>
        <Panel title="Timeline" accent="var(--accent)" delay="0.15s">
          <AgentTimeline events={events} />
        </Panel>
        <Panel title="Metrics" accent="var(--accent-2)" delay="0.2s">
          <MetricsPanel />
        </Panel>
      </div>
    </main>
  );
}

function Panel({
  title,
  accent,
  delay,
  children,
}: {
  title: string;
  accent: string;
  delay: string;
  children: React.ReactNode;
}) {
  return (
    <section className="glass rise p-5" style={{ animationDelay: delay }}>
      <div className="mb-4 flex items-center gap-2">
        <span className="h-3 w-1 rounded-full" style={{ background: accent }} />
        <h2 className="label">{title}</h2>
      </div>
      {children}
    </section>
  );
}
