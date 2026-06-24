# Agent Specification

The contract **every** agent must satisfy. Narrative descriptions are in
[`../docs/agents.md`](../docs/agents.md).

## Interface

- An agent MUST subclass `BaseAgent` and define a unique `role: AgentRole`.
- An agent MUST implement `async def run(self, state: ProjectState) -> ProjectState`.
- An agent MUST depend only on `core` contracts and the `ModelRouter`.
- An agent MUST NOT import or call another agent. (Sequencing is the workflow's
  job — [ADR-0010](../docs/adr/ADR-0010.md).)

## Behavior

- An agent MUST do exactly one job (single responsibility).
- An agent MUST read its inputs from and write its outputs to `state` only.
- An agent MUST append an `AgentMessage` to `state.messages` via `state.record()`
  describing its outcome (sender, status, summary, any `files_changed`).
- An agent SHOULD obtain LLM output via `self._ask(...)` (role-routed), never by
  constructing a provider directly.
- An agent MUST set a sensible status (`COMPLETED` / `FAILED`) on its message.

## Role-specific MUST NOTs

- **Manager** MUST NOT produce code or `files_changed`.
- **Planner / Researcher / Memory / Review** MUST NOT write to `generated_code`.
- **Coder** MUST NOT execute commands or perform git operations.
- **Execution / Testing** MUST run only inside the sandbox (no host shell).

## Acceptance criteria

- [ ] Has a unique `role`; registered in `AgentRole`.
- [ ] `run()` is async, takes and returns `ProjectState`.
- [ ] Records at least one `AgentMessage`.
- [ ] No import of another agent module.
- [ ] Has at least one unit test exercising its state transition.
- [ ] Honors its role-specific MUST NOTs (verified by tests where applicable,
      e.g. `test_manager_never_writes_code`).
