# ForgeAI Development Roadmap

The project is built in **12 phases**. We complete one phase at a time and
do not jump ahead.

| Phase | Name                  | Goal                                                        |
|-------|-----------------------|-------------------------------------------------------------|
| 0     | **Product Design**    | Decide *exactly* what we are building. (This phase.)        |
| 1     | Project Setup         | Repo structure, tooling, Docker Compose skeleton.           |
| 2     | Authentication        | Login / signup, sessions, protected routes.                 |
| 3     | Database              | PostgreSQL schema, migrations, core models.                 |
| 4     | Agent Architecture    | Base agent abstraction, Manager + Planner.                  |
| 5     | Tool System           | File ops, shell, search — the agents' hands.                |
| 6     | Memory + RAG          | Qdrant embeddings, project memory, retrieval.               |
| 7     | Multi-Agent Workflow  | LangGraph orchestration of the full team.                   |
| 8     | Docker Sandbox        | Isolated, safe code execution.                              |
| 9     | GitHub Integration    | Branches, commits, PRs.                                     |
| 10    | Dashboard             | The full Next.js UI.                                        |
| 11    | Deployment            | Production deploy.                                          |

## Phase 0 deliverables (this phase)

Phase 0 produces **documentation only** — no application code.

- [x] Product vision — [`01-vision.md`](01-vision.md)
- [x] Target users & core features — [`02-users-and-features.md`](02-users-and-features.md)
- [x] User flow & delegation model — [`03-user-flow.md`](03-user-flow.md)
- [x] System architecture — [`04-architecture.md`](04-architecture.md)
- [x] Tech stack (locked) — [`05-tech-stack.md`](05-tech-stack.md)
- [x] MVP scope (v1.0) — [`06-mvp-scope.md`](06-mvp-scope.md)
- [x] Engineering principles — [`07-principles.md`](07-principles.md)

When all boxes are checked and committed, Phase 0 is done.
