# packages/

Shared Python packages used by the backend and agents. Each has **one
responsibility**. All are scaffolded in Phase 1 (empty) and filled in their
own phases.

| Package    | Responsibility                                   | Built in |
|------------|--------------------------------------------------|----------|
| `core`     | Shared utilities, types, constants               | ongoing  |
| `models`   | LLM provider layer / Model Router (LiteLLM)      | Phase 4  |
| `agents`   | All AI agents (manager, planner, coder, ...)     | Phase 4  |
| `prompts`  | System prompts for each agent                    | Phase 4  |
| `tools`    | Tool implementations (file ops, shell, search)   | Phase 5  |
| `memory`   | Memory layer                                     | Phase 6  |
| `rag`      | RAG logic (Qdrant retrieval/embeddings)          | Phase 6  |

They are importable on `PYTHONPATH` (set in the API Dockerfile and for local
dev). No AI logic exists yet — these are intentionally empty namespaces.
