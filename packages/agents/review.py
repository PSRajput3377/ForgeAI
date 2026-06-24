"""ReviewAgent — senior-engineer review. Approves or requests changes."""

from __future__ import annotations

from core.messages import AgentMessage, MessageStatus
from core.roles import AgentRole
from core.state import ProjectState, ReviewVerdict

from agents.base import BaseAgent


class ReviewAgent(BaseAgent):
    role = AgentRole.REVIEW

    async def run(self, state: ProjectState) -> ProjectState:
        # Review depends on tests: failing tests => changes requested, which
        # drives the reflection loop. Passing tests => approved.
        if state.test_passed:
            state.review_verdict = ReviewVerdict.APPROVED
            state.review_feedback = ""
            state.needs_reflection = False
            status = MessageStatus.COMPLETED
        else:
            state.review_verdict = ReviewVerdict.CHANGES_REQUESTED
            state.review_feedback = "Tests failed; fix the failing build before re-review."
            state.needs_reflection = True
            status = MessageStatus.FAILED

        task_id = state.current_task.task_id if state.current_task else "n/a"
        state.record(
            AgentMessage(
                task_id=task_id,
                sender=self.role,
                status=status,
                summary=f"Review verdict: {state.review_verdict.value}",
            )
        )
        return state
