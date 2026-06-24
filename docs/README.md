# ForgeAI Documentation

Everything you need to understand ForgeAI **without reading the source code**.

> `docs/` explains **how** ForgeAI works.
> [`../specs/`](../specs/) defines **what** each component must do. (ADR-0013)

## Start here

| If you want to…                        | Read                              |
|----------------------------------------|-----------------------------------|
| Understand the whole system            | [architecture.md](architecture.md) |
| Run it locally                         | [setup.md](setup.md)              |
| Know what each agent does              | [agents.md](agents.md)            |
| See how a request flows end-to-end     | [workflows.md](workflows.md)      |
| Understand the shared state            | [state.md](state.md)              |
| Know the tool interfaces               | [tools.md](tools.md)              |
| Understand memory & RAG                | [memory.md](memory.md)            |
| Understand code execution & sandboxing | [execution.md](execution.md)      |
| Understand observability & the workspace | [observability.md](observability.md) |
| Understand auth, teams & multi-tenancy | [auth.md](auth.md)                |
| Understand GitHub integration & PR/CI automation | [github.md](github.md)  |
| Understand enterprise integrations & knowledge graph | [integrations.md](integrations.md) |
| Understand production reliability, scale & ops | [production.md](production.md) |
| See the database schema                | [database.md](database.md)        |
| Use the API                            | [api.md](api.md)                  |
| Read the agent prompts                 | [prompts.md](prompts.md)          |
| Understand the security model          | [security.md](security.md)        |
| Understand the test strategy           | [testing.md](testing.md)          |
| Deploy it                              | [deployment.md](deployment.md)    |
| Know *why* we chose X                  | [decisions.md](decisions.md) · [adr/](adr/README.md) |
| See the plan                           | [roadmap.md](roadmap.md)          |

## Maps & diagrams

[diagrams/](diagrams/README.md) — architecture, sequence, workflow, state, ER
(Mermaid source, embedded throughout the docs).

## Product design (Phase 0)

The original product vision lives in [00-product-design/](00-product-design/).

## Contributing

Conventions and the definition of done: [contributing.md](contributing.md).
