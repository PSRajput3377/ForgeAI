"use client";

/**
 * PR Approval Center (Phase 11, Priority 1) — the UI centerpiece.
 *
 * Lists pending PR proposals from the agent pipeline. A human can Review the
 * diff, then Approve (→ one-click executes the GitHubWorkflow and shows the PR
 * URL) or Reject. Nothing is written to GitHub without an explicit Approve.
 */
import { useCallback, useEffect, useState } from "react";
import {
  approvePR,
  executePR,
  listPendingPRs,
  rejectPR,
  type PRProposal,
} from "@/lib/api";
import { DiffViewer } from "@/components/DiffViewer";

export function ApprovalCenter() {
  const [proposals, setProposals] = useState<PRProposal[]>([]);
  const [openDiff, setOpenDiff] = useState<string | null>(null);
  const [prUrls, setPrUrls] = useState<Record<string, string>>({});
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(() => {
    listPendingPRs().then(setProposals).catch(() => {});
  }, []);

  useEffect(() => {
    refresh();
    const id = setInterval(refresh, 4000);
    return () => clearInterval(id);
  }, [refresh]);

  async function onApprove(id: string) {
    setBusy(id);
    setError(null);
    try {
      await approvePR(id);
      const result = await executePR(id); // one-click: approve → create PR
      setPrUrls((u) => ({ ...u, [id]: result.pr_url }));
      refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to create PR on GitHub");
    } finally {
      setBusy(null);
    }
  }

  async function onReject(id: string) {
    setBusy(id);
    try {
      await rejectPR(id);
      refresh();
    } finally {
      setBusy(null);
    }
  }

  if (proposals.length === 0 && Object.keys(prUrls).length === 0) {
    return <p className="text-sm text-neutral-500">No pending approvals.</p>;
  }

  return (
    <div className="space-y-4">
      {error && (
        <p className="rounded-md border border-red-900 bg-red-950/40 px-3 py-2 text-xs text-red-400">
          {error}
        </p>
      )}
      {proposals.map((p) => (
        <div key={p.approval_id} className="rounded-lg border border-neutral-800 p-4">
          <div className="flex items-start justify-between">
            <div>
              <h3 className="font-medium">{p.pr_title}</h3>
              <p className="mt-1 font-mono text-xs text-neutral-400">
                branch: {p.branch} · {p.repo}
              </p>
              <p className="mt-1 text-xs text-yellow-400">● Awaiting approval</p>
            </div>
            <span className="text-xs text-neutral-500">
              {p.files_changed.length} file(s)
            </span>
          </div>

          <div className="mt-3 flex gap-2">
            <button
              onClick={() => setOpenDiff(openDiff === p.approval_id ? null : p.approval_id)}
              className="rounded-md border border-neutral-700 px-3 py-1 text-xs hover:bg-neutral-900"
            >
              {openDiff === p.approval_id ? "Hide diff" : "Review"}
            </button>
            <button
              disabled={busy === p.approval_id}
              onClick={() => onApprove(p.approval_id)}
              className="rounded-md bg-green-600 px-3 py-1 text-xs font-medium hover:bg-green-500 disabled:opacity-50"
            >
              {busy === p.approval_id ? "Creating PR…" : "Approve"}
            </button>
            <button
              disabled={busy === p.approval_id}
              onClick={() => onReject(p.approval_id)}
              className="rounded-md bg-red-600/80 px-3 py-1 text-xs font-medium hover:bg-red-600 disabled:opacity-50"
            >
              Reject
            </button>
          </div>

          {openDiff === p.approval_id && (
            <div className="mt-3">
              <DiffViewer approvalId={p.approval_id} />
            </div>
          )}
        </div>
      ))}

      {Object.entries(prUrls).map(([id, url]) => (
        <div key={id} className="rounded-lg border border-green-800 bg-green-950/30 p-4">
          <p className="text-sm text-green-300">✓ Pull request created</p>
          <a href={url} target="_blank" rel="noreferrer" className="text-xs text-green-400 underline">
            {url}
          </a>
        </div>
      ))}
    </div>
  );
}
