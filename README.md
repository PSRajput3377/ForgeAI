# ForgeAI

**An autonomous AI engineering platform that behaves like a team of software engineers — and a research-grade system that measures and improves itself over time.**

Most AI coding tools are one model answering one prompt:

```
User → LLM → Answer
```

ForgeAI is a coordinated team that plans, codes, tests, reviews, and ships — then
*learns from every run*:

```
User
  ↓
Engineering Manager   (delegates — never writes code)
  ↓
Planner → Researcher → Coder → Tester → Reviewer → DevOps
  ↓
Pull Request
  ↓
Evaluation → Performance DB → Analytics → (gated) Self-improvement
```

You describe a task ("Add JWT authentication"). A Manager agent breaks it down
and delegates to specialist agents. You watch them plan, research, code, test,
and review — in real time — inside a sandboxed project. Every run is then
**scored, stored, and compared**, so the system gets measurably better across
runs without you changing code.

---

## Table of contents

- [What it is](#what-it-is)
- [Why it's built this way](#why-its-built-this-way)
- [How it works, end to end](#how-it-works-end-to-end)
- [The self-improvement system (Phase 12)](#the-self-improvement-system-phase-12)
- [Projects & first-run experience (Phase 13)](#projects--first-run-experience-phase-13)
- [Applications — who uses it and for what](#applications--who-uses-it-and-for-what)
- [Getting started](#getting-started)
- [Using it end to end](#using-it-end-to-end)
- [Development](#development)
- [Project layout](#project-layout)
- [Status](#status)
- [Documentation](#documentation)
- [Tech stack](#tech-stack)

---

## What it is

ForgeAI is a **multi-agent autonomous software engineering platform**. Instead of
a single chatbot, it runs a team of specialist agents, each with one job,
coordinated by an explicit workflow graph. The team takes a natural-language
request and carries it all the way to a reviewed, test-passing pull request —
while you watch the whole thing happen live.

On top of that pipeline sits a **self-improving layer**: every run is measured,
the results are stored durably, and the system can compare prompt versions,
benchmark itself across releases, learn from failures, and recommend
improvements — all behind human approval gates.

**The whole backend runs and is fully tested offline** — no Docker, no models, no
external services required. Every external dependency (LLM, GitHub, datastores)
has a deterministic in-memory fake, so the entire system is reproducible in CI.
**330 tests pass** in seconds.

---

## Why it's built this way

A few deliberate engineering choices shape the whole project:

- **A team, not a model.** Real software is built by specialists who plan,
  implement, test, and review separately. Splitting the work across agents with
  single responsibilities makes each step inspectable, testable, and
  replaceable — and makes failures debuggable instead of mysterious.

- **The graph sequences agents — agents never call each other.** All
  coordination is expressed declaratively by a LangGraph workflow over one
  shared `ProjectState`. Agents stay loosely coupled; the execution order,
  branching, and retry loop are explicit and visible (ADR-0001).

- **Provider abstraction + deterministic fake + "going live is just config."**
  LLMs, GitHub, and datastores are all behind interfaces with in-memory fakes.
  The same code runs offline (echo provider, fake GitHub) and in production
  (Ollama, real GitHub) — you flip a config value, not a code path (ADR-0003).
  This is why the whole system is testable without a single external service.

- **Human-gated writes.** Anything that affects the outside world — opening a
  PR, promoting a prompt, changing the workflow — is *proposed*, then requires
  explicit approval. The system never silently mutates production.

- **Measure before you optimize.** You can't improve what you don't measure, so
  the self-improvement work starts with an evaluation substrate and only then
  adds learning loops on top — and those loops stay advisory until there's
  enough real data to act on.

---

## How it works, end to end

A single request flows through an explicit workflow graph. Each node is one
agent doing one job, reading from and writing to a shared `ProjectState`:

```
START → manager(intake) → planner → research → memory → coder
      → execute → tests → review → [approved?]
                                      │ no  → reflection → coder   (retry loop)
                                      │ yes → git → manager(final) → END
```

| Agent | Responsibility |
|-------|----------------|
| **Manager** | Interprets the request, classifies the task type, delegates, writes the final response. Never writes code. |
| **Planner** | Breaks the request into a numbered list of executable tasks. (Can *debate* — see Phase 12.) |
| **Researcher** | Gathers only the context relevant to the task from docs/code. |
| **Memory** | Surfaces short-term context and long-term knowledge (RAG over Qdrant). |
| **Coder** | Writes the code, working strictly from the given context. |
| **Execution** | Runs install/build/test commands inside a Docker sandbox. |
| **Testing** | Runs tests and reports pass/fail with evidence. |
| **Review** | Approves or requests changes on real criteria. |
| **Reflection** | On failure, diagnoses the root cause and proposes a fix, then retries — and *remembers* the fix (Phase 12). |
| **Git** | Stages changes, writes a conventional-commit message, and *proposes* a gated PR. |

Around the graph:

- **Observability** — every node emits lifecycle events on an event bus that
  fans out to a timeline store, a metrics collector, and a live WebSocket. The
  web Workspace renders the run as it happens.
- **Sandboxed execution** — generated code runs in an isolated Docker container
  with security profiles; destructive operations are withheld.
- **Memory + RAG** — past tasks, decisions, and project context are embedded in
  Qdrant and retrieved for new requests.
- **GitHub** — commits are authored on a local clone via `git`, and PRs are
  opened only after explicit human approval.

---

## The self-improvement system (Phase 12)

This is what turns ForgeAI from "a multi-agent tool" into "a system that gets
better over time." It's built as a **foundation** (measurement, deterministic
and shippable now) plus **learning loops** (scaffolded behind safe defaults,
switched on once real usage data exists). Full contract:
[`specs/self-improvement-spec.md`](specs/self-improvement-spec.md).

| Component | What it does |
|-----------|--------------|
| **Evaluation Engine** (`packages/evaluation`) | After every run, derives one scored `Evaluation` (outcome + cost + which prompt versions/models were used) via a **versioned rubric**, so two runs are comparable. |
| **Performance Database** (`evaluations` table) | Durable, queryable run scores. Per-agent / per-prompt-version stats are *derived* from the records, never stored separately — so they can't drift. |
| **Prompt Versioning** (`packages/prompts`) | Prompts are versioned and append-only; one active version per agent. Every run records which version it used. `system_prompt(role)` is unchanged for callers. |
| **Reflection Memory + Failure KB** (`packages/failures`) | Error → Fix → **Store → Reuse**. Failures are keyed by a normalized signature so recurring errors collide on one entry; a known-good fix is reused instantly instead of re-diagnosed. A fix that later fails is demoted — the KB self-corrects. |
| **Benchmark Suite** (`packages/benchmarks`) | A versioned set of scenarios (add feature, fix bug, refactor, write tests, create API) run through the real workflow and scored, tagged per ForgeAI version so releases are comparable. |
| **Multi-Agent Debate** (`packages/agents/debate.py`) | Optionally runs N independent Planner attempts from different angles, judged to a winner. Off by default, deterministic, fully recorded. |
| **Dynamic Agent Selection** (`packages/selection`) | Classifies a request by task type (backend / frontend / database / general) behind a strategy interface, recording the rationale. Rule-based now; a learned strategy can replace it by config. |
| **Agent Analytics** (`/analytics`) | A dashboard tab: per-agent success/score, prompt-version comparison (`v3` vs `v4` → promote hint), and the benchmark trend. |
| **Learning loops** (`packages/learning`) | A/B prompt promotion, workflow optimization, and PR-outcome learning — all **recommend-only with approval gates**; none auto-acts on thin data. |
| **Agent Marketplace** (`packages/marketplace`) | Register third-party agents (Security, Docs, DevOps…) as descriptors and discover the approved ones. No code runs on registration; a contract check enforces the agent spec. |

**The full loop, proven live:** type a task → the agent team executes → the run
is scored → persisted to PostgreSQL → surfaced on the analytics dashboard.

See [a complete offline walkthrough](#walkthrough-see-the-whole-system-in-one-command)
of every component below.

---

## Projects & first-run experience (Phase 13)

Phase 12 made ForgeAI a research-grade *engine*. Phase 13 makes it a *product* —
it gives the engine a front door. The root cause of "to which project?", "no way
to start from nothing", and "no sub-minute wow" was one missing primitive: a
**Project that owns a real workspace directory**. Phase 13 adds it.
Full contract: [`specs/projects-spec.md`](specs/projects-spec.md).

| Component | What it does |
|-----------|--------------|
| **First-class Projects** (`app/projects.py`, `/projects`) | A `Project` owns a directory on disk (`<WORKSPACES_ROOT>/<id>`). CRUD endpoints manage it within the existing Org → Workspace → Project tenancy + RBAC. The path is derived from the id (never client-supplied) and confined to the project's own folder. |
| **Run binds to a project** | `/agents/run` resolves `project_id` → that project's path, runs the team against it, and **writes generated files there** — so a run produces a real, inspectable project on disk (404 on an unknown id). |
| **Bootstrap from nothing** (`packages/starters`) | Create a project from a versioned **starter** — `empty`, or a `fastapi-saas` starter (JWT auth, PostgreSQL, Docker, tests). Deterministic and offline: scaffolds instantly, then hands the project to the agent team. Refuses to overwrite a non-empty project. |
| **Onboarding flow** (`/projects` page) | Signed-in users land on a **project chooser** — *Create New* (name + starter picker) or *Open Existing* — not a bare workspace. Choosing a project binds it and opens the workspace. |
| **The first-minute "wow"** | From a fresh account: pick a starter → it scaffolds → land in the workspace with suggested one-click first tasks → watch the team build it live. Works **offline with `MODEL_PROVIDER=echo`**, so it's demoable on any hardware. |

The Project model carries a nullable `repo`, so a future **git-backed mode**
slots in behind the same interface with no agent/workflow change.

---

## Applications — who uses it and for what

ForgeAI is useful both as a **product** (autonomous engineering) and as a
**research platform** (a measurable, self-improving multi-agent system).

**As an autonomous engineering team:**

- **Developers** — "Add authentication to my app." Offload well-scoped features,
  bug fixes, refactors, and test-writing to a team that plans, implements, tests,
  reviews, and opens a PR you approve.
- **Startups** — "We need CRUD APIs." Ship internal tooling and boilerplate-heavy
  work fast, with a human approving every PR.
- **Students & educators** — a transparent, inspectable reference for how
  multi-agent systems, LangGraph orchestration, RAG, sandboxed execution, and
  agent evaluation actually fit together.
- **Companies** — "Build an internal dashboard." Run it on local models (no data
  leaves your infrastructure) with workspace isolation, RBAC, and approval-gated
  GitHub writes.

**As a research / platform substrate:**

- **Agent evaluation & benchmarking** — a versioned rubric, a benchmark suite,
  and a performance database make "did this change actually help?" a measurable
  question rather than a vibe.
- **Prompt engineering at scale** — versioned prompts + per-version stats turn
  prompt iteration into A/B experiments with an approval-gated promotion path.
- **Self-improving / self-correcting agents** — the failure knowledge base,
  multi-agent debate, and learning loops are concrete, tested implementations of
  research ideas (reflection, debate, learning from outcomes).
- **Plugin ecosystem** — the marketplace lets teams publish and discover
  specialist agents behind a permissioned, contract-checked interface.

**Deployment-shape advantages:**

- **Runs fully local** — Ollama models, no API keys, no data leaving your
  machine. Swap to a hosted provider by config when you want to.
- **Reproducible** — deterministic fakes mean the whole system runs and tests
  offline; great for CI and for demos on modest hardware (`MODEL_PROVIDER=echo`).
- **Safe by construction** — sandboxed execution, path validation, withheld
  destructive ops, JWT auth, and human-gated external writes.

---

## Getting started

### Prerequisites

- **Docker** + **Docker Compose** (for the local service stack)
- **Node.js** 20+ (for the frontend)
- **[uv](https://github.com/astral-sh/uv)** (for the Python backend)
- ~20 GB free disk (for the local Ollama models — only if you run real models)

### 1. Clone and configure

```bash
git clone https://github.com/PSRajput3377/ForgeAI.git
cd ForgeAI
make env          # creates .env from .env.example (safe local defaults)
```

The defaults work out of the box — no API keys needed. Change `JWT_SECRET`
before any non-local use, and add `GITHUB_TOKEN` only for live GitHub features.

### 2. Start the stack

```bash
make up            # postgres, redis, qdrant, ollama, forge-api
make pull-models   # one-time ~20 GB model download (qwen3, deepseek-coder, …)
```

Check it's healthy:

```bash
make ps
curl http://localhost:8000/health        # {"status":"ok",...}
```

| Service     | URL                                |
|-------------|------------------------------------|
| API         | http://localhost:8000              |
| API docs    | http://localhost:8000/docs         |
| Web app     | http://localhost:3000              |
| Analytics   | http://localhost:3000/analytics    |
| Qdrant      | http://localhost:6333/dashboard    |

### 3. Run the frontend

```bash
make web-install
make web-dev       # http://localhost:3000
```

> **Running on modest hardware?** Real local models need real RAM — an 8B model
> wants ~6–8 GB, and a full run makes several sequential LLM calls. If runs time
> out, set `MODEL_PROVIDER=echo` in `.env` and `make up` again: the entire
> pipeline (HTTP → workflow → scoring → database → analytics) then runs
> **instantly and deterministically**, with no models required. This is the
> same provider the test suite uses (ADR-0003).

---

## Using it end to end

### Via the UI (the intended experience)

1. Open **http://localhost:3000** → **Sign in** to create an account.
2. You land on the **project chooser**: **Create New** (name it, pick a starter —
   `empty` or the `fastapi-saas` starter) or **Open Existing**.
3. Creating a project scaffolds it and drops you into the **Workspace**, bound to
   that project. Use a suggested one-click task, or type your own — e.g.
   *"Add JWT authentication"* — and hit **Run** (or ⌘/Ctrl+Enter).
4. Watch the **agent timeline, status, and metrics update live** over the
   WebSocket as the team plans → researches → codes → tests → reviews. Generated
   files are written into the project on disk.
5. The run's verdict + generated code appear inline; any proposed PR shows up in
   the **Approval Center** for one-click review → approve.
6. Open **Analytics** (top-right link) to see the run land: per-agent stats,
   prompt-version comparison, and the benchmark trend.

> On modest hardware, set `MODEL_PROVIDER=echo` so the whole flow runs instantly
> and deterministically — the first-minute path needs no models.

### Via the API (everything the UI does is an endpoint — see `/docs`)

```bash
# 1. Register + log in to get a token
curl -s -X POST localhost:8000/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"email":"you@example.com","name":"You","password":"changeme123"}'

TOKEN=$(curl -s -X POST localhost:8000/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"you@example.com","password":"changeme123"}' \
  | python3 -c 'import sys,json;print(json.load(sys.stdin)["access_token"])')

# 2. Run the multi-agent workflow on a task
curl -s -X POST localhost:8000/agents/run \
  -H 'Content-Type: application/json' \
  -d '{"user_request":"Add JWT authentication","project_id":"demo-1"}' | python3 -m json.tool

# 3. Watch the run's event timeline
curl -s localhost:8000/observability/timeline/demo-1 | python3 -m json.tool

# 4. See it land in analytics (scored + persisted)
curl -s localhost:8000/analytics/overview          | python3 -m json.tool
curl -s localhost:8000/analytics/prompts/planner   | python3 -m json.tool
curl -s localhost:8000/analytics/benchmarks/trend  | python3 -m json.tool
```

### Walkthrough: see the whole system in one command

A self-contained, offline, deterministic tour of **every Phase 12 component** —
selection, debate, evaluation, failure-memory reuse, prompt versioning + the
promotion gate, derived stats, the workflow-optimization hint, the PR-outcome
signal, and the marketplace:

```bash
cd apps/api
PYTHONPATH="$PWD:$PWD/../../packages" uv run python ../../scripts/demo_phase12.py
```

### GitHub integration

GitHub is behind a **provider abstraction** with a deterministic
`FakeGitHubProvider` (for offline tests/CI) and a production `RestGitHubProvider`.
Commits are authored on a **local clone via git** (not the REST API), composing
with the sandbox, testing, reflection, and review. **Going live is just config:**

```bash
# add a fine-grained PAT (repo scope) to .env, then:
curl localhost:8000/github/status                    # {"mode":"live"}
curl localhost:8000/github/repo/octocat/Hello-World  # real repo data
```

All PR writes are **human-gated** (propose → approve → execute). Validate live
functionality against **sandbox repositories** via
[`scripts/verify-github.sh`](scripts/verify-github.sh) — never production repos.

---

## Development

The backend runs and is fully tested **offline** — no Docker, no models, no
external services (every external dependency has a deterministic fake):

```bash
cd apps/api
uv sync
uv run pytest -q                                # 330 tests, ~10s
uv run ruff check . && uv run black --check .   # lint + format
```

The frontend builds with `cd apps/web && npm install && npm run build`.

---

## Project layout

```
ForgeAI/
├── apps/
│   ├── api/            FastAPI backend — routes, runtimes, durable stores
│   └── web/            Next.js frontend — Workspace + Analytics
├── packages/           The engine (one domain per package):
│   ├── core/           ProjectState, roles, messages
│   ├── models/         LLM provider interface + Ollama + echo fake + router
│   ├── prompts/        Versioned, append-only agent prompts
│   ├── agents/         The 10 specialists + the LangGraph workflow + debate
│   ├── tools/          File / shell / search — the agents' hands
│   ├── execution/      Docker sandbox, security profiles, retry loop
│   ├── memory/ rag/    Project memory + RAG over Qdrant
│   ├── github/         Provider abstraction, local-clone commits, gated PRs
│   ├── observability/  Event bus, store, metrics, tracing, audit
│   ├── integrations/   External connectors + hub
│   ├── evaluation/     Scored run records + versioned rubric (Phase 12)
│   ├── failures/       Failure knowledge base (Phase 12)
│   ├── benchmarks/     Versioned scenario suite + harness (Phase 12)
│   ├── selection/      Dynamic task-type routing (Phase 12)
│   ├── learning/       A/B promotion, workflow-opt, PR-outcome (Phase 12)
│   ├── marketplace/    Register + discover third-party agents (Phase 12)
│   └── starters/       Versioned project scaffolds for bootstrap (Phase 13)
├── specs/              What each component MUST do (checkable contracts)
├── docs/               How it works: architecture, ADRs, diagrams, per-domain
├── infrastructure/     Dockerfiles + service configs
└── scripts/            demo_phase12.py, verify-github.sh, …
```

---

## Status

The project was built in **13 phases**, all complete:

| Phase | Name | Status |
|-------|------|--------|
| 0 | Product Design | ✅ |
| 1 | Project Setup | ✅ |
| 2 | AI Engine & Agent Architecture | ✅ |
| 2.5 | System Design & Documentation | ✅ |
| 3 | Tool System & Action Engine | ✅ |
| 4 | Memory, RAG & Knowledge Engine | ✅ |
| 5 | Autonomous Execution & Docker Sandbox | ✅ |
| 6 | Developer Workspace & Observability | ✅ |
| 7 | Auth, Multi-User Workspaces & Teams | ✅ |
| 8 | GitHub Integration & Autonomous Workflow | ✅ |
| 9 | Enterprise Integrations & Ecosystem | ✅ |
| 10 | Production: Scale, Security & Reliability | ✅ |
| 11 | Dashboard & PR Approval Center | ✅ |
| 12 | Self-Improving Agent System | ✅ |
| 13 | Projects & First-Run Experience | ✅ |

> The data-dependent halves of the Phase 12 learning loops (auto-promotion,
> workflow mutation, PR-outcome-driven learning) are **scaffolded behind safe
> defaults and approval gates** — they switch from *recommend* to *act* via
> config once real usage data exists, by design.

---

## Documentation

ForgeAI is documented so you can understand it **without reading the source**.

- **[`docs/`](docs/README.md)** — architecture, agents, workflows, shared state,
  tools, database, API, prompts, security, testing, deployment, Mermaid
  diagrams, and a [26-entry ADR log](docs/adr/README.md).
- **[`specs/`](specs/README.md)** — the checkable contracts each component must
  satisfy, including [`self-improvement-spec.md`](specs/self-improvement-spec.md)
  (Phase 12).
- **[`docs/00-product-design/`](docs/00-product-design/)** — the product vision
  and the [Phase 12](docs/00-product-design/phase-12-plan.md) / [Phase 13](docs/00-product-design/phase-13-plan.md) plans.

The "why" behind each technology choice is in [`docs/decisions.md`](docs/decisions.md).

---

## Tech stack

**Frontend:** Next.js · React · TypeScript · Tailwind · shadcn/ui
**Backend:** FastAPI · LangGraph · SQLAlchemy (async) · WebSockets
**Data:** PostgreSQL · Redis · Qdrant
**AI:** Ollama (local models) · model-router abstraction · LangGraph · Langfuse (tracing)
**Infra:** Docker · Docker Compose

See [`docs/00-product-design/05-tech-stack.md`](docs/00-product-design/05-tech-stack.md)
for the rationale.
