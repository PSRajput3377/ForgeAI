/**
 * Landing page (Phase 1 placeholder).
 *
 * Confirms the frontend renders and can reach the API. The real screens
 * (Login, Dashboard, Workspace, Settings) arrive in Phase 10.
 */
import { ApiStatus } from "@/components/ApiStatus";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-6 p-8">
      <div className="text-center">
        <h1 className="text-4xl font-bold tracking-tight">ForgeAI</h1>
        <p className="mt-2 text-neutral-400">
          A team of AI engineers — Planner · Coder · Reviewer
        </p>
      </div>
      <ApiStatus />
      <p className="text-xs text-neutral-600">Phase 1 — Foundation</p>
    </main>
  );
}
