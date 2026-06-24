# Database Design

PostgreSQL schema. The **auth & multi-tenancy tables are implemented** (Phase 7)
as async SQLAlchemy models in `apps/api/app/db/models.py`; the original MVP
entities below are the baseline they extend. Same models run on SQLite for
tests (ADR-0018).

## Multi-tenancy & auth (Phase 7, implemented)

```
users ──< memberships >── workspaces ──< projects
organizations ──< workspaces
workspaces ──< invitations
workspaces ──< approvals / activity
projects ──< comments
```

| Table | Key columns |
|-------|-------------|
| `users` | id, email (unique), name, password_hash (Argon2), avatar |
| `organizations` | id, name, slug (unique), owner_id → users |
| `workspaces` | id, organization_id → orgs, name |
| `memberships` | user_id, workspace_id, role (owner/admin/member/viewer); unique(user, workspace) |
| `projects` | id, workspace_id → workspaces, name, description |
| `invitations` | id, workspace_id, email, role, token (unique), accepted, expires_at |
| `approvals` | id, workspace_id, action, requested_by, approved_by, status |
| `activity` | id, workspace_id, user_id, action, detail (audit + feed) |
| `comments` | id, project_id, user_id, body |
| `pr_approvals` | id, status, repository, owner, name, pr_title, pr_plan (JSON), pr_url, decided_by — persisted PR approvals (ADR-0024) |

RBAC roles rank `owner > admin > member > viewer`. See [auth.md](auth.md).

---

## Original MVP entities (baseline)

## ER diagram

```mermaid
erDiagram
    users ||--o{ projects : "creates"
    projects ||--o{ sessions : "has"
    projects ||--o{ tasks : "has"
    sessions ||--o{ messages : "contains"
    tasks ||--o{ tool_calls : "produces"
    users {
        uuid id PK
        text email UK
        text password_hash
        timestamptz created_at
    }
    projects {
        uuid id PK
        text name
        text path
        uuid created_by FK
    }
    sessions {
        uuid id PK
        uuid project_id FK
    }
    messages {
        uuid id PK
        uuid session_id FK
        text role
        text content
    }
    tasks {
        uuid id PK
        uuid project_id FK
        text status
        text agent
    }
    tool_calls {
        uuid id PK
        uuid task_id FK
        text tool
        jsonb input
        jsonb output
    }
```

## Entities

### users
| Column         | Type        | Notes                  |
|----------------|-------------|------------------------|
| id             | uuid (PK)   |                        |
| email          | text        | unique                 |
| password_hash  | text        |                        |
| created_at     | timestamptz | default now()          |

### projects
| Column       | Type        | Notes                       |
|--------------|-------------|-----------------------------|
| id           | uuid (PK)   |                             |
| name         | text        |                             |
| description  | text        | nullable                    |
| path         | text        | workspace path on disk      |
| created_by   | uuid (FK)   | → users.id                  |
| created_at   | timestamptz | default now()               |

### sessions
A conversation thread within a project.
| Column      | Type        | Notes              |
|-------------|-------------|--------------------|
| id          | uuid (PK)   |                    |
| project_id  | uuid (FK)   | → projects.id      |
| created_at  | timestamptz | default now()      |

### messages
| Column      | Type        | Notes                          |
|-------------|-------------|--------------------------------|
| id          | uuid (PK)   |                                |
| session_id  | uuid (FK)   | → sessions.id                  |
| role        | text        | user / assistant / agent       |
| content     | text        |                                |
| created_at  | timestamptz | default now()                  |

### tasks
A unit of work executed by the agent team.
| Column      | Type        | Notes                                   |
|-------------|-------------|-----------------------------------------|
| id          | uuid (PK)   |                                         |
| project_id  | uuid (FK)   | → projects.id                           |
| status      | text        | pending / running / done / failed       |
| agent       | text        | which agent currently owns the task     |
| created_at  | timestamptz | default now()                           |

### tool_calls
The audit record of every tool invocation an agent makes (the backing store for
the Logs UI). Mirrors the `AgentMessage`/tool trail in [state.md](state.md).
| Column     | Type        | Notes                          |
|------------|-------------|--------------------------------|
| id         | uuid (PK)   |                                |
| task_id    | uuid (FK)   | → tasks.id                     |
| tool       | text        | filesystem / terminal / git …  |
| input      | jsonb       | tool arguments                 |
| output     | jsonb       | `ToolResult` (ok/output/error) |
| created_at | timestamptz | default now()                  |

## Indexes & constraints

- **PKs:** UUID on every table (avoids enumeration, eases distribution).
- **Unique:** `users.email`.
- **Foreign keys:** `projects.created_by → users`, `sessions.project_id →
  projects`, `messages.session_id → sessions`, `tasks.project_id → projects`,
  `tool_calls.task_id → tasks` — all `ON DELETE CASCADE` so deleting a project
  cleans up its children.
- **Indexes (planned):** `projects(created_by)`, `sessions(project_id)`,
  `messages(session_id, created_at)`, `tasks(project_id, status)`,
  `tool_calls(task_id, created_at)` — to support the common list/timeline reads.
- **Extensions:** `pgcrypto` for `gen_random_uuid()` (see
  `infrastructure/postgres/init.sql`).

## Notes & future tables

- `status` / `role` / `agent` are text for now; may become enums once the agent
  roster is final.
- Embeddings/vectors live in **Qdrant**, not Postgres ([architecture.md](architecture.md)).
- **Future:** `logs` (structured run logs), `users.settings` (model
  preferences), `api_keys`, `project_memory` (long-term memory pointers).
