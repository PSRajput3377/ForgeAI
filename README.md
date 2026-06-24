# ForgeAI

**An autonomous AI engineering platform that behaves like a team of software engineers — not a single chatbot.**

Most AI coding tools are one model answering one prompt:

```
User → LLM → Answer
```

ForgeAI is a coordinated team:

```
User
  ↓
Engineering Manager   (delegates — never writes code)
  ↓
Planner → Researcher → Coder → Tester → Reviewer → DevOps
  ↓
Result
```

You describe a task ("Add JWT authentication"). A Manager agent breaks it
down and delegates to specialist agents. You watch them plan, research,
code, test, and review — in real time — inside a sandboxed project.

---

## Who it's for

- **Developers** — "Add authentication to my app."
- **Startups** — "We need CRUD APIs."
- **Students** — "Build my assignment."
- **Companies** — "Build an internal dashboard."

## Status

🚧 **Pre-alpha — in active development.**

The project is being built in 12 phases. See the
[Development Roadmap](docs/00-product-design/00-roadmap.md).

| Phase | Name                  | Status         |
|-------|-----------------------|----------------|
| 0     | Product Design               | ✅ Complete    |
| 1     | Project Setup                | ✅ Complete    |
| 2     | AI Engine & Agent Architecture | ✅ Complete  |
| 3     | Tool System                  | ⬜ Not started |
| 4     | Memory + RAG                 | ⬜ Not started |
| 5     | Docker Sandbox               | ⬜ Not started |
| 6     | GitHub Integration           | ⬜ Not started |
| 7     | Authentication               | ⬜ Not started |
| 8     | Database                     | ⬜ Not started |
| 9     | Dashboard                    | ⬜ Not started |
| 10    | Deployment                   | ⬜ Not started |

> Note: the phase order was revised in Phase 2 to front-load the AI engine
> (the product's core). See `docs/decisions.md`.

## Documentation

ForgeAI is documented so you can understand it **without reading the source**.

- **[`docs/`](docs/README.md)** — how it works: architecture, agents, workflows,
  shared state, tools, database, API, prompts, security, testing, deployment,
  plus Mermaid diagrams and an [ADR log](docs/adr/README.md).
- **[`specs/`](specs/README.md)** — what each component must do: the checkable
  contracts (agent, tool, state, API, prompt, evaluation, v1.0 acceptance).
- **[`docs/00-product-design/`](docs/00-product-design/)** — the original
  product vision (Phase 0).

The "why" behind each technology choice is in [`docs/decisions.md`](docs/decisions.md).

## Tech stack (at a glance)

**Frontend:** Next.js · React · TypeScript · Tailwind · shadcn/ui
**Backend:** FastAPI · LangGraph · SQLAlchemy · WebSockets
**Data:** PostgreSQL · Redis · Qdrant
**AI:** LiteLLM (model router) · Ollama · LangGraph · Langfuse
**Infra:** Docker · Docker Compose

See [`docs/00-product-design/05-tech-stack.md`](docs/00-product-design/05-tech-stack.md) for the rationale.
