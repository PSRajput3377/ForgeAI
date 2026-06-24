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

  if (!metrics) return <p className="text-sm text-neutral-500">Loading metrics…</p>;

  return (
    <div className="space-y-3 text-sm">
      <div className="flex gap-6">
        <Stat label="Tasks" value={String(metrics.tasks_total)} />
        <Stat label="Success" value={`${Math.round(metrics.success_rate * 100)}%`} />
      </div>
      <div>
        <p className="mb-1 text-xs uppercase text-neutral-500">Per agent</p>
        {Object.entries(metrics.agents).map(([name, s]) => (
          <div key={name} className="flex justify-between text-xs text-neutral-400">
            <span className="capitalize">{name}</span>
            <span>
              {Math.round(s.success_rate * 100)}% · {s.avg_duration.toFixed(2)}s · {s.runs} runs
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-2xl font-semibold">{value}</p>
      <p className="text-xs text-neutral-500">{label}</p>
    </div>
  );
}
