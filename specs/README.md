# specs/

**What every component must do** — the checkable contracts.

> `docs/` explains **how** ForgeAI works today.
> `specs/` defines **what** each component must do. (ADR-0013)

Every implementation is checked against its spec before merge. A spec defines
inputs, outputs, invariants, and acceptance criteria — independent of the
current implementation.

| Spec | Defines |
|------|---------|
| [agent-spec.md](agent-spec.md) | The contract every agent must satisfy |
| [tool-spec.md](tool-spec.md) | The contract every tool must satisfy |
| [memory-spec.md](memory-spec.md) | Memory scopes, manager, scoring, context |
| [rag-spec.md](rag-spec.md) | Chunking, embedding, indexing, retrieval |
| [execution-spec.md](execution-spec.md) | Sandbox, security, error classification, retry loop |
| [observability-spec.md](observability-spec.md) | Events, bus, store, metrics, tracing, approvals |
| [auth-spec.md](auth-spec.md) | Authentication, RBAC, workspace isolation, invitations |
| [github-spec.md](github-spec.md) | Provider, branching, PRs, CI, autonomous loop |
| [integrations-spec.md](integrations-spec.md) | Connectors, hub, permissions, approvals, knowledge graph |
| [state-spec.md](state-spec.md) | `ProjectState` field rules & invariants |
| [api-contracts.md](api-contracts.md) | Request/response contracts per endpoint |
| [prompt-spec.md](prompt-spec.md) | What a well-formed agent prompt must contain |
| [evaluation-spec.md](evaluation-spec.md) | How we measure agent/output quality |
| [roadmap-v1.md](roadmap-v1.md) | The acceptance criteria for v1.0 |

## Spec format

Each spec uses **MUST / SHOULD / MUST NOT** (RFC-2119 sense) and ends with an
**Acceptance criteria** checklist that a reviewer can verify.
