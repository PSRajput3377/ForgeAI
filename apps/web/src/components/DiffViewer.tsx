"use client";

import { useEffect, useState } from "react";
import { getPRDiff, type DiffFile } from "@/lib/api";

/** Shows the proposed file contents for a PR proposal, before approval. */
export function DiffViewer({ approvalId }: { approvalId: string }) {
  const [files, setFiles] = useState<DiffFile[] | null>(null);

  useEffect(() => {
    getPRDiff(approvalId).then(setFiles).catch(() => setFiles([]));
  }, [approvalId]);

  if (files === null) return <p className="text-xs text-neutral-500">Loading diff…</p>;
  if (files.length === 0) return <p className="text-xs text-neutral-500">No files.</p>;

  return (
    <div className="space-y-3">
      {files.map((f) => (
        <div key={f.path} className="overflow-hidden rounded-md border border-neutral-800">
          <div className="bg-neutral-900 px-3 py-1 font-mono text-xs text-neutral-300">
            {f.path}
          </div>
          <pre className="overflow-x-auto bg-black/40 p-3 text-xs leading-relaxed">
            {f.content.split("\n").map((line, i) => (
              <div key={i} className="text-green-300">
                <span className="mr-3 select-none text-neutral-600">+</span>
                {line}
              </div>
            ))}
          </pre>
        </div>
      ))}
    </div>
  );
}
