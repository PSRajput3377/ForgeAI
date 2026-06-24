# v1.0 Acceptance Criteria

The definition of "v1.0 is done." Scope is fixed by
[ADR-0005](../docs/adr/ADR-0005.md); this is the checklist that proves it.

## In scope (must all be true for v1.0)

- [ ] **Login** — a user can sign up and log in (JWT).
- [ ] **Create Project** — a user can create a project and choose a stack.
- [ ] **Chat** — a user can submit a task in natural language.
- [ ] **Planner agent** — produces a real, structured plan from the request.
- [ ] **Coder agent** — writes real files into the project workspace.
- [ ] **Review agent** — approves or requests changes on real criteria.
- [ ] **Local file editing** — changes are applied via the sandboxed Filesystem tool.
- [ ] **Docker execution** — generated code runs in an isolated container.
- [ ] **Project memory** — past tasks/decisions are recalled for new requests.
- [ ] The full workflow runs end-to-end against **real Ollama models**.
- [ ] Each of the above is covered by tests and documented.

## Explicitly OUT of scope for v1.0

- ❌ Slack / Jira integrations
- ❌ AWS / cloud deployment automation
- ❌ Browser automation
- ❌ Auto-merge of PRs

## Quality bar

- [ ] All components meet their specs (`agent-spec`, `tool-spec`, `state-spec`,
      `api-contracts`, `prompt-spec`).
- [ ] Offline test suite green; ruff + black clean.
- [ ] An eval run exists for the core requests ([evaluation-spec.md](evaluation-spec.md)).
- [ ] Security rules in [`../docs/security.md`](../docs/security.md) are enforced
      (sandbox, path validation, withheld destructive ops, JWT).
- [ ] Docs let a newcomer understand the system without reading source.

When every box above is checked, v1.0 ships.
