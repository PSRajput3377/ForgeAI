# Design Decisions — the "why"

This is the narrative companion to the formal [`adr/`](adr/) records. When an
interviewer (or a future contributor) asks *"why did you choose X?"*, the
answer is here, with a link to the full ADR.

## Why a multi-agent team? (not one big prompt)
One LLM call has no division of labor and no verification step. A team gives
separation of concerns, checkpoints (Review/Testing can reject), and
traceability. → [ADR-0001](adr/ADR-0001.md), [ADR-0002](adr/ADR-0002.md)

## Why LangGraph?
We need orchestration where order, branching, and **retries** are explicit and
inspectable — not buried in ad-hoc async code. LangGraph models the workflow as
a state graph over one shared `ProjectState`, which also enforces loose
coupling (agents touch state, never each other) and makes the reflection retry
loop a first-class edge. → [ADR-0010](adr/ADR-0010.md)

## Why Ollama (and a Model Router)?
The MVP runs **fully local** — no API keys, no per-token cost, full privacy.
Agents never call a provider SDK directly; they go through a Model Router, so
swapping in OpenAI/Claude/Gemini later is a one-class change. → [ADR-0003](adr/ADR-0003.md)

## Why FastAPI?
Async-first (critical for many concurrent agent/LLM calls and WebSocket
streaming), first-class Pydantic validation (our message contracts are Pydantic
models), and automatic OpenAPI docs.

## Why PostgreSQL?
A battle-tested relational system of record for users, projects, sessions,
tasks, and messages — strong consistency and rich querying. → [ADR-0004](adr/ADR-0004.md)

## Why Redis?
Fast, ephemeral coordination: running-job state, the agent queue, locks, and
temporary state that doesn't belong in the durable store. → [ADR-0004](adr/ADR-0004.md)

## Why Qdrant?
Memory and RAG need semantic similarity search over embeddings — a purpose-built
vector database rather than bolting vectors onto Postgres. → [ADR-0004](adr/ADR-0004.md)

## Why Docker (sandbox)?
Agent-generated code must run somewhere **isolated from the host**. Containers
give a disposable, resource-limited, network-restricted sandbox. → see
[`security.md`](security.md)

## Why a monorepo?
10+ agents, 30+ APIs, 100+ prompts, multiple LLMs — a flat split won't scale.
`apps/` + `packages/` isolates concerns under one toolchain. → [ADR-0006](adr/ADR-0006.md)

## Why a shared ProjectState?
Passing dozens of variables between agents is brittle. One typed state object
that every node reads and writes keeps the data flow explicit and auditable, and
makes each agent independently testable. → [ADR-0010](adr/ADR-0010.md),
[`state.md`](state.md)

## Why uv + Python 3.12?
Fast, reproducible installs with a committed lockfile; Docker pins the runtime
so it's independent of the dev host. → [ADR-0007](adr/ADR-0007.md)

---

For the complete, immutable record of every decision see the
[ADR index](adr/README.md).
