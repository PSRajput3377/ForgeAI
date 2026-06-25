"use client";

import { useState } from "react";
import { GeneratedFiles } from "@/components/GeneratedFiles";
import { runAgents, type RunResult } from "@/lib/api";

/**
 * Task input — the way to *start* a run from the workspace. Submits the request
 * to POST /agents/run; the agents/timeline/metrics panels update live over the
 * WebSocket while the run executes, and the final verdict is shown here.
 */
export function TaskInput() {
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
      setResult(await runAgents(request));
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
    <div className="space-y-3">
      <div className="flex gap-3">
        <textarea
          value={task}
          onChange={(e) => setTask(e.target.value)}
          onKeyDown={onKeyDown}
          placeholder="Describe a task — e.g. “Add JWT authentication”"
          rows={2}
          disabled={running}
          className="flex-1 resize-none rounded-md border border-neutral-800 bg-neutral-950 px-3 py-2 text-sm text-neutral-100 placeholder:text-neutral-600 focus:border-neutral-600 focus:outline-none disabled:opacity-60"
        />
        <button
          onClick={submit}
          disabled={running || !task.trim()}
          className="shrink-0 self-stretch rounded-md bg-white px-5 text-sm font-medium text-black transition hover:bg-neutral-200 disabled:cursor-not-allowed disabled:opacity-40"
        >
          {running ? "Running…" : "Run"}
        </button>
      </div>

      <p className="text-xs text-neutral-600">
        ⌘/Ctrl + Enter to run. Watch the agents work live below.
      </p>

      {error && (
        <p className="rounded-md border border-red-900 bg-red-950/40 px-3 py-2 text-xs text-red-400">
          {error}
        </p>
      )}

      {result && (
        <div className="rounded-md border border-neutral-800 bg-neutral-950 px-3 py-2 text-xs text-neutral-300">
          <p>
            <span className="text-neutral-500">Verdict:</span>{" "}
            <span
              className={
                result.review_verdict === "approved" ? "text-green-400" : "text-yellow-400"
              }
            >
              {result.review_verdict}
            </span>{" "}
            · {result.tasks} tasks · {result.retries} retries ·{" "}
            {result.files_changed.length} files changed
          </p>
          {result.final_response && (
            <p className="mt-1 whitespace-pre-wrap text-neutral-400">{result.final_response}</p>
          )}
          {result.pr_approval_id && (
            <p className="mt-2 text-green-400">
              PR proposed — open <span className="text-neutral-500">Pending Approvals</span>{" "}
              to review and execute.
            </p>
          )}
        </div>
      )}

      {result && Object.keys(result.generated_files ?? {}).length > 0 && (
        <div className="rounded-lg border border-neutral-800 p-4">
          <h3 className="mb-3 text-xs uppercase tracking-wide text-neutral-500">
            Generated code
          </h3>
          <GeneratedFiles files={result.generated_files} />
        </div>
      )}
    </div>
  );
}
