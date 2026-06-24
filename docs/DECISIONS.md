# Architecture Decision Records (ADRs)

A running log of significant decisions. Newest at the top. Each entry:
what we decided, why, and what we considered.

---

## ADR-0001 — Build as a multi-agent team, not a single LLM call

**Phase:** 0 · **Status:** Accepted

**Decision:** ForgeAI orchestrates specialist agents (Planner, Researcher,
Coder, Tester, Reviewer, DevOps) under an Engineering Manager, instead of a
single do-everything LLM call.

**Why:** Separation of concerns, checkpoints (Tester/Reviewer can reject),
traceability, and tighter per-agent prompts.

**Considered:** Single-model chatbot (rejected — no division of labor or
verification step).

---

## ADR-0002 — The Engineering Manager never writes code

**Phase:** 0 · **Status:** Accepted

**Decision:** The Manager only interprets, decomposes, delegates, and sequences.
All code is produced by specialist agents.

**Why:** Keeps orchestration clean and each specialist focused; mirrors a real
tech lead.

---

## ADR-0003 — All LLM access goes through a Model Router

**Phase:** 0 · **Status:** Accepted

**Decision:** Agents call a LiteLLM-based Model Router, never a provider SDK
directly. Provider/model is configurable at runtime (Ollama, Gemini, Groq,
OpenRouter, ...).

**Why:** Provider independence; add/swap providers with near-zero code change.

---

## ADR-0004 — Three purpose-specific data stores

**Phase:** 0 · **Status:** Accepted

**Decision:** PostgreSQL (system of record), Redis (jobs/queue/locks/ephemeral
state), Qdrant (vector embeddings for memory & RAG).

**Why:** Each store is used for what it's best at rather than overloading one.

---

## ADR-0005 — Ruthless MVP scope for v1.0

**Phase:** 0 · **Status:** Accepted

**Decision:** v1.0 = Login, Create Project, Chat, Planner+Coder+Review agents,
local file editing, Docker execution, project memory. Slack/Jira/AWS/browser
automation are explicitly deferred.

**Why:** Prove the core team-of-agents loop before expanding surface area.

---

## ADR-0006 — Monorepo with apps/ + packages/

**Phase:** 1 · **Status:** Accepted

**Decision:** Single repo split into `apps/` (web, api) and `packages/`
(agents, core, prompts, tools, memory, rag, models), plus `infrastructure/`,
`docs/`, `scripts/`.

**Why:** ForgeAI will grow to 10+ agents, 30+ APIs, 100+ prompts, and multiple
LLMs. A flat frontend/backend split would not scale; this keeps each concern
isolated while sharing one toolchain and compose stack.

---

## ADR-0007 — uv for Python, pinned to 3.12

**Phase:** 1 · **Status:** Accepted

**Decision:** Use `uv` (not Poetry/pip) to manage the backend, with Python
pinned to 3.12 in the API Dockerfile and `pyproject.toml`.

**Why:** `uv` is already installed, is far faster, and produces a committed
`uv.lock` for reproducibility. Python 3.12 is the project target (the dev host
runs 3.14, so Docker is the source of truth). Poetry was considered but is not
installed and offers no advantage here.

---

## ADR-0008 — Hand-scaffold the app starters

**Phase:** 1 · **Status:** Accepted

**Decision:** Write minimal Next.js 15 and FastAPI starters by hand rather than
running `create-next-app` / generators.

**Why:** Deterministic, fully version-controlled layout with no interactive
prompts; dependencies resolve at install/build time. Verified working: backend
tests + lint pass, frontend type-checks and builds.

---

## ADR-0009 — Agent system lives in `packages/`, imported by the API

**Phase:** 2 · **Status:** Accepted

**Decision:** The AI engine (`core`, `models`, `prompts`, `tools`, `agents`)
lives in repo-root `packages/`, not inside `apps/api`. The API depends on it
via `PYTHONPATH`/pytest `pythonpath`.

**Why:** Keeps orchestration reusable and independently testable, and matches
the Phase 1 monorepo layout. The API is one consumer of the engine, not its
owner.

---

## ADR-0010 — LangGraph over one shared `ProjectState`

**Phase:** 2 · **Status:** Accepted

**Decision:** Orchestrate agents with an explicit LangGraph `StateGraph` over a
single `ProjectState`, with a conditional edge after review that drives a
bounded `reflection → coder` retry loop. No agent calls another directly.

**Why:** Makes execution order, branching, and retries explicit and
inspectable; enforces loose coupling (agents only touch shared state); supports
self-correction. Ad-hoc async loops were rejected as unobservable.

---

## ADR-0011 — EchoProvider for offline, deterministic testing

**Phase:** 2 · **Status:** Accepted

**Decision:** Ship an `EchoProvider` implementing the `LLMProvider` interface
that returns canned responses with no network calls. The full workflow test
suite runs against it.

**Why:** The whole agent graph must be testable in CI without a live Ollama
server or the ~20 GB of pulled models. Provider independence (ADR-0003) makes
this a drop-in.

---

## Note — roadmap reordering

The original Phase 0 roadmap placed Authentication at Phase 2 and split agent
work across Phases 4/5/7. We front-loaded the **AI engine** as Phase 2 because
it is the heart of the product. The remaining phases shift accordingly; the
phase *table* in the roadmap reflects the new order.
