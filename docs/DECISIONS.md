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
