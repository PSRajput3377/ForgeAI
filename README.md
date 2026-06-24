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
| 0     | Product Design        | ✅ Complete    |
| 1     | Project Setup         | ⬜ Not started |
| 2     | Authentication        | ⬜ Not started |
| 3     | Database              | ⬜ Not started |
| 4     | Agent Architecture    | ⬜ Not started |
| 5     | Tool System           | ⬜ Not started |
| 6     | Memory + RAG          | ⬜ Not started |
| 7     | Multi-Agent Workflow  | ⬜ Not started |
| 8     | Docker Sandbox        | ⬜ Not started |
| 9     | GitHub Integration    | ⬜ Not started |
| 10    | Dashboard             | ⬜ Not started |
| 11    | Deployment            | ⬜ Not started |

## Documentation

The full product design lives in [`docs/00-product-design/`](docs/00-product-design/).
Architectural decisions are logged in [`docs/DECISIONS.md`](docs/DECISIONS.md).

## Tech stack (at a glance)

**Frontend:** Next.js · React · TypeScript · Tailwind · shadcn/ui
**Backend:** FastAPI · LangGraph · SQLAlchemy · WebSockets
**Data:** PostgreSQL · Redis · Qdrant
**AI:** LiteLLM (model router) · Ollama · LangGraph · Langfuse
**Infra:** Docker · Docker Compose

See [`docs/00-product-design/05-tech-stack.md`](docs/00-product-design/05-tech-stack.md) for the rationale.
