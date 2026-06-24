# Database Design

Initial PostgreSQL schema for the MVP. **Planned here in Phase 1; implemented
with SQLAlchemy + Alembic in Phase 3.** This is enough for v1.0.

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

## Relationships

```
users 1──* projects 1──* sessions 1──* messages
                   └──* tasks
```

## Notes

- UUID primary keys throughout (avoids enumeration, eases distribution).
- `status` / `role` / `agent` are stored as text for now; may become enums in
  Phase 3 once the agent roster is final.
- Embeddings/vectors live in **Qdrant**, not Postgres (see `architecture.md`).
