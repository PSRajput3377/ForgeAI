# Evaluation Specification

How we measure **quality** — distinct from the functional test suite
([`../docs/testing.md`](../docs/testing.md)), which verifies plumbing offline.
Evaluation answers: *do the agents produce good results with real models?*

## What we evaluate

| Dimension        | Question                                              |
|------------------|------------------------------------------------------|
| Task success     | Did the run achieve the requested outcome?           |
| Code correctness | Does the generated code build and pass its tests?    |
| Plan quality     | Are the Planner's tasks complete and well-ordered?   |
| Review accuracy  | Does Review catch real issues without false alarms?  |
| Self-correction  | Does Reflection fix failures within `max_retries`?   |
| Efficiency       | Tokens / wall-clock / retries per successful task.   |

## Method

- **Eval set:** a versioned suite of representative requests (e.g. "add JWT
  auth", "fix failing test", "add a CRUD endpoint") with expected outcomes.
- **Harness:** run each request through the real workflow (Ollama-backed),
  capture the final state + `messages` trail.
- **Scoring:** automated where possible (build/test pass, retries used);
  rubric-based human or LLM-judge scoring for plan/review quality.
- **Tracing:** Langfuse captures per-agent calls for inspection (planned).

## Metrics & targets (initial)

- Task success rate ≥ baseline, tracked per model.
- Mean retries per successful task: lower is better.
- Review precision/recall on a labeled set of seeded defects.

## A change MUST NOT

- Be considered "done" on quality grounds without an eval run when it touches
  prompts, the workflow graph, or model routing.

## Acceptance criteria

- [ ] An eval set exists and is versioned.
- [ ] Each eval case has an expected outcome / rubric.
- [ ] Results are recorded per model and comparable across runs.
- [ ] Prompt/workflow/model changes report their eval impact.
