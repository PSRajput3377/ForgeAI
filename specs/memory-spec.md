# Memory Specification

Contracts for the memory subsystem. Narrative in
[`../docs/memory.md`](../docs/memory.md). Source: `packages/memory/`.

## Scopes

- There MUST be exactly four scopes: `session`, `project`, `user`, `knowledge`.
- `session` memory MUST be addressable by `session_id`; `project` by
  `project_id`; `user` by `user_id`.

## Memory Manager

- Agents MUST access memory only through the `MemoryManager` — never the store
  or a database directly.
- `store_memory` MUST create-or-update by (scope, key, owner).
- `retrieve` MUST return items ranked by score (see Scoring) and MUST mark
  returned items as used (increment usage, update recency).
- `compress_session` MUST summarize and remove old items while keeping the most
  recent `keep_last`, and MUST be a no-op when there is nothing to compress.

## Scoring

- Score MUST combine recency, importance, usage frequency, and project
  relevance.
- Recency MUST use a logical tick clock (deterministic), not wall-clock.
- An item belonging to the active project MUST score higher than an otherwise
  identical item from another project.

## Store backends

- Any `MemoryStore` MUST implement `put / get / query / delete` and MUST be
  owner-scoped (a user's memory is not visible to another user).
- The offline `InMemoryStore` and the production PostgreSQL store MUST be
  interchangeable behind the interface.

## Context Builder

- MUST assemble at most a bounded-size context (`max_chars`).
- MUST omit empty sections.
- MUST draw relevant files from the Retriever when one is configured.

## Acceptance criteria

- [ ] Four scopes, owner-scoped, manager-mediated.
- [ ] Scoring is deterministic and honors all four signals.
- [ ] Compression keeps recent N and folds the rest into a summary.
- [ ] Context is bounded and omits empty sections.
- [ ] Tests cover persistence, scoring, compression, and context assembly.
