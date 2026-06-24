# Self-Improvement Specification (Phase 12)

How ForgeAI **measures itself and improves over time** — turning the static
pipeline (`Manager → Planner → Research → Coder → Testing → Review → PR`) into a
system whose quality rises across runs *without code changes*.

> `docs/` explains **how** ForgeAI works today.
> `specs/` defines **what** each component must do. (ADR-0013)

This spec extends, and does not replace, [`evaluation-spec.md`](evaluation-spec.md):
that spec defines *whether* a run is good; this one defines how we **record,
compare, and act on** that judgement over many runs.

## Guiding constraint — learning needs real data

Self-improvement loops are only meaningful once there is run history to learn
from (real GitHub validation, production deployment, real users, real usage).
This spec therefore splits Phase 12 into two halves with a hard line between
them:

| Half | Depends on real data? | Status target |
|------|----------------------|---------------|
| **Foundation** — measurement, storage, versioning, benchmarks | No — fully deterministic and offline-testable | Built in Phase 12 |
| **Learning loops** — promotion, workflow optimization, learned selection, PR-outcome learning | Yes — needs volume to be valid | Scaffolded behind a seam; switched on when data exists |

The Foundation MUST be implementable and testable with the existing
deterministic fakes (`EchoModel`, `FakeGitHubProvider`, in-memory stores), with
**zero** real models or services required — consistent with the rest of the
repo (ADR pattern: provider abstraction + fake + "going live is just config").

The Learning loops MUST be built behind the same provider/strategy seam so they
can be enabled by configuration once data exists, **without** changing the
agents or the workflow graph.

---

## Component contracts

### 1. Evaluation Engine

After every run, the engine MUST produce a single `Evaluation` record capturing
both **outcome** and **cost**:

```json
{
  "run_id": "…", "task": "Add JWT authentication",
  "tests_passed": true, "review_score": 9, "retries": 1,
  "execution_time_s": 42, "tokens": 5120, "pr_accepted": null,
  "prompt_versions": {"planner": "v3", "coder": "v2", "...": "..."},
  "model_routing": {"planner": "qwen3:8b", "coder": "deepseek-coder"},
  "score": 0.86, "success": true
}
```

- The engine MUST derive `score` from a documented, versioned rubric so two runs
  are comparable. The rubric version MUST be recorded on the record.
- It MUST score automatically where possible (tests pass, retries used,
  wall-clock) and MAY use an LLM-judge for plan/review quality (recorded as a
  distinct, attributable sub-score).
- It MUST NOT require real models: with `EchoModel`, scoring runs end-to-end and
  produces deterministic records.
- `pr_accepted` MAY be null at write time and backfilled later (see §10).

### 2. Performance Database

Per-agent aggregates MUST be queryable for the analytics dashboard:

| Agent | Success rate | Avg time | Avg retries | Accepted PR % | Avg score |
|-------|-------------|----------|-------------|---------------|-----------|

- Aggregates MUST be **derived** from `Evaluations`/event data (a view or
  recomputable rollup), never a separate source of truth that can drift.
- Stats MUST be sliceable by agent, prompt version, and model.
- Reads MUST work against the in-memory store offline and Postgres in
  production, behind one interface (mirrors `observability/store.py`).

### 3. Prompt Versioning

The flat `PROMPTS` dict in `packages/prompts/registry.py` MUST become
**versioned and addressable** without breaking existing callers.

- `system_prompt(role)` MUST keep returning the **active** version's text
  (backward compatible).
- Each role MUST support multiple named versions (`v1`, `v2`, …) with exactly
  one marked active.
- Every run MUST record the prompt version used per agent (feeds §1).
- A prompt change MUST create a new version, never mutate an existing one
  (append-only history — the audit trail of what produced which results).

### 4. Reflection Memory + Failure Knowledge Base

Today `ReflectionAgent` does Error → Fix → **Forget**. It MUST become
Error → Fix → **Store → Reuse**.

- On reflection, a `Failure` record MUST be stored: `{error_signature, cause,
  fix, outcome}`. `error_signature` MUST be a normalized key (e.g. exception
  type + salient message tokens) so recurring errors collide.
- Before proposing a fix, Reflection MUST consult the KB by signature and, on a
  hit with a successful past outcome, MUST surface that fix (a retrieval, not a
  guess) — "fix instantly."
- Storing/retrieving MUST be deterministic and offline (in-memory store + the
  same Postgres-backed seam).
- A surfaced past fix that fails MUST be recorded as a new outcome so the KB
  self-corrects (no fix is trusted permanently).

### 5. Benchmark Suite

A versioned suite of scenarios (`add feature`, `fix bug`, `refactor module`,
`write tests`, `create API`) with expected results.

