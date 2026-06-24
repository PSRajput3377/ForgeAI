# Agents

> Placeholder — populated in **Phase 4 (Agent Architecture)** and
> **Phase 7 (Multi-Agent Workflow)**.

ForgeAI orchestrates a team of specialist agents under an Engineering Manager
that delegates and never writes code (see ADR-0001 / ADR-0002).

Planned roster:

| Agent       | Responsibility                          | MVP (v1.0) |
|-------------|-----------------------------------------|------------|
| Manager     | Interpret, decompose, delegate, sequence| —          |
| Planner     | Produce the step-by-step plan           | ✅         |
| Researcher  | Gather context / docs                   | later      |
| Coder       | Write & edit code                       | ✅         |
| Tester      | Run and validate                        | later      |
| Reviewer    | Review changes, accept/reject           | ✅         |
| DevOps      | Build / run / deploy concerns           | later      |

Each agent's system prompt lives in `packages/prompts`. Implementation lives in
`packages/agents`. Orchestration (LangGraph) is described here once built.
