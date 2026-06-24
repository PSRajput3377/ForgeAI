# Phase 12 — Autonomous Engineering Team & Self-Improving Agent System

Spec: [`specs/self-improvement-spec.md`](../../specs/self-improvement-spec.md).

Phase 12 turns the static pipeline into a system that improves across runs. Per
the spec's guiding constraint, it splits into a **Foundation** (buildable and
offline-testable now) and **Learning loops** (scaffolded now, switched on once
real usage data exists). We build one sub-phase at a time and do not jump ahead.

## Sub-phase sequence

Each sub-phase is independently shippable: offline tests green, ruff + black
clean, docs updated, and pushed (per project convention).

| Sub | Name | Builds | Depends on |
|-----|------|--------|-----------|
| **12.1** | Evaluation Engine | `Evaluation` record + versioned rubric scorer, wired post-run; in-memory store behind the Postgres seam | — |
| **12.2** | Performance Database | `evaluations` table + derived `agent_stats` rollup; sliceable queries | 12.1 |
| **12.3** | Prompt Versioning | Versioned, addressable prompts; `system_prompt(role)` unchanged; per-run version recording | 12.1 |
| **12.4** | Reflection Memory + Failure KB | Error→Fix→Store→Reuse; `failures` table; signature match + reuse | 12.1 |
| **12.5** | Benchmark Suite | Versioned scenarios + harness; offline (echo) and real-model modes; `benchmarks`/`benchmark_results` | 12.1, 12.2 |
| **12.6** | Multi-Agent Debate | N independent planner attempts + Review-as-judge; off by default; deterministic under `EchoModel` | 12.3 |
| **12.7** | Dynamic Agent Selection | Rule-based task-type classifier behind a strategy interface; recorded rationale | 12.1 |
| **12.8** | Agent Analytics dashboard | New tab: per-agent deltas + prompt comparison; *Promote* as approval-gated action | 12.2, 12.3 |
| **12.9** | Learning-loop scaffolds | A/B promotion, workflow optimization, PR-outcome backfill as interfaces with safe defaults + approval gates; none auto-acts | 12.2, 12.3, 12.8 |
| **12.10** | Marketplace / Plugin system *(optional, independent)* | Permissioned registration + discovery of contract-satisfying agents | agent-spec |

**Recommended stop line for "Phase 12 foundation done":** through **12.8**.
12.9 lands the seams but stays inert until data exists; 12.10 is independent and
can follow on its own timeline.

## Why this order

- **12.1 first** — nothing can be compared until runs are measured. Everything
  downstream reads `Evaluation` records.
- **12.2 before 12.5/12.8** — benchmarking and analytics both need the stats
  rollup to exist.
- **12.3 before 12.6/12.8** — debate and the prompt-comparison UI both key off
  versioned prompts.
- **12.4 is parallel-safe** — Reflection memory only needs the storage seam from
  12.1; it can be built any time after.
- **12.9 last among the foundation** — promotion/optimization read the analytics
  and version data, and must be gated, so they come after the surfaces exist.

## Guardrails carried from the spec

- Foundation is testable with `EchoModel` / `FakeGitHubProvider` / in-memory
  stores — **no real models or services** required.
- Prompt versions are **append-only**; no in-place mutation.
- No auto-promotion or graph mutation from data without a documented sample
  threshold **and** explicit approval — consistent with the platform's
  approval-gated writes.
- `agent_stats` is **derived**, never an independent writable source of truth.
- Learning loops sit behind interfaces so "going live is just config."

## Per-sub-phase definition of done

1. Spec acceptance criteria for that component are met.
2. Offline tests cover it (deterministic, no network).
3. `ruff check` + `black --check` clean.
4. Docs updated (and an ADR for 12.1's measurement-substrate design).
5. Committed and pushed.
