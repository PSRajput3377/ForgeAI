"""ReviewAgent — senior-engineer review. Approves or requests changes.

Failing tests always block (driving the reflection loop). When tests pass and a
real model is configured, the agent additionally performs a genuine code review
of the generated files and can request changes with concrete feedback; with the
offline EchoProvider that review is skipped (unparseable response), so passing
tests approve exactly as before.
"""

from __future__ import annotations

from core.messages import AgentMessage, MessageStatus
from core.roles import AgentRole
from core.state import ProjectState, ReviewVerdict

from agents.base import BaseAgent

# Don't keep requesting changes forever — once we've spent the retry budget,
# stop second-guessing the model so the run can terminate.
_REVIEW_RETRY_BUDGET = 1


class ReviewAgent(BaseAgent):
    role = AgentRole.REVIEW

    async def run(self, state: ProjectState) -> ProjectState:
        if not state.test_passed:
            # Failing tests => changes requested, which drives the reflection loop.
            return self._record(
                state,
                ReviewVerdict.CHANGES_REQUESTED,
                "Tests failed; fix the failing build before re-review.",
                MessageStatus.FAILED,
            )

        # Tests pass. Optionally do a real review of the generated code. Only
        # while we still have retry budget, so we can't loop indefinitely.
        if state.retry_count < _REVIEW_RETRY_BUDGET:
            verdict = await self._review_code(state)
            if verdict is not None and not verdict.get("approved", True):
                issues = verdict.get("issues") or verdict.get("feedback") or "Changes requested."
                if isinstance(issues, list):
                    issues = "; ".join(str(i) for i in issues)
                return self._record(
                    state,
                    ReviewVerdict.CHANGES_REQUESTED,
                    str(issues)[:500],
                    MessageStatus.FAILED,
                )

        return self._record(state, ReviewVerdict.APPROVED, "", MessageStatus.COMPLETED)

    async def _review_code(self, state: ProjectState) -> dict | None:
        """Ask the model to review the generated files. None when unavailable."""
        if not state.generated_code:
            return None
        # Only meaningful when the Coder produced real files (not the offline
        # placeholder). Skip the single-file echo placeholder.
        if set(state.generated_code) == {"generated/output.txt"}:
            return None

        listing = "\n\n".join(
            f"--- {path} ---\n{content[:4000]}" for path, content in state.generated_code.items()
        )
        prompt = (
            "Review the following generated project for correctness, missing "
            "files, and obvious bugs. Respond with JSON: "
            '{"approved": true|false, "issues": ["..."]}. Approve unless there '
            "is a concrete, fixable problem.\n\n"
            f"Request: {state.user_request}\n\nFiles:\n{listing}"
        )
        result = await self._ask_json(prompt)
        return result if isinstance(result, dict) else None

    def _record(
        self,
        state: ProjectState,
        verdict: ReviewVerdict,
        feedback: str,
        status: MessageStatus,
    ) -> ProjectState:
        state.review_verdict = verdict
        state.review_feedback = feedback
        state.needs_reflection = verdict == ReviewVerdict.CHANGES_REQUESTED
        task_id = state.current_task.task_id if state.current_task else "n/a"
        state.record(
            AgentMessage(
                task_id=task_id,
                sender=self.role,
                status=status,
                summary=f"Review verdict: {verdict.value}",
            )
        )
        return state
