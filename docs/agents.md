# Agents — AI Engine Architecture

ForgeAI is an **AI organization**: a Manager that delegates to specialist
agents, orchestrated by an explicit LangGraph workflow over one shared state
object. No agent calls another directly — the graph is the only thing that
sequences them. This keeps the system modular, loosely coupled, and testable
(ADR-0001/0002).

## High-level flow

```
                         User
                          │
                          ▼
                    Manager (intake)
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
       Planner        Researcher        Memory
                          │
                          ▼
                        Coder
                          │
                          ▼
                      Execution
                          │
                          ▼
                       Testing
                          │
                          ▼
                        Review
                          │
                 needs reflection?
                   │yes        │no
                   ▼           ▼
              Reflection      Git
                   │           │
              (retry Coder)    ▼
                          Manager (final) → Result
```

## The roster

| Agent          | Responsibility                                              | Writes code? |
|----------------|-------------------------------------------------------------|--------------|
| **Manager**    | Interpret request, delegate, monitor, produce final response | ❌ never     |
| **Planner**    | Break request into executable tasks                          | ❌           |
| **Researcher** | Gather only relevant context (README, docs, code)            | ❌           |
| **Memory**     | Surface short-term + long-term context                       | ❌           |
| **Coder**      | Write code from task + context (never guesses)               | ✅           |
| **Execution**  | Run install/build/test commands, collect logs (Phase 8: Docker) | —         |
| **Testing**    | Run tests, validate outputs, report pass/fail                | —            |
| **Review**     | Senior review: performance, security, readability, etc.      | ❌           |
| **Reflection** | Read failures, diagnose, propose a fix, retry (self-correct) | ❌           |
| **Git**        | Stage, commit, (Phase 9) open PRs                            | —            |

## Why a Manager (no agent-to-agent chatter)

Eight agents talking directly to each other is N² chaos. Routing everything
through the Manager (and expressing order in the graph) gives one place to
monitor progress, handle failures, and retry — exactly how a tech lead works.

## Shared state — `ProjectState`

Every agent reads from and writes to one object instead of passing dozens of
variables around (`packages/core/state.py`):

```
ProjectState
├── user_request
├── tasks / current_task
├── project_context / retrieved_docs
├── generated_code
├── execution_logs / test_passed
├── review_feedback / review_verdict
├── retry_count / max_retries / needs_reflection
├── messages          (structured audit trail)
└── final_response
```

## Structured communication

Agents never exchange raw prompts. The Planner emits `TaskSpec` objects and
each agent returns an `AgentMessage` envelope (`packages/core/messages.py`):

```jsonc
// TaskSpec
{ "task_id": "...", "title": "Create Login API", "priority": "high", "status": "pending" }

// AgentMessage (returned to the Manager)
{ "task_id": "...", "sender": "coder", "status": "completed",
  "files_changed": ["auth.py", "routes.py"] }
```

## Model Provider Layer (Model Router)

Agents depend only on `ModelRouter.complete_for(role, messages)`
(`packages/models`). The router maps each role to a configured model and
forwards to a provider:

```
Agent → ModelRouter → LLMProvider
                       ├── OllamaProvider  (default; qwen3/deepseek/llama)
                       └── EchoProvider     (offline, deterministic — tests)
```

Swapping in OpenAI/Claude/Gemini later = add a provider class. No agent code
changes (ADR-0003). The `EchoProvider` lets the **entire graph run in tests
without a live LLM or pulled models**.

## Tool abstraction

Agents never touch the machine directly; they invoke tools that return a
uniform `ToolResult` (`packages/tools`). Phase 2 ships a sandboxed
`FilesystemTool` (path-escape protected). Terminal/Docker, Git, Search, and
Database tools plug into the same interface in later phases ([tools.md](tools.md)).

## LangGraph workflow

`packages/agents/workflow.py` builds the graph: a node per step, a conditional
edge after **review** that branches to **reflection** (retry) or **git**
(finish), and a `reflection → coder` retry loop bounded by `max_retries`. The
whole thing is `compile()`d and run with `run_workflow(router, request)`.

