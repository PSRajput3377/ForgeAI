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
      <main className="flex min-h-screen items-center justify-center p-6">
        <p className="text-sm text-neutral-500">Loading your projects…</p>
      </main>
    );
  }

  return (
    <main className="mx-auto min-h-screen max-w-5xl p-6">
      <header className="mb-8">
        <h1 className="text-2xl font-semibold">Your projects</h1>
        <p className="mt-1 text-sm text-neutral-500">
          Open an existing project, or create a new one from a starter and let the agent
          team build it.
        </p>
      </header>

      <div className="grid grid-cols-1 gap-8 lg:grid-cols-2">
        {/* Create New */}
        <section className="rounded-lg border border-neutral-800 p-5">
          <h2 className="mb-3 text-xs uppercase tracking-wide text-neutral-500">
            Create new project
          </h2>
          <label className="mb-3 block">
            <span className="mb-1 block text-xs text-neutral-400">Project name</span>
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="my-saas-app"
              className="w-full rounded-md border border-neutral-700 bg-neutral-900 px-3 py-2 text-sm"
            />
          </label>

          <p className="mb-2 text-xs text-neutral-400">Start from</p>
          <div className="space-y-2">
            {starters.map((s) => (
              <button
                key={s.id}
                onClick={() => setStarter(s.id)}
                className={`w-full rounded-md border p-3 text-left transition ${
                  starter === s.id
                    ? "border-blue-500 bg-blue-950/30"
                    : "border-neutral-800 hover:border-neutral-700"
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">{s.name}</span>
                  {starter === s.id && <span className="text-xs text-blue-400">selected</span>}
                </div>
                <p className="mt-0.5 text-xs text-neutral-500">{s.description}</p>
                {s.tags.length > 0 && (
                  <div className="mt-1.5 flex flex-wrap gap-1">
                    {s.tags.map((t) => (
                      <span
                        key={t}
                        className="rounded bg-neutral-800 px-1.5 py-0.5 text-[10px] text-neutral-400"
                      >
                        {t}
                      </span>
                    ))}
                  </div>
                )}
              </button>
            ))}
          </div>

          {error && <p className="mt-3 text-sm text-red-400">{error}</p>}

          <button
            onClick={create}
            disabled={busy || !name.trim()}
            className="mt-4 w-full rounded-md bg-white py-2 text-sm font-medium text-black transition hover:bg-neutral-200 disabled:cursor-not-allowed disabled:opacity-40"
          >
            {busy ? "Creating…" : "Create & open"}
          </button>
        </section>

        {/* Open Existing */}
        <section className="rounded-lg border border-neutral-800 p-5">
          <h2 className="mb-3 text-xs uppercase tracking-wide text-neutral-500">
            Open existing
          </h2>
          {projects.length === 0 ? (
            <p className="text-sm text-neutral-500">
              No projects yet — create your first one on the left.
            </p>
          ) : (
            <ul className="space-y-2">
              {projects.map((p) => (
                <li key={p.id}>
                  <button
                    onClick={() => open(p)}
                    className="w-full rounded-md border border-neutral-800 p-3 text-left transition hover:border-neutral-600"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium">{p.name}</span>
                      {p.starter && (
                        <span className="text-[10px] text-neutral-500">{p.starter}</span>
                      )}
                    </div>
                    {p.description && (
                      <p className="mt-0.5 text-xs text-neutral-500">{p.description}</p>
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
