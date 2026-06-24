"""TestingAgent — runs tests and reports pass/fail with evidence.

Phase 2 skeleton sets a deterministic pass. Phase 8 runs real test suites in
the sandbox; integration/E2E (Playwright) come later.
"""

from __future__ import annotations

from core.messages import AgentMessage, MessageStatus
from core.roles import AgentRole
from core.state import ProjectState

from agents.base import BaseAgent


class TestingAgent(BaseAgent):
    role = AgentRole.TESTING

    async def run(self, state: ProjectState) -> ProjectState:
        # Placeholder: tests pass unless a prior execution log signals failure.
        failed = any("exit 1" in log for log in state.execution_logs)
        state.test_passed = not failed
        state.execution_logs.append(
            "[testing] tests passed" if state.test_passed else "[testing] tests FAILED"
        )
        task_id = state.current_task.task_id if state.current_task else "n/a"
        state.record(
            AgentMessage(
                task_id=task_id,
                sender=self.role,
                status=(
                    MessageStatus.COMPLETED
                    if state.test_passed
                    else MessageStatus.FAILED
                ),
                summary="Ran tests",
                payload={"passed": state.test_passed},
            )
        )
        return state
