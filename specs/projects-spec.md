# Projects & First-Run Specification (Phase 13)

How ForgeAI becomes a **usable product**, not just an engine: a first-class
**Project** that owns a workspace on disk, the ability to **bootstrap a new
project from nothing**, and an onboarding flow that delivers a working result in
the first minute.

> `docs/` explains **how** ForgeAI works today.
> `specs/` defines **what** each component must do. (ADR-0013)

## Why this phase exists

The engine (Phases 0–12) is ahead of the product. Today a user types "Add JWT
authentication" and the honest next question is *"to which project?"* — there is
no first-class Project that owns files, no way to start from nothing, and no
sub-minute "it worked" moment. This phase closes that gap. The **root cause of
several symptoms is one missing primitive: a Project that owns a real workspace
directory.** Fix that and "to which project?", project bootstrap, and the wow
moment all resolve together.

## Scope decision

A **Project owns a local directory on the API host** (under a configurable
workspaces root). Bootstrap scaffolds files into that directory; the agent
pipeline reads and writes it via the existing workspace-scoped tools
(`build_default_registry(root)`). The `Project` model MUST be shaped so a
**git-backed mode can slot in later** behind the same interface (a nullable
`repo` field), without changing agents or the workflow — the same
provider-abstraction discipline used elsewhere.

---

## Component contracts

### 1. Project as a first-class object

- A `Project` MUST own a workspace **path** on disk: `<WORKSPACES_ROOT>/<id>`,
  created when the project is created and removed when it is deleted.
- The existing `Project` table (Phase 7: id, workspace_id, name, description)
  MUST be extended with `path` and a nullable `repo` (for the future git mode).
  It MUST stay within the existing Organization → Workspace → Project tenancy.
- CRUD endpoints MUST exist: create, list (scoped to the caller's workspace),
  get, delete. They MUST enforce the existing RBAC/workspace isolation
  (auth-spec) — a user only sees their workspace's projects.
- The workspace root MUST be configurable (`WORKSPACES_ROOT`) and MUST default
  to a path that works in the Docker container and on the host.
- Path handling MUST prevent traversal: a project's effective root is fixed to
  its own directory; no request may read/write outside it (reuses the
  filesystem tool's existing root-confinement).

### 2. `/agents/run` binds to a real project

- `/agents/run` MUST accept a `project_id` that resolves to a real `Project`,
  and MUST run the workflow against that project's `path` (its tools are scoped
  to that root).
- An unknown `project_id` MUST return 404 — not silently run against nothing.
- For backward compatibility / tests, a run MAY still accept an explicit
  `project_path`, but the project-bound path MUST take precedence when both are
  given.
- Generated files MUST be written into the project directory (not an
  in-memory-only `generated_code` map), so the result is a real, inspectable
  project on disk.

### 3. Project bootstrap (scaffold from nothing)

- The platform MUST support creating a project from a **starter template** —
  e.g. "FastAPI SaaS starter with JWT, PostgreSQL, Docker, and tests."
- A starter MUST be a deterministic, versioned set of files (no model required
  to scaffold), so bootstrap is instant and reproducible and works offline.
- At least these starters MUST exist initially: an empty project, and one
  non-trivial backend starter (FastAPI). More MAY be added behind the same
  interface.
- After scaffolding, bootstrap MUST hand the project to the normal agent
  pipeline so the team can immediately extend it.
- Bootstrap MUST be idempotent-safe: scaffolding into a non-empty project MUST
  be refused or explicitly confirmed, never silently overwrite.

### 4. Onboarding / first-run flow (UI)

- The first screen a signed-in user sees MUST be a **project chooser**: *Create
  New Project* or *Open Existing*, not the bare workspace.
- *Create New* MUST offer the starter templates (incl. "empty") and create the
  project + workspace dir in one step.
- Opening a project MUST land the user in the workspace **bound to that
  project**, with the task input ready.
- The flow MUST make the path from "nothing" to "a running project" obvious
  without the user needing to understand the architecture first.

### 5. The first-minute result ("wow")

- From a fresh account, a user MUST be able to: choose a starter → watch the
  team scaffold and build it live → end with a working project — without editing
  config or reading docs.
- The live timeline/agents/metrics MUST reflect this run (already wired via the
  observability WebSocket).
- This MUST work offline with `MODEL_PROVIDER=echo` (deterministic, instant) so
  the experience is demoable on any hardware; real models deepen it but are not
  required for the first-run path.

### 6. Integration honesty (transparency)

- Integrations that are interface-complete but validated only against fakes
  MUST be **clearly labelled** as such in the UI and docs (e.g. a "simulated"
  vs "live" badge), so capability is never overstated.
- The GitHub provider's `mode` (`fake` | `live`) MUST be surfaced where it's
  relevant to the user.

---

## New / changed persistence

| Table | Change |
|-------|--------|
| `projects` | add `path` (str, the workspace dir) and `repo` (nullable str, future git mode) |

No new tables required for the local-dir model; bootstrap starters are files in
the repo, not DB rows.

## A change MUST NOT

- Run the agent pipeline against a `project_id` that resolves to no real
  project (must 404).
- Read or write outside a project's own workspace directory (path traversal).
- Let bootstrap silently overwrite an existing non-empty project.
- Overstate an integration's readiness — fake-validated integrations MUST be
  labelled.
- Break the offline-first guarantee: the first-run path MUST work with the echo
  provider and in-memory/SQLite stores.

## Acceptance criteria

- [ ] A `Project` owns a real workspace directory; CRUD endpoints exist and
      enforce workspace isolation.
- [ ] `/agents/run` binds to a real `project_id`, runs against its path, writes
      files there, and 404s on an unknown id.
- [ ] At least two starters exist (empty + FastAPI); bootstrap scaffolds
      deterministically and offline, then hands off to the pipeline.
- [ ] The UI opens on a project chooser (Create New / Open Existing) and binds
      the workspace to the chosen project.
- [ ] A fresh user can go from sign-in to a working project in the first minute
      with `MODEL_PROVIDER=echo`.
- [ ] Fake-validated integrations are labelled in the UI/docs.
- [ ] Offline suite green; ruff + black clean; docs + an ADR updated.
