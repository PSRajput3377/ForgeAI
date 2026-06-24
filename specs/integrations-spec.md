# Enterprise Integrations Specification

Contracts for the integration ecosystem. Narrative in
[`../docs/integrations.md`](../docs/integrations.md). Source:
`packages/integrations/`.

## Connectors

- Every system MUST implement `Connector` (`search`, `get`, and — if writable —
  `create`/`update`) over normalized `ExternalObject`s.
- A read-only connector MUST raise `NotImplementedError` on write.
- Each `ExternalObject` MUST carry a stable cross-system `ref`.
- `Fake*` (offline) and production connectors MUST be interchangeable.

## Integration Hub

- Agents MUST access external systems only through the hub.
- The hub MUST enforce per-agent connector permissions on read and write.
- The hub MUST gate writes flagged by the approval rules behind an approver, and
  MUST raise if not approved.
- A read-only connector MUST reject writes at the hub.
- `search` MUST query multiple connected systems and skip non-readable ones.

## Security

- Per-agent permissions MUST be an allow-list of `(system, capability)`.
- Sensitive writes (email, ticket creation, prod doc updates) MUST require
  approval by default.
- Secrets MUST be encrypted at rest; plaintext secrets MUST NOT be stored.

## Knowledge graph & retrieval

- The graph MUST link cross-system refs with a typed relationship.
- `related(ref)` MUST traverse multiple hops (bounded).
- `answer(question)` MUST aggregate evidence across systems + related refs.

## Acceptance criteria

- [ ] All 8 systems implemented as connectors with correct read/write capability.
- [ ] Hub blocks unauthorized agents and read-only writes.
- [ ] Gated writes blocked without approval; allowed with approval; non-gated
      writes skip approval.
- [ ] Cross-system search returns hits from multiple systems.
- [ ] Knowledge graph multi-hop `related` works; `answer` aggregates evidence.
- [ ] Secrets encrypted at rest (round-trip; blob ≠ plaintext).
- [ ] Entire suite runs offline.
