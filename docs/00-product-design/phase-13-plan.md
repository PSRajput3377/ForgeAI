# Phase 13 — Projects & First-Run Experience

Spec: [`specs/projects-spec.md`](../../specs/projects-spec.md).

Phase 12 made ForgeAI a research-grade *engine*. Phase 13 makes it a *product*:
a first-class Project that owns a workspace, bootstrap-from-nothing, and an
onboarding flow that produces a working result in the first minute.

This addresses a direct, fair critique: the backend is ahead of the UX. The root
cause of several symptoms — "to which project?", no bootstrap, no sub-minute wow
— is one missing primitive: **a Project that owns a real workspace directory.**
Build that, and the rest follows.

## Scope

A **Project owns a local directory** on the API host (`<WORKSPACES_ROOT>/<id>`).
The model carries a nullable `repo` so a **git-backed mode slots in later**
behind the same interface, with no agent/graph change. Same spec-first,
offline-testable discipline as Phase 12.

## Sub-phase sequence

| Sub | Name | Builds | Closes |
|-----|------|--------|--------|
| **13.1** | **Project object + workspace dir** | `path`/`repo` on the `Project` model; a `ProjectService` that creates/removes the dir; CRUD endpoints with workspace isolation | "to which project?" |
| **13.2** | **Run binds to a project** | `/agents/run` resolves `project_id` → path, scopes the tools to it, writes generated files there, 404s on unknown id | wires engine ↔ project |
| **13.3** | **Project bootstrap** | versioned starter templates (empty + FastAPI SaaS w/ JWT+Postgres+Docker+tests); deterministic scaffold → hand off to the pipeline | bootstrap-from-nothing |
| **13.4** | **Onboarding flow (UI)** | Welcome → Create New / Open Existing → project picker; workspace bound to the chosen project | first-run UX |
| **13.5** | **The first-minute wow** | starter → watch the team scaffold + build live → working project; works offline (`MODEL_PROVIDER=echo`) | the magic moment |
| **13.6** | **Integration honesty pass** | label fake-validated vs. live integrations in UI + docs; surface GitHub `mode` | transparency |

**Recommended stop line for "usable product":** through **13.5**. 13.6 is a
small, independent transparency pass.

## Why this order

- **13.1 first** — every later piece needs a Project that owns a path.
- **13.2 before 13.3** — bootstrap scaffolds *into* a project, so the bind must
  exist first.
- **13.3 before 13.4/13.5** — the UI chooser offers starters, and the wow moment
  *is* a bootstrap run, so scaffolding must work first.
- **13.6 last** — independent; can ship anytime.

## Guardrails (from the spec)

- Offline-first: the whole first-run path works with `MODEL_PROVIDER=echo` and
  SQLite — demoable on any hardware.
- Path confinement: a run can never read/write outside its project's directory
  (reuses the filesystem tool's root-confinement).
- No silent overwrite: bootstrap refuses a non-empty target unless confirmed.
- Tenancy preserved: projects live within the existing Org → Workspace →
  Project model and RBAC (auth-spec).
- Honesty: fake-validated integrations are labelled, never overstated.

## Per-sub-phase definition of done

1. Spec acceptance criteria for that component met.
2. Offline tests cover it (deterministic, no network).
3. `ruff check` + `black --check` clean; frontend builds.
4. Docs updated (+ an ADR for the Project/workspace-dir design in 13.1).
5. Committed and pushed.
