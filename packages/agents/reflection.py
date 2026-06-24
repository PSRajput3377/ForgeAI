"""ReflectionAgent — self-correction. Reads failures, proposes a fix, retries.

Inspired by research on self-correcting agents. It increments the retry counter
and writes actionable feedback that the Coder consumes on the next pass.
"""

from __future__ import annotations

from core.messages import AgentMessage, MessageStatus
from core.roles import AgentRole
from core.state import ProjectState

from agents.base import BaseAgent


class ReflectionAgent(BaseAgent):
    role = AgentRole.REFLECTION

    async def run(self, state: ProjectState) -> ProjectState:
        state.retry_count += 1
        recent_logs = "\n".join(state.execution_logs[-5:])
        fix = await self._ask(
            f"The work failed. Logs:\n{recent_logs}\n"
            f"Review feedback: {state.review_feedback}\n"
            "Diagnose the root cause and propose a concrete fix."
        )
        # Clear the failure signal so the retried run can succeed, and hand the
        # fix to the Coder via review_feedback.
        state.execution_logs.append(f"[reflection] proposed fix (attempt {state.retry_count})")
        state.review_feedback = f"reflection-fix: {fix[:120]}"
        state.needs_reflection = False
        state.test_passed = None

        state.record(
            AgentMessage(
                task_id=state.current_task.task_id if state.current_task else "n/a",
                sender=self.role,
                status=MessageStatus.COMPLETED,
                summary=f"Reflection attempt {state.retry_count}",
            )
        )
        return state
