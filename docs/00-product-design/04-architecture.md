# 04 — System Architecture

## Backend request path

Every request flows through the **Agent Manager**. There is no path that
skips it — this keeps orchestration centralized and observable.

```
Frontend
  ↓
FastAPI            HTTP + WebSocket entrypoints
  ↓
API Layer          request validation, auth, routing
  ↓
Agent Manager      the orchestrator
  ↓
LangGraph          stateful multi-agent workflow engine
  ↓
Agents             Planner, Researcher, Coder, Tester, Reviewer, DevOps
  ↓
Tools              file ops, shell, search, git, ...
  ↓
LLM                via the Model Router
```

## Frontend (Next.js)

Pages:

- **Dashboard** — live agent execution view
- **Projects** — list / create / open
- **Chat** — task input and conversation
- **Logs** — tool-call stream
- **Settings** — model/provider selection
- **History** — past tasks per project

## Data stores

Three stores, each with a clear job.

### PostgreSQL — system of record
Users, projects, tasks, agent runs, logs (durable relational data).

### Redis — fast, ephemeral state
- Running jobs
- Agent queue
- Temporary state
- Locks

### Qdrant — vector database
- Project files (embeddings)
- Documentation
- Conversation history
- Retrieval for RAG / memory

## Model Router (do NOT hardcode a provider)

Agents never call a provider SDK directly. They call a **Model Router**, so we
can swap or add providers with almost no code changes.

```
Planner / any agent
        ↓
   Model Router          (LiteLLM-based)
        ↓
 ┌──────┬───────┬──────┬────────────┐
 ▼      ▼       ▼      ▼            ▼
Ollama Gemini  Groq  OpenRouter  (more later)
```

Provider/model choice is configurable from **Settings** (feature #7).

## Why this shape

- **Single entrypoint (Agent Manager)** → one place to observe, log, and control.
- **LangGraph** → durable, inspectable multi-agent state (vs. ad-hoc loops).
- **Separate stores** → relational truth (PG), speed/coordination (Redis),
  semantic recall (Qdrant) — each tool for its job.
- **Model Router** → provider independence from day one.
