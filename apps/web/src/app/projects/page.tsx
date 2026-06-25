"use client";

/**
 * Project chooser — the front door (Phase 13.4).
 *
 * Signed-in users land here first: Open an existing project, or Create a new one
 * from a starter template. Choosing a project binds it as active and opens the
 * workspace. No need to understand the architecture — pick a starter and go.
 */
import { useEffect, useState } from "react";
import {
  bootstrapProject,
  createProject,
  ensureWorkspace,
  listProjects,
  listStarters,
  type Project,
  type Starter,
} from "@/lib/api";
import { useAppStore } from "@/store/useAppStore";
import { useAuthStore } from "@/store/useAuthStore";

export default function ProjectsPage() {
  const accessToken = useAuthStore((s) => s.accessToken);
  const workspaceId = useAppStore((s) => s.workspaceId);
  const setWorkspaceId = useAppStore((s) => s.setWorkspaceId);
  const setActiveProject = useAppStore((s) => s.setActiveProject);

  const [projects, setProjects] = useState<Project[]>([]);
  const [starters, setStarters] = useState<Starter[]>([]);
  const [name, setName] = useState("");
  const [starter, setStarter] = useState("empty");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (!accessToken) {
      window.location.href = "/login";
      return;
    }
    (async () => {
      let ws = workspaceId;
      if (!ws) {
        ws = await ensureWorkspace();
        if (ws) setWorkspaceId(ws);
      }
      if (ws) setProjects(await listProjects(ws));
      setStarters(await listStarters());
      setReady(true);
    })();
  }, [accessToken, workspaceId, setWorkspaceId]);

  function open(p: Project) {
    setActiveProject(p.id, p.name);
    window.location.href = "/workspace";
  }

  async function create() {
    const trimmed = name.trim();
    if (!trimmed || !workspaceId || busy) return;
    setBusy(true);
    setError(null);
    try {
      const project =
        starter === "empty"
          ? await createProject(workspaceId, trimmed)
          : await bootstrapProject(workspaceId, trimmed, starter);
      if (!project) throw new Error("Could not create the project");
      setActiveProject(project.id, project.name);
      // A starter scaffolds files; jump straight into the workspace to build on it.
      window.location.href = "/workspace";
    } catch (e) {
      setError(e instanceof Error ? e.message : "Create failed");
      setBusy(false);
    }
  }

  if (!ready) {
    return (
      <main className="flex min-h-screen items-center justify-center gap-3 p-6 text-sm text-[var(--muted)]">
        <span className="spin-slow h-4 w-4 rounded-full border-2 border-[var(--accent)] border-t-transparent" />
        Loading your projects…
      </main>
    );
  }

  return (
    <main className="mx-auto min-h-screen max-w-5xl p-6 py-12">
      <header className="rise mb-10">
        <h1 className="text-3xl font-semibold tracking-tight">Your projects</h1>
        <p className="mt-2 text-sm text-[var(--muted)]">
          Open an existing project, or create one from a starter and let the agent team
          build it.
        </p>
      </header>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Create New */}
        <section className="glass rise p-6">
          <div className="mb-4 flex items-center gap-2">
            <span className="h-3 w-1 rounded-full bg-[var(--accent)]" />
            <h2 className="label">Create new project</h2>
          </div>
          <label className="mb-4 block">
            <span className="mb-1.5 block text-xs text-[var(--muted)]">Project name</span>
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="my-saas-app"
              className="w-full rounded-xl border border-[var(--panel-border)] bg-black/30 px-3 py-2.5 text-sm transition focus:border-[var(--accent)] focus:outline-none focus:ring-2 focus:ring-[var(--accent)]/20"
            />
          </label>

          <p className="mb-2 text-xs text-[var(--muted)]">Start from</p>
          <div className="space-y-2">
            {starters.map((s) => (
              <button
                key={s.id}
                onClick={() => setStarter(s.id)}
                className={`w-full rounded-xl border p-3.5 text-left transition ${
                  starter === s.id
                    ? "border-[var(--accent)] bg-[var(--accent)]/10 ring-2 ring-[var(--accent)]/20"
                    : "border-[var(--panel-border)] hover:border-white/20"
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">{s.name}</span>
                  {starter === s.id && (
                    <span className="text-xs font-medium text-[var(--accent)]">✓ selected</span>
                  )}
                </div>
                <p className="mt-0.5 text-xs text-[var(--muted)]">{s.description}</p>
                {s.tags.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-1">
                    {s.tags.map((t) => (
                      <span
                        key={t}
                        className="chip px-2 py-0.5 text-[10px] text-[var(--muted)]"
                      >
                        {t}
                      </span>
                    ))}
                  </div>
                )}
              </button>
            ))}
          </div>

          {error && (
            <p className="mt-3 rounded-lg border border-[var(--red)]/30 bg-[var(--red)]/10 px-3 py-2 text-xs text-[var(--red)]">
              {error}
            </p>
          )}

          <button
            onClick={create}
            disabled={busy || !name.trim()}
            className="btn-primary mt-4 inline-flex w-full items-center justify-center gap-2 py-2.5 text-sm"
          >
            {busy ? (
              <>
                <span className="spin-slow h-3.5 w-3.5 rounded-full border-2 border-white/70 border-t-transparent" />
                Creating…
              </>
            ) : (
              "Create & open →"
            )}
          </button>
        </section>

        {/* Open Existing */}
        <section className="glass rise p-6" style={{ animationDelay: "0.06s" }}>
          <div className="mb-4 flex items-center gap-2">
            <span className="h-3 w-1 rounded-full bg-[var(--accent-3)]" />
            <h2 className="label">Open existing</h2>
          </div>
          {projects.length === 0 ? (
            <div className="flex h-40 items-center justify-center rounded-xl border border-dashed border-[var(--panel-border)] text-center text-sm text-[var(--faint)]">
              No projects yet —<br />create your first one on the left.
            </div>
          ) : (
            <ul className="space-y-2">
              {projects.map((p) => (
                <li key={p.id}>
                  <button
                    onClick={() => open(p)}
                    className="group w-full rounded-xl border border-[var(--panel-border)] p-3.5 text-left transition hover:border-white/20 hover:bg-white/[0.02]"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium">{p.name}</span>
                      <span className="flex items-center gap-2">
                        {p.starter && (
                          <span className="chip px-2 py-0.5 text-[10px] text-[var(--muted)]">
                            {p.starter}
                          </span>
                        )}
                        <span className="text-[var(--faint)] transition group-hover:translate-x-0.5 group-hover:text-[var(--foreground)]">
                          →
                        </span>
                      </span>
                    </div>
                    {p.description && (
                      <p className="mt-0.5 text-xs text-[var(--muted)]">{p.description}</p>
                    )}
                  </button>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>
    </main>
  );
}
