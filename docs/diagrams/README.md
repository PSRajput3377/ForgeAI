# Diagrams

Diagrams are kept as **Mermaid** (`.mmd`) source, not binary images.

**Why Mermaid instead of `.png`:** source diagrams are version-controlled,
diffable in pull requests, render natively on GitHub, and never go stale
against the code. Binary PNGs can't be reviewed or regenerated.

| File                | Shows                                            |
|---------------------|--------------------------------------------------|
| `architecture.mmd`  | System layers: frontend → backend → agents → infra |
| `sequence.mmd`      | Request lifecycle across the agent team          |
| `workflow.mmd`      | The LangGraph agent workflow (with reflection loop) |
| `state.mmd`         | `ProjectState` and which agents read/write it    |
| `er.mmd`            | Database entity-relationship diagram             |

## Viewing

- **GitHub** renders ```` ```mermaid ```` blocks automatically — see the
  embedded copies in `architecture.md`, `workflows.md`, `state.md`, etc.
- **VS Code**: the "Markdown Preview Mermaid Support" extension.
- **CLI / PNG export** (only if a raster image is ever required):

  ```bash
  npx @mermaid-js/mermaid-cli -i docs/diagrams/architecture.mmd -o architecture.png
  ```
