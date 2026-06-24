# State Specification — `ProjectState`

Field rules and invariants. The field reference and read/write matrix are in
[`../docs/state.md`](../docs/state.md). Source: `packages/core/state.py`.

## Invariants

- There MUST be exactly **one** `ProjectState` instance per workflow run; it is
  threaded through every node.
- `messages` MUST be **append-only**. Agents add via `state.record()`; nothing
  removes or rewrites entries. It is the authoritative audit trail.
- List fields (`tasks`, `retrieved_docs`, `execution_logs`) SHOULD be appended
  to, not overwritten, to preserve history within a run.
- Control fields (`review_verdict`, `retry_count`, `max_retries`) MUST be the
  **only** inputs to the post-review routing edge — routing MUST NOT depend on
  an agent calling another agent.
- `retry_count` MUST be non-negative and MUST NOT exceed `max_retries` as a loop
  bound (the edge stops reflecting at the limit).
- `final_response` MUST be set by the Manager before the run reaches `END`.

## Field ownership

- Each field has a defined writer set (see the matrix in `docs/state.md`). An
  agent MUST NOT write fields outside its role (e.g. Planner MUST NOT write
  `generated_code`).
- `test_passed` MUST be reset to `None` by Reflection so a retry is evaluated
  fresh.

## Serialization

- `ProjectState` MUST be a Pydantic model (serializable to/from JSON) so runs
  can be persisted, resumed, and inspected.

## Acceptance criteria

- [ ] All fields typed and defaulted; model validates round-trip to JSON.
- [ ] `record()` only appends to `messages`.
- [ ] Workflow routing reads only control fields.
- [ ] Reflection bumps `retry_count` and resets `test_passed`.
- [ ] A run always ends with a non-empty `final_response`.