## Per-agent contracts

Each agent has a single responsibility and a defined input/output over the
shared state. Formal acceptance criteria live in
[`../specs/agent-spec.md`](../specs/agent-spec.md).

### Manager
- **Purpose:** interpret the request, delegate, monitor, produce the final response.
- **Delegation strategy:** decides which specialists are needed and the order;
  the graph encodes the sequence. Touches state at `intake` and `final` only.
- **Retry logic:** owns `max_retries`; the post-review edge drives reflection.
- **Termination:** stops when Review approves, or retries are exhausted.
- **Writes:** `messages`, `final_response`. **Never writes code or files.**
- **Failure cases:** unclear request → still produces a final response noting it.

### Planner
- **Purpose:** break the request into executable `TaskSpec`s. **Never codes.**
- **Inputs:** `user_request`. **Outputs:** `tasks`, `current_task`.
- **Failure cases:** vague request → coarse tasks (refined as research lands).
- **Future:** parse model output into structured tasks with dependencies.

### Researcher
- **Purpose:** gather only task-relevant context. Reads README/docs/source.
  **Never writes code.**
- **Inputs:** `user_request`, `project_context`. **Outputs:** `retrieved_docs`.
- **Future:** browser, GitHub, official docs (post-MVP).

### Memory
- **Purpose:** surface short-term (task/files/errors) and long-term (style, past
  decisions, frameworks) context.
- **Inputs:** `user_request`, `project_id`. **Outputs:** `project_context`.
- **Implementation:** when given a `ContextBuilder` (Phase 4), it assembles
  scored memories (session/project/user) + semantic RAG hits and writes them
  into `state.project_context`; otherwise it falls back to lightweight behavior.
  See [memory.md](memory.md). PostgreSQL-backed durable memory lands in the
  Database phase behind the same interface.

### Coder
- **Purpose:** write code from task + context. **Never guesses; never executes
  commands; never pushes git.**
- **Inputs:** `current_task`, `retrieved_docs`, `review_feedback`.
- **Outputs:** `generated_code` (path → content).
- **Failure cases:** missing context → relies on Research/Memory rather than
  inventing.

### Execution
- **Purpose:** run install/build/test commands, collect logs/exit codes.
  Runs **only inside Docker**.
- **Inputs:** `generated_code`, `project_path`. **Outputs:** `execution_logs`,
  `test_passed`.
- **Implementation:** when wired with an `engine_factory` (Phase 5), it drives
  the `ExecutionEngine` — running the project's profile in an isolated sandbox
  with the self-correcting retry loop — and sets `test_passed` from the
  `RunRecord`. Otherwise it simulates. See [execution.md](execution.md).

### Testing
- **Purpose:** run tests, validate outputs, report pass/fail with evidence.
- **Inputs:** `execution_logs`, code. **Outputs:** `test_passed`, logs.

### Review
- **Purpose:** senior review — performance, security, readability, architecture,
  naming, code smells. **Never writes code.**
- **Inputs:** `generated_code`, `test_passed`.
- **Outputs:** `review_verdict` (approved / changes_requested), `review_feedback`.

### Reflection
- **Purpose:** self-correction — read failures, diagnose, propose a fix, retry.
- **Inputs:** `execution_logs`, `review_feedback`.
- **Outputs:** bumps `retry_count`, sets `review_feedback` (the fix), resets
  `test_passed`; routes back to Coder. Bounded by `max_retries`.

### Git
- **Purpose:** stage, commit, (later) open PRs.
- **Inputs:** `generated_code`, `user_request`. **Outputs:** commit message.
- **Future:** real git ops + PR creation via the Git tool.

## Status

Every agent is a **runnable skeleton**: real role, prompt, router wiring, and
structured I/O, with deterministic placeholder logic where full LLM
intelligence lands later. The graph executes end-to-end (verified by the test
suite, including the reflection loop). Real intelligence, tools, memory, and
sandboxing arrive in later phases ([roadmap.md](roadmap.md)).
