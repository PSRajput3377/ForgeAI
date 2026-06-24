# Tool Specification

The contract **every** tool must satisfy. Catalog and narrative in
[`../docs/tools.md`](../docs/tools.md).

## Interface

- A tool MUST subclass `Tool` and define a unique `name`.
- A tool MUST implement `run(**kwargs) -> ToolResult`.
- A tool MUST return a `ToolResult` for **expected** failures (set `ok=False`,
  populate `error`) rather than raising.
- A tool MAY raise only for programmer errors (never for user/agent input).

## Behavior & safety

- A tool MUST declare and stay within its permission scope.
- A tool that touches the filesystem MUST confine all paths to a project `root`
  and reject path escapes (`../`, absolute paths outside root).
- A tool that executes commands MUST run inside the Docker sandbox, MUST enforce
  a timeout, and MUST capture stdout, stderr, and exit code.
- A tool MUST NOT perform destructive actions outside its declared scope. File
  **delete/rename** MUST NOT be exposed in the MVP.
- A tool SHOULD be deterministic given the same inputs and environment.

## Documentation

- Every tool MUST document its **inputs, outputs, errors, and permissions** in
  `docs/tools.md`.

## Acceptance criteria

- [ ] Unique `name`; subclasses `Tool`.
- [ ] Returns `ToolResult`; no exceptions on expected failures.
- [ ] Enforces its scope (path confinement / sandbox / timeout as applicable).
- [ ] Has tests for each action **and** its error/permission paths
      (e.g. `test_path_escape_is_blocked`).
- [ ] Documented in `docs/tools.md`.
