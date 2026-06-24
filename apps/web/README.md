# @forge-ai/web

ForgeAI frontend — Next.js 15 (App Router) · React 19 · TypeScript · Tailwind ·
Zustand. shadcn/ui is added when the real UI lands in Phase 10.

## Local development

```bash
npm install
npm run dev      # http://localhost:3000
```

Or from the repo root: `make web-dev`.

Set `NEXT_PUBLIC_API_URL` (defaults to `http://localhost:8000`) to point the
landing page's health check at the backend.

## Planned screens (Phase 10)

- **Login** — email / password
- **Dashboard** — recent tasks, running agents, usage
- **Workspace** — chat, file explorer, logs, current agent, memory
- **Settings** — models, projects, preferences

Phase 1 ships only a placeholder landing page that verifies the
frontend↔backend connection.
