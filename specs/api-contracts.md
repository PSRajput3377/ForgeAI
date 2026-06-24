# API Contracts

Request/response contracts per endpoint. The human-readable API guide is in
[`../docs/api.md`](../docs/api.md). These are the authoritative shapes that
implementations and clients are checked against.

## Conventions

- All bodies are JSON and Pydantic-validated. Unknown fields are rejected.
- Errors use HTTP status codes with `{ "detail": <string|object> }`.
- Authenticated endpoints (once auth lands) require `Authorization: Bearer
  <jwt>`; missing/invalid → `401`.
- Timestamps are ISO-8601 UTC. IDs are UUID strings.

## Implemented

### `GET /health`
- **200** → `{ "status": "ok", "environment": "development" }`

### `GET /`
- **200** → `{ "service": "forge-api", "version": "0.1.0" }`

### `POST /agents/run`
- **Request:**
  ```json
  { "user_request": "string (required)",
    "project_id": "uuid | null",
    "project_path": "string | null" }
  ```
- **200:**
  ```json
  { "final_response": "string",
    "review_verdict": "approved | changes_requested | pending",
    "tasks": 6,
    "files_changed": ["generated/output.txt"],
    "retries": 0 }
  ```
- **422** → validation error (e.g. missing `user_request`).
- **502/504** (planned) → upstream model/provider unavailable.

## Planned (defined ahead of implementation)

### `POST /projects`
- **Request:** `{ "name": "string", "description": "string?", "stack": "string" }`
- **201:** the created project object.

### `GET /projects`
- **200:** `{ "projects": [ ... ] }`

### `POST /tools/run`
- **Request:** `{ "tool": "filesystem", "action": "read", "args": { ... } }`
- **200:** a `ToolResult` shape: `{ "ok": true, "output": "", "error": "", "data": {} }`

### `POST /chat`
- **Request:** `{ "session_id": "uuid", "content": "string" }`
- **200 / streaming:** assistant + agent messages (WebSocket for live runs).

## Acceptance criteria

- [ ] Every endpoint validates its request body and rejects unknown fields.
- [ ] Responses match the documented shape (typed Pydantic response models).
- [ ] Error responses use the `{ "detail": ... }` convention.
- [ ] Each endpoint has at least one test (happy path + one error path).
