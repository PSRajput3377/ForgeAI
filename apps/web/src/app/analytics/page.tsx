"use client";

/**
 * Agent Analytics (Phase 12.8).
 *
 * Surfaces the measurement substrate (12.1–12.7): overall run stats, prompt
 * version comparison (with a "promote" hint — promotion itself is an
 * approval-gated action, not automatic), and the benchmark trend across
 * ForgeAI versions.
 */
import { useEffect, useState } from "react";
import {
  getAnalyticsOverview,
  getBenchmarkTrend,
  getIntegrationStatus,
  getPromptComparison,
  type IntegrationStatus,
  type PromptVersionStats,
  type Stats,
} from "@/lib/api";

export default function AnalyticsPage() {
  const [overview, setOverview] = useState<Stats | null>(null);
  const [prompts, setPrompts] = useState<Record<string, PromptVersionStats>>({});
  const [trend, setTrend] = useState<{ forge_version: string; pass_rate: number }[]>([]);
  const [integrations, setIntegrations] = useState<IntegrationStatus | null>(null);

  useEffect(() => {
    const load = () => {
      getAnalyticsOverview().then(setOverview).catch(() => {});
      getPromptComparison().then(setPrompts).catch(() => {});
      getBenchmarkTrend().then(setTrend).catch(() => {});
      getIntegrationStatus().then(setIntegrations).catch(() => {});
    };
    load();
    const id = setInterval(load, 5000);
    return () => clearInterval(id);
  }, []);

  return (
    <main className="mx-auto min-h-screen max-w-5xl p-6 py-10">
      <header className="rise mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Agent Analytics</h1>
          <p className="mt-1 text-sm text-[var(--muted)]">
            How the team performs — and how it&apos;s improving.
          </p>
        </div>
        <a href="/workspace" className="btn-ghost px-3 py-1.5 text-xs">
          ← Workspace
        </a>
      </header>

      <Panel title="Overview">
        {overview && overview.runs > 0 ? (
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
            <Stat label="Runs" value={String(overview.runs)} />
            <Stat label="Success" value={pct(overview.success_rate)} />
            <Stat label="Mean score" value={overview.mean_score.toFixed(2)} />
            <Stat label="Avg retries" value={overview.avg_retries.toFixed(2)} />
            <Stat label="Avg time" value={`${overview.avg_time_s.toFixed(2)}s`} />
            <Stat
              label="PR accepted"
              value={overview.accepted_pr_rate === null ? "—" : pct(overview.accepted_pr_rate)}
            />
          </div>
        ) : (
          <Empty>No runs recorded yet. Start a task in the Workspace.</Empty>
        )}
      </Panel>

      <div className="mt-6">
        <Panel title="Prompt comparison">
          {Object.keys(prompts).length === 0 ? (
            <Empty>No prompt-version data yet — runs record the versions they used.</Empty>
          ) : (
            <div className="space-y-4">
              {Object.entries(prompts).map(([role, data]) => (
                <PromptRole key={role} role={role} data={data} />
              ))}
            </div>
          )}
        </Panel>
      </div>

      <div className="mt-6">
        <Panel title="Benchmark trend">
          {trend.length === 0 ? (
            <Empty>No benchmark runs recorded yet.</Empty>
          ) : (
            <div className="space-y-1 text-sm">
              {trend.map((t, i) => (
                <div key={i} className="flex items-center gap-3">
                  <span className="w-32 text-neutral-400">{t.forge_version}</span>
                  <div className="h-2 flex-1 overflow-hidden rounded bg-neutral-800">
                    <div
                      className="h-full bg-green-600"
                      style={{ width: `${Math.round(t.pass_rate * 100)}%` }}
                    />
                  </div>
                  <span className="w-12 text-right text-neutral-300">{pct(t.pass_rate)}</span>
                </div>
              ))}
            </div>
          )}
        </Panel>
      </div>

      <div className="mt-6">
        <Panel title="Integrations">
          {!integrations ? (
            <Empty>Loading…</Empty>
          ) : (
            <>
              <p className="mb-3 text-xs text-neutral-500">
                Honest readiness — <span className="text-neutral-300">live</span> talks to the real
                system; <span className="text-neutral-300">simulated</span> is interface-complete,
                validated against an in-memory fake.
              </p>
              <div className="flex flex-wrap gap-2">
                <ModeChip label="GitHub provider" mode={integrations.github_mode} />
                {integrations.connectors.map((c) => (
                  <ModeChip key={c.system} label={c.system} mode={c.mode} />
                ))}
              </div>
            </>
          )}
        </Panel>
      </div>
    </main>
  );
}

function ModeChip({ label, mode }: { label: string; mode: string }) {
  const live = mode === "live";
  return (
    <span className="inline-flex items-center gap-1.5 rounded-md border border-neutral-800 px-2.5 py-1 text-xs">
      <span className={`h-1.5 w-1.5 rounded-full ${live ? "bg-green-500" : "bg-yellow-500"}`} />
      <span className="capitalize text-neutral-300">{label}</span>
      <span className={live ? "text-green-400" : "text-yellow-500"}>{mode}</span>
    </span>
  );
}

function PromptRole({ role, data }: { role: string; data: PromptVersionStats }) {
  const versions = Object.entries(data.versions);
  // The non-active version with the highest mean score is a promote candidate.
  const best = versions
    .filter(([v]) => v !== data.active_version)
    .sort((a, b) => b[1].mean_score - a[1].mean_score)[0];
  const active = data.active_version ? data.versions[data.active_version] : undefined;
  const promote = best && active && best[1].mean_score > active.mean_score ? best[0] : null;

  return (
    <div className="rounded-md border border-neutral-800 p-3">
      <p className="mb-2 text-sm font-medium capitalize">{role}</p>
      <div className="space-y-1">
        {versions
          .sort((a, b) => a[0].localeCompare(b[0]))
          .map(([version, s]) => (
            <div key={version} className="flex items-center gap-3 text-xs text-neutral-400">
              <span className="w-10">{version}</span>
              {version === data.active_version && (
                <span className="rounded-full bg-[var(--accent)]/15 px-2 py-0.5 text-[var(--accent)]">
                  active
                </span>
              )}
              <span>{pct(s.mean_score, true)} score</span>
              <span className="text-neutral-600">·</span>
              <span>{pct(s.success_rate)} success</span>
              <span className="text-neutral-600">·</span>
              <span>{s.runs} runs</span>
            </div>
          ))}
      </div>
      {promote && (
        <p className="mt-2 text-xs text-yellow-400">
          {promote} scores higher than the active version — consider promoting it (requires
          approval).
        </p>
      )}
    </div>
  );
}

function pct(value: number, ofOne = false) {
  return `${Math.round(value * 100)}${ofOne ? "" : "%"}`;
}

function Panel({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="glass rise p-5">
      <div className="mb-4 flex items-center gap-2">
        <span className="h-3 w-1 rounded-full bg-[var(--accent)]" />
        <h2 className="label">{title}</h2>
      </div>
      {children}
    </section>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-[var(--panel-border)] bg-black/20 px-4 py-3">
      <p className="text-2xl font-semibold">{value}</p>
      <p className="mt-0.5 text-xs text-[var(--faint)]">{label}</p>
    </div>
  );
}

function Empty({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex h-20 items-center justify-center text-sm text-[var(--faint)]">
      {children}
    </div>
  );
}
