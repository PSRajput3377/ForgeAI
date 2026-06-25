"use client";

/** Shows file contents returned from a completed agent run. */
export function GeneratedFiles({ files }: { files: Record<string, string> }) {
  const entries = Object.entries(files).sort(([a], [b]) => a.localeCompare(b));

  if (entries.length === 0) {
    return <p className="text-sm text-neutral-500">No generated files.</p>;
  }

  return (
    <div className="space-y-3">
      {entries.map(([path, content]) => (
        <div key={path} className="overflow-hidden rounded-md border border-neutral-800">
          <div className="bg-neutral-900 px-3 py-1 font-mono text-xs text-neutral-300">
            {path}
          </div>
          <pre className="max-h-96 overflow-auto bg-black/40 p-3 text-xs leading-relaxed text-neutral-200">
            {content}
          </pre>
        </div>
      ))}
    </div>
  );
}
