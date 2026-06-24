# API

REST + WebSocket surface of the FastAPI backend.

> Phase 1 ships only health/banner endpoints. Real endpoints (auth, projects,
> sessions, tasks, agent streaming) are added from Phase 2 onward and
> documented here as they land.

Interactive docs are always available when the API is running:
**http://localhost:8000/docs** (Swagger) and **/redoc**.

## Current endpoints

| Method | Path          | Description                                      |
|--------|---------------|--------------------------------------------------|
| GET    | `/`           | Service banner (name + version)                  |
| GET    | `/health`     | Liveness probe                                   |
| POST   | `/agents/run` | Run the full multi-agent workflow for a request  |

### `POST /agents/run`

```jsonc
// request
{ "user_request": "Add JWT authentication", "project_path": "/work/myproj" }

// response
{ "final_response": "...", "review_verdict": "approved",
  "tasks": 6, "files_changed": ["generated/output.txt"], "retries": 0 }
```

> Requires Ollama running with models pulled (`make pull-models`). The offline
> path is covered by the test suite via `EchoProvider`.

## Conventions (for endpoints added later)

- JSON request/response bodies validated with Pydantic models.
- Auth via JWT bearer tokens (Phase 2).
- Long-running agent runs stream over WebSockets.
- Errors use standard HTTP status codes with a `{ "detail": ... }` body.
