"use client";

import { useEffect, useState } from "react";
import { getMetrics } from "@/lib/api";

interface Metrics {
  tasks_total: number;
  success_rate: number;
  agents: Record<string, { success_rate: number; avg_duration: number; runs: number }>;
}

/** Metrics dashboard panel — periodically pulls the metrics snapshot. */
export function MetricsPanel() {
  const [metrics, setMetrics] = useState<Metrics | null>(null);

  useEffect(() => {
    const load = () => getMetrics().then(setMetrics).catch(() => {});
    load();
    const id = setInterval(load, 5000);
    return () => clearInterval(id);
  }, []);

  if (!metrics)
    return (
      <div className="flex h-24 items-center justify-center text-sm text-[var(--faint)]">
        Loading…
      </div>
    );

  return (
    <div className="space-y-4 text-sm">
      <div className="grid grid-cols-2 gap-3">
        <Stat label="Tasks" value={String(metrics.tasks_total)} />
        <Stat label="Success" value={`${Math.round(metrics.success_rate * 100)}%`} accent />
      </div>
      <div>
        <p className="label mb-2">Per agent</p>
        <div className="space-y-1.5">
          {Object.entries(metrics.agents).map(([name, s]) => (
            <div key={name} className="flex items-center justify-between text-xs">
              <span className="capitalize text-[var(--foreground)]/80">{name}</span>
              <span className="text-[var(--muted)]">
                {Math.round(s.success_rate * 100)}% · {s.avg_duration.toFixed(2)}s · {s.runs}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function Stat({ label, value, accent }: { label: string; value: string; accent?: boolean }) {
  return (
    <div className="rounded-xl border border-[var(--panel-border)] bg-black/20 p-3">
      <p
        className={`text-2xl font-semibold ${accent ? "text-[var(--green)]" : "text-[var(--foreground)]"}`}
      >
        {value}
      </p>
      <p className="mt-0.5 text-xs text-[var(--faint)]">{label}</p>
    </div>
  );
}
