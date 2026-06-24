# 05 — Tech Stack (Final / Locked)

This stack is locked for the MVP. Changes go through an ADR in
[`../decisions.md`](../decisions.md).

## Frontend
- **Next.js** — app framework
- **React** — UI library
- **TypeScript** — type safety
- **Tailwind CSS** — styling
- **shadcn/ui** — component primitives

## Backend
- **FastAPI** — async Python API framework
- **Python** — language
- **LangGraph** — multi-agent orchestration
- **SQLAlchemy** — ORM
- **WebSockets** — live agent/log streaming

## Database
- **PostgreSQL** — system of record

## Cache
- **Redis** — jobs, queue, temporary state, locks

## Vector Database
- **Qdrant** — embeddings for files, docs, conversation, memory

## Infrastructure
- **Docker** — containerization
- **Docker Compose** — local multi-service orchestration

## AI
- **Ollama** — local model serving
- **LiteLLM** — model router / provider abstraction
- **LangGraph** — agent workflow engine

## Observability
- **Langfuse** — LLM tracing & observability

---

## Proposed folder structure (implemented in Phase 1)

> Documented here for reference. The directories are created in **Phase 1**,
> not Phase 0. Every folder has **one responsibility**.

```
forge-ai/
├── frontend/        Next.js app
├── backend/         FastAPI app + API layer + Agent Manager
├── agents/
│     ├── manager/
│     ├── planner/
│     ├── researcher/
│     ├── coder/
│     ├── testing/
│     ├── reviewer/
│     └── memory/
├── tools/           file ops, shell, search, git, ...
├── docker/          Dockerfiles & compose
├── docs/            architecture notes (this lives here)
├── scripts/         dev / ops scripts
├── infra/           deployment config
├── prompts/         agent system prompts
└── README.md
```
