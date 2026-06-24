# Prompt Specification

What a well-formed agent prompt must contain. The current prompts are documented
in [`../docs/prompts.md`](../docs/prompts.md). Source:
`packages/prompts/registry.py`.

## A prompt MUST

- State a clear **persona** ("You are a senior backend engineer").
- State the agent's **single job** in one or two sentences.
- State the **hard constraints** explicitly, especially the MUST NOTs
  ("Never write code", "Only write code. Never explain.").
- Be **role-specific** — no do-everything prompts.

## A prompt SHOULD

- Be concise; avoid contradictory instructions.
- Describe the expected **output shape** when the agent must return structured
  data (e.g. "Output either APPROVED or a list of required changes").
- Avoid hardcoded project assumptions (those come from state/context).

## A prompt MUST NOT

- Embed secrets, credentials, or environment-specific values.
- Duplicate another agent's responsibility.
- Exist in code without a corresponding entry in `docs/prompts.md`.

## Governance

- Prompts are stored in the registry (`system_prompt(role)`), not inline in
  agent logic, so they can be versioned and iterated independently.
- A prompt change is reviewed like code and its quality impact measured via the
  [evaluation spec](evaluation-spec.md).

## Acceptance criteria

- [ ] Defined in `PROMPTS` for its `AgentRole`.
- [ ] Contains persona + single job + explicit constraints.
- [ ] Mirrored in `docs/prompts.md`.
- [ ] Contains no secrets or environment-specific values.
