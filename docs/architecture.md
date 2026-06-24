# Architecture

System-level architecture. For the original product design see
[`00-product-design/`](00-product-design/).

## Monorepo layout

```
forge-ai/
├── apps/
│   ├── web/                 Next.js frontend
│   └── api/                 FastAPI backend
├── packages/
│   ├── agents/              All AI agents
│   ├── core/                Shared utilities
│   ├── prompts/             System prompts
│   ├── tools/               Tool implementations
│   ├── memory/              Memory layer
│   ├── rag/                 RAG logic
│   └── models/              LLM provider layer (Model Router)
├── infrastructure/
│   ├── docker/              Dockerfiles
│   ├── postgres/ redis/ qdrant/ ollama/   service-specific config
├── docs/
├── scripts/
├── .env.example
├── docker-compose.yml
├── Makefile
└── README.md
```

**Why a monorepo?** ForgeAI will eventually have 10+ agents, 30+ APIs, 100+
prompts, and multiple LLMs. A flat `frontend/`–`backend/` split would not
scale; `apps/` + `packages/` keeps each concern isolated and independently
evolvable while sharing one toolchain and one `docker-compose`.

## Request path

Every request follows the same layered path:

```
Frontend  →  API Routes  →  Service Layer  →  Agent Manager  →  LangGraph
          →  Agents  →  Tools  →  LLM (Model Router)  →  Database
```

In Phase 1, only **Frontend → API Routes → Service Layer → Database** seams
exist (and the DB layer is empty until Phase 3). The agent layers are stubs
that get filled in Phases 4–7.

## Local services (Docker Compose)

```
                    Docker
 ┌──────────────────────────────────────┐
 │  PostgreSQL   system of record        │
 │  Redis        jobs / queue / locks    │
 │  Qdrant       vector embeddings       │
 │  Ollama       local LLMs              │
 │  ForgeAI API  FastAPI app             │
 │  (later: Langfuse, nginx)             │
 └──────────────────────────────────────┘
```

## Model routing

Agents never call a provider SDK directly — they go through the Model Router
(`packages/models`, Phase 4). For the MVP everything is local via **Ollama**:

| Env var          | Default            | Role                     |
|------------------|--------------------|--------------------------|
| `MODEL_PLANNER`  | `qwen3:8b`         | Planning & reasoning     |
| `MODEL_CODER`    | `deepseek-coder`   | Code generation          |
| `MODEL_RESEARCH` | `llama3.1:8b`      | Research & summaries     |
| `MODEL_EMBED`    | `nomic-embed-text` | Embeddings for RAG       |

No OpenAI key. No Claude key. See ADR-0003 in [`DECISIONS.md`](DECISIONS.md).
