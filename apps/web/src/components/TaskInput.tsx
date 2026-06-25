"use client";

import { useState } from "react";
import { GeneratedFiles } from "@/components/GeneratedFiles";
import { runAgents, type RunResult } from "@/lib/api";
import { useAppStore } from "@/store/useAppStore";

/**
 * Task input — the way to *start* a run from the workspace. Submits the request
 * to POST /agents/run against the active project; the agents/timeline/metrics
 * panels update live over the WebSocket, and the final verdict is shown here.
 */
// One-click starter tasks so a freshly-opened project isn't a blank box.
const SUGGESTIONS = [
  "Add a /status endpoint that returns uptime",
  "Add a health check with a database ping",
  "Write tests for the existing endpoints",
];

export function TaskInput() {
  const projectId = useAppStore((s) => s.activeProjectId);
  const [task, setTask] = useState("");
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<RunResult | null>(null);

  async function submit() {
    const request = task.trim();
    if (!request || running) return;
    setRunning(true);
    setError(null);
    setResult(null);
    try {
      setResult(await runAgents(request, projectId ?? undefined));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Run failed");
    } finally {
      setRunning(false);
    }
  }

  function onKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    // Cmd/Ctrl+Enter submits; plain Enter inserts a newline.
    if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
      e.preventDefault();
      submit();
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex gap-3">
        <textarea
          value={task}
          onChange={(e) => setTask(e.target.value)}
          onKeyDown={onKeyDown}
          placeholder="Describe a task — e.g. “Add JWT authentication”"
          rows={2}
          disabled={running}
          className="flex-1 resize-none rounded-xl border border-[var(--panel-border)] bg-black/30 px-4 py-3 text-sm text-[var(--foreground)] placeholder:text-[var(--faint)] transition focus:border-[var(--accent)] focus:outline-none focus:ring-2 focus:ring-[var(--accent)]/20 disabled:opacity-60"
        />
        <button
          onClick={submit}
          disabled={running || !task.trim()}
          className="btn-primary inline-flex shrink-0 items-center gap-2 self-stretch px-6 text-sm"
        >
          {running ? (
            <>
              <span className="spin-slow h-3.5 w-3.5 rounded-full border-2 border-white/70 border-t-transparent" />
              Running
            </>
          ) : (
            <>Run ↵</>
          )}
        </button>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <span className="text-xs text-[var(--faint)]">Try</span>
        {SUGGESTIONS.map((s) => (
          <button
            key={s}
            onClick={() => setTask(s)}
            disabled={running}
            className="chip px-3 py-1 text-xs text-[var(--muted)] transition hover:border-white/20 hover:text-[var(--foreground)] disabled:opacity-50"
          >
            {s}
          </button>
        ))}
        <span className="ml-auto text-xs text-[var(--faint)]">⌘/Ctrl + Enter to run</span>
      </div>

      {error && (
        <div className="rise rounded-xl border border-[var(--red)]/30 bg-[var(--red)]/10 px-4 py-3 text-xs text-[var(--red)]">
          {error}
        </div>
      )}

      {result && (
        <div className="rise rounded-xl border border-[var(--panel-border)] bg-black/20 px-4 py-3 text-xs">
          <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
            <StatusBadge verdict={result.review_verdict} />
            <Stat label="tasks" value={result.tasks} />
            <Stat label="retries" value={result.retries} />
            <Stat label="files" value={result.files_changed.length} />
          </div>
          {result.final_response && (
            <p className="mt-2 whitespace-pre-wrap leading-relaxed text-[var(--muted)]">
              {result.final_response}
            </p>
          )}
          {result.pr_approval_id && (
            <p className="mt-2 text-[var(--green)]">
              ✓ PR proposed — open{" "}
              <span className="text-[var(--muted)]">Pending approvals</span> to review &amp; execute.
            </p>
          )}
        </div>
      )}

      {result && Object.keys(result.generated_files ?? {}).length > 0 && (
        <div className="rise rounded-xl border border-[var(--panel-border)] bg-black/20 p-4">
          <h3 className="label mb-3">Generated code</h3>
          <GeneratedFiles files={result.generated_files} />
        </div>
      )}
    </div>
  );
}

function StatusBadge({ verdict }: { verdict: string }) {
  const ok = verdict === "approved";
  return (
    <span
      className="inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium"
      style={{
        background: ok ? "rgba(52,211,153,0.12)" : "rgba(251,191,36,0.12)",
        color: ok ? "var(--green)" : "var(--amber)",
      }}
    >
      <span
        className="h-1.5 w-1.5 rounded-full"
        style={{ background: ok ? "var(--green)" : "var(--amber)" }}
      />
      {verdict}
    </span>
  );
}

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <span className="text-[var(--muted)]">
      <span className="font-semibold text-[var(--foreground)]">{value}</span> {label}
    </span>
  );
}
