# forge-api

ForgeAI backend (FastAPI).

## Layered architecture

Every request follows one path:

```
Frontend
  ↓
API Routes        app/api/        HTTP/WebSocket endpoints, validation
  ↓
Service Layer     app/services/   business logic
  ↓
Agent Manager     (Phase 4)       orchestrator
  ↓
LangGraph         (Phase 7)       multi-agent workflow
  ↓
Agents            packages/agents
  ↓
Tools             packages/tools
  ↓
LLM               packages/models (Model Router)
  ↓
Database          app/db/         PostgreSQL via SQLAlchemy
```

In Phase 1 only the **API Routes**, **config**, and **Service Layer** seams
exist. No AI logic yet.

## Local development

```bash
uv sync                  # install deps (Python 3.12)
uv run uvicorn app.main:app --reload
```

Or from the repo root: `make api-dev`.

## Health check

```bash
curl http://localhost:8000/health
```