- Each scenario MUST declare an expected outcome / rubric (extends
  `evaluation-spec.md`'s eval set).
- A harness MUST run the suite through the **real workflow** and emit per-agent
  + aggregate metrics (success rate, latency, quality, retries).
- The suite MUST run deterministically offline for CI (echo provider) and
  against real models for true benchmarking — same harness, config switch.
- Results MUST be stored per ForgeAI version so versions are comparable (§2).

### 6. Multi-Agent Debate *(research; testable offline)*

For configured roles (initially Planner), the workflow MAY run **N independent
attempts** and select a winner.

- It MUST run attempts independently (no shared context between them).
- A judge (Review-as-judge) MUST select or synthesize the winning output using
  documented criteria; the decision MUST be recorded (which lost and why).
- It MUST be **off by default** and enabled per-role by config — the default
  graph is unchanged.
- It MUST be deterministic under `EchoModel` (e.g. seeded by attempt index) so
  tests are stable.

### 7. Dynamic Agent Selection *(scaffold now; learn later)*

The workflow MUST support **task-type-conditioned** routing (backend / frontend
/ database / …) selecting specialist variants or skipping nodes.

- Phase 12 ships a **rule-based** classifier (deterministic, offline) as the
  default strategy.
- The selection strategy MUST sit behind an interface so a **learned** strategy
  (from §2/§10 data) can replace it by config, with no agent/graph change.
- Every selection MUST be recorded with its rationale (auditable; feeds learning).

### 8. Learning Loops *(deferred — scaffold only)*

These MUST exist as interfaces with a default **no-op / rule-based** strategy in
Phase 12, and MUST NOT auto-act on production until data thresholds are met:

- **A/B promotion** — run arms now and record results; *promotion* of a winning
  prompt/agent MUST require a configurable minimum sample size and significance,
  and MUST be gated behind explicit approval (consistent with the platform's
  approval-gated writes). It MUST NOT auto-promote silently.
- **Workflow optimization** — the system MAY recommend skipping a node (e.g.
  "research unnecessary for task type X") from history, but MUST surface it as a
  recommendation for approval, not a silent graph mutation.
- **PR-outcome learning** — PR accept/reject (§10) MUST feed `Evaluation`
  records as a labeled signal; acting on it is deferred to a learned strategy.

### 9. Agent Marketplace / Plugin System *(platform; independent)*

Third-party agents (Security, Documentation, DevOps, …) MAY be registered and
discovered dynamically.

- A registered agent MUST satisfy the existing **agent contract**
  ([`agent-spec.md`](agent-spec.md)) — one role, reads/writes `ProjectState`,
  never calls another agent directly.
- Discovery MUST be explicit and permissioned (no implicit code execution from
  registration); registration is an approval-gated action.
- This component is **independent** of the learning loops and MAY ship on its
  own timeline.

### 10. Learning from PR Outcomes *(deferred — backfill seam now)*

- The `Evaluation` record MUST carry a nullable `pr_accepted` that the GitHub
  workflow backfills when a PR is merged/closed (accept = positive, reject =
  negative).
- The webhook/poll seam MUST exist in Phase 12 (the field + the writer);
  *acting* on the signal is part of the deferred learned strategy.

---

## New persistence (logical schema)

Backed by the existing in-memory-store → Postgres pattern (same interface).

| Table | Key columns |
|-------|-------------|
| `evaluations` | id, run_id, task, score, success, tests_passed, review_score, retries, execution_time_s, tokens, pr_accepted (nullable), rubric_version, created_at |
| `prompt_versions` | id, agent_role, version, body, is_active, created_at |
| `benchmarks` | id, scenario, expected_result, suite_version |
| `benchmark_results` | id, benchmark_id, forge_version, success, latency_s, score, retries, created_at |
| `failures` | id, error_signature, cause, fix, outcome, created_at |
| `agent_stats` | (derived) agent_role, success_rate, avg_score, avg_time_s, avg_retries, accepted_pr_pct |

`agent_stats` MUST be derived/recomputable, not an independent writable table.

## Dashboard

A new **Agent Analytics** tab MUST show per-agent success/score with deltas
(`Planner 97% ↑+2%`, `Coder 88% ↓-1%`) and a prompt-version comparison
(`v3 92%` vs `v4 95%` → *Promote v4*), where *Promote* is an approval-gated
action (§8), never automatic.

## A change MUST NOT

- Mutate an existing prompt version in place (§3) — versions are append-only.
- Auto-promote a prompt/agent or mutate the workflow graph from data without
  meeting the sample threshold **and** explicit approval (§8).
- Require real models or services for the Foundation half to be tested (§Guiding
  constraint).
- Let `agent_stats` become a writable source of truth that can drift from
  `evaluations` (§2).
- Allow a registered marketplace agent to bypass the agent contract or run code
  on registration (§9).

## Acceptance criteria

**Foundation (Phase 12 ships these):**

- [x] Every run produces a versioned, rubric-scored `Evaluation` record offline.
- [x] Per-agent stats are derivable and sliceable by agent / prompt version / model.
- [x] Prompts are versioned and addressable; `system_prompt(role)` is unchanged
      for callers; each run records the versions it used.
- [x] Reflection stores failures and reuses a matching past fix on recurrence.
- [ ] A versioned benchmark suite + harness runs offline (echo) and on real models.
- [ ] Multi-agent debate runs behind a config flag, off by default, deterministic
      under `EchoModel`.
- [ ] Rule-based dynamic agent selection works and is recorded with rationale.
- [ ] The Agent Analytics tab renders per-agent deltas and prompt comparison.
- [ ] Offline suite green; ruff + black clean; docs updated; an ADR records the
      measurement-substrate design.

**Learning loops (scaffolded in Phase 12, enabled post-data):**

- [ ] A/B promotion, workflow optimization, and PR-outcome learning exist as
      interfaces with safe defaults and approval gates; none auto-acts on
      production without meeting a documented data threshold.
- [ ] `pr_accepted` backfill seam exists end-to-end (field + writer).
