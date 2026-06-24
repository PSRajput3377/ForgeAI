# Roadmap

The canonical phase roadmap lives in
[`00-product-design/00-roadmap.md`](00-product-design/00-roadmap.md).

## Phase status

| Phase | Name                  | Status         |
|-------|-----------------------|----------------|
| 0     | Product Design                 | ✅ Complete    |
| 1     | Project Setup                  | ✅ Complete    |
| 2     | AI Engine & Agent Architecture | ✅ Complete    |
| 2.5   | System Design & Documentation  | ✅ Complete    |
| 3     | Tool System & Action Engine    | ✅ Complete    |
| 4     | Memory, RAG & Knowledge Engine | ✅ Complete    |
| 5     | Autonomous Execution & Docker Sandbox | ✅ Complete |
| 6     | Developer Workspace & Observability | ✅ Complete |
| 7     | Auth, Multi-User Workspaces & Teams | ✅ Complete |
| 8     | GitHub Integration             | ⬜ Not started |
| 9     | Dashboard                      | ⬜ Not started |
| 10    | Deployment                     | ⬜ Not started |

> Database work (async SQLAlchemy, ADR-0018) landed inside Phase 7 because
> auth/multi-tenancy requires it — there is no longer a standalone DB phase.

> The original roadmap placed Authentication/Database earlier and split the
> agent work across later phases. Phase 2 front-loaded the AI engine (the core
> of the product), so subsequent phases were reordered. See `decisions.md`.
