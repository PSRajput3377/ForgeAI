# Architecture Decision Records

Each ADR captures one significant decision: the context, the decision, and the
consequences. They are immutable once accepted — a reversal is a *new* ADR that
supersedes the old one.

The narrative "why we chose X" rationale lives in [`../decisions.md`](../decisions.md);
this folder is the formal record.

| ADR | Title | Status | Phase |
|-----|-------|--------|-------|
| [0001](ADR-0001.md) | Multi-agent team, not a single LLM call | Accepted | 0 |
| [0002](ADR-0002.md) | The Engineering Manager never writes code | Accepted | 0 |
| [0003](ADR-0003.md) | All LLM access goes through a Model Router | Accepted | 0 |
| [0004](ADR-0004.md) | Three purpose-specific data stores | Accepted | 0 |
| [0005](ADR-0005.md) | Ruthless MVP scope for v1.0 | Accepted | 0 |
| [0006](ADR-0006.md) | Monorepo with apps/ + packages/ | Accepted | 1 |
| [0007](ADR-0007.md) | uv for Python, pinned to 3.12 | Accepted | 1 |
| [0008](ADR-0008.md) | Hand-scaffold the app starters | Accepted | 1 |
| [0009](ADR-0009.md) | Agent system lives in packages/, imported by API | Accepted | 2 |
| [0010](ADR-0010.md) | LangGraph over one shared ProjectState | Accepted | 2 |
| [0011](ADR-0011.md) | EchoProvider for offline deterministic testing | Accepted | 2 |
| [0012](ADR-0012.md) | Diagrams as Mermaid, not PNG | Accepted | 2.5 |
| [0013](ADR-0013.md) | Separate specs/ (what) from docs/ (how) | Accepted | 2.5 |
| [0014](ADR-0014.md) | Capability System: request capabilities, not tools | Accepted | 3 |
| [0015](ADR-0015.md) | Memory & RAG: pluggable backends, offline by default | Accepted | 4 |
| [0016](ADR-0016.md) | Sandbox abstraction with offline backends | Accepted | 5 |
| [0017](ADR-0017.md) | Event-driven observability with offline backends | Accepted | 6 |
| [0018](ADR-0018.md) | Async SQLAlchemy with SQLite-in-memory for offline tests | Accepted | 7 |
| [0019](ADR-0019.md) | GitHub provider abstraction with an offline fake | Accepted | 8 |
| [0020](ADR-0020.md) | Author commits via local clone + git, not REST | Accepted | 8.1 |

## Template

```markdown
# ADR-NNNN — Title

- **Status:** Proposed | Accepted | Superseded by ADR-XXXX
- **Phase:** N
- **Date:** YYYY-MM-DD

## Context
What problem/forces led to this decision?

## Decision
What we decided.

## Consequences
Trade-offs, what becomes easier/harder, what we explicitly rejected.
```
