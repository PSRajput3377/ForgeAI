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
`FilesystemTool` (path-escape protected). Terminal/Docker (Phase 8), Git
(Phase 9), Search, and Database tools plug into the same interface.

## LangGraph workflow

`packages/agents/workflow.py` builds the graph: a node per step, a conditional
edge after **review** that branches to **reflection** (retry) or **git**
(finish), and a `reflection → coder` retry loop bounded by `max_retries`. The
whole thing is `compile()`d and run with `run_workflow(router, request)`.

## Phase 2 status

Every agent is a **runnable skeleton**: real role, prompt, router wiring, and
structured I/O, with deterministic placeholder logic where full LLM
intelligence lands later. The graph executes end-to-end (verified by the test
suite, including the reflection loop). Real intelligence, tools, memory, and
sandboxing arrive in Phases 4–9.
