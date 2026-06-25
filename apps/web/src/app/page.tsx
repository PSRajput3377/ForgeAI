/**
 * Landing page — the hero. Sets the tone: a coordinated AI engineering team
 * that ships and then improves itself.
 */
import { ApiStatus } from "@/components/ApiStatus";

const PIPELINE = ["Manager", "Planner", "Research", "Coder", "Tests", "Review", "PR"];

const FEATURES = [
  {
    title: "A team, not a chatbot",
    body: "Ten specialist agents plan, research, code, test, and review — coordinated by an explicit workflow graph.",
    accent: "var(--accent)",
  },
  {
    title: "Watch it work, live",
    body: "Every step streams to the workspace over WebSockets. Generated code lands in a real project on disk.",
    accent: "var(--accent-3)",
  },
  {
    title: "It improves itself",
    body: "Every run is scored, stored, and compared. Prompt A/B, benchmarks, and failure memory — all gated.",
    accent: "var(--accent-2)",
  },
];

export default function Home() {
  return (
    <main className="relative mx-auto flex min-h-screen max-w-5xl flex-col items-center justify-center px-6 py-20">
      {/* top status chip */}
      <div className="rise mb-10">
        <ApiStatus />
      </div>

      {/* hero */}
      <div className="rise text-center" style={{ animationDelay: "0.05s" }}>
        <div className="chip mx-auto mb-6 inline-flex items-center gap-2 px-3 py-1 text-xs text-[var(--muted)]">
          <span className="h-1.5 w-1.5 rounded-full bg-[var(--green)]" />
          Autonomous AI Engineering Platform
        </div>
        <h1 className="gradient-text text-6xl font-bold tracking-tight sm:text-7xl">ForgeAI</h1>
        <p className="mx-auto mt-5 max-w-2xl text-lg leading-relaxed text-[var(--muted)]">
          A coordinated team of AI engineers that plans, codes, tests, reviews, and ships —
          then <span className="text-[var(--foreground)]">measures and improves itself</span> across
          every run.
        </p>
      </div>

      {/* animated pipeline preview */}
      <div
        className="rise mt-10 flex flex-wrap items-center justify-center gap-2"
        style={{ animationDelay: "0.12s" }}
      >
        {PIPELINE.map((stage, i) => (
          <div key={stage} className="flex items-center gap-2">
            <span className="chip px-3 py-1.5 text-xs font-medium text-[var(--foreground)]/90">
              {stage}
            </span>
            {i < PIPELINE.length - 1 && <span className="text-[var(--faint)]">→</span>}
          </div>
        ))}
      </div>

      {/* CTAs */}
      <div className="rise mt-10 flex gap-3" style={{ animationDelay: "0.18s" }}>
        <a href="/login" className="btn-primary px-6 py-2.5 text-sm">
          Get started
        </a>
        <a href="/projects" className="btn-ghost px-6 py-2.5 text-sm">
          Open projects →
        </a>
      </div>

      {/* feature trio */}
      <div className="mt-20 grid w-full grid-cols-1 gap-5 sm:grid-cols-3">
        {FEATURES.map((f, i) => (
          <div
            key={f.title}
            className="glass glass-hover rise p-6"
            style={{ animationDelay: `${0.25 + i * 0.07}s` }}
          >
            <span
              className="mb-4 block h-9 w-9 rounded-xl"
              style={{
                background: `linear-gradient(140deg, ${f.accent}, transparent 80%)`,
                boxShadow: `0 8px 24px -10px ${f.accent}`,
              }}
            />
            <h3 className="mb-2 text-sm font-semibold">{f.title}</h3>
            <p className="text-sm leading-relaxed text-[var(--muted)]">{f.body}</p>
          </div>
        ))}
      </div>

      <p className="mt-16 text-xs text-[var(--faint)]">
        13 phases · 333 tests · runs fully offline · local models
      </p>
    </main>
  );
}
