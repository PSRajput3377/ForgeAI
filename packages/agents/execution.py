"""ExecutionAgent — runs the project's build/test profile in a sandbox.

When wired with an ExecutionEngine factory (Phase 5), it runs the real
build→test loop in an isolated sandbox, records the RunRecord, and sets
``test_passed`` from the outcome. Without one, it falls back to the Phase 2
simulation so the offline default workflow still runs.

The engine's self-correcting retry loop is driven by a *fixer* the agent
supplies; here the fix is recorded as feedback the Reflection/Coder agents act
on, keeping the agent layer and the engine decoupled.
"""

from __future__ import annotations

from core.messages import AgentMessage, MessageStatus
from core.roles import AgentRole
from core.state import ProjectState

from agents.base import BaseAgent


class ExecutionAgent(BaseAgent):
    role = AgentRole.EXECUTION

    def __init__(self, router, engine_factory=None):
        super().__init__(router)
        # engine_factory(state) -> ExecutionEngine, or None for simulation.
        self.engine_factory = engine_factory

    async def run(self, state: ProjectState) -> ProjectState:
        if self.engine_factory is not None:
            engine = self.engine_factory(state)
            record = await engine.execute(task=state.user_request, project=state.project_id or "")
            for r in record.results:
                state.execution_logs.append(
                    f"[execution] $ {r.command} -> exit {r.exit_code}"
                    + (f" ({r.stderr.strip()[:120]})" if not r.success else "")
                )
            state.test_passed = record.success
            status = MessageStatus.COMPLETED if record.success else MessageStatus.FAILED
            summary = (
                f"Ran {len(record.results)} step(s), "
                f"{'passed' if record.success else 'failed'} after {record.retries} retr(y/ies)"
            )
            payload = {"success": record.success, "retries": record.retries}
        else:
            state.execution_logs.append("[execution] simulated build: exit 0")
            status = MessageStatus.COMPLETED
            summary = "Executed build (simulated)"
            payload = {"exit_code": 0}

        task_id = state.current_task.task_id if state.current_task else "n/a"
        state.record(
            AgentMessage(
                task_id=task_id,
                sender=self.role,
                status=status,
                summary=summary,
                payload=payload,
            )
        )
        return state
