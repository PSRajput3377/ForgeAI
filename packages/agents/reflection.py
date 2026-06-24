"""ReflectionAgent — self-correction. Reads failures, proposes a fix, retries.

Inspired by research on self-correcting agents. It increments the retry counter
and writes actionable feedback that the Coder consumes on the next pass.

Phase 12.4: when a ``FailureStore`` is provided, Reflection consults the
knowledge base by error signature *before* asking the model — on a hit with a
known-good fix it reuses it ("fix instantly") instead of re-diagnosing, and it
stores every episode so the KB grows. Without a store it behaves exactly as
before (offline default unchanged).
"""

from __future__ import annotations

from core.messages import AgentMessage, MessageStatus
from core.roles import AgentRole
from core.state import ProjectState
from models.router import ModelRouter

from agents.base import BaseAgent


class ReflectionAgent(BaseAgent):
    role = AgentRole.REFLECTION

    def __init__(self, router: ModelRouter, *, failure_store=None):
        super().__init__(router)
        self.failure_store = failure_store

    async def run(self, state: ProjectState) -> ProjectState:
        state.retry_count += 1
        recent_logs = "\n".join(state.execution_logs[-5:])
        error_text = f"{recent_logs}\n{state.review_feedback}".strip()

        recalled = self.failure_store.recall(error_text) if self.failure_store else None
        if recalled is not None:
            # Known error: reuse the fix that worked before, no model call.
            fix = recalled.fix
            self.failure_store.record(error_text, fix=fix, cause=recalled.cause)
            state.execution_logs.append(
                f"[reflection] reused known fix for '{recalled.signature}' "
                f"(attempt {state.retry_count})"
            )
        else:
            fix = await self._ask(
                f"The work failed. Logs:\n{recent_logs}\n"
                f"Review feedback: {state.review_feedback}\n"
                "Diagnose the root cause and propose a concrete fix."
            )
            if self.failure_store is not None:
                self.failure_store.record(error_text, fix=fix[:500])
            state.execution_logs.append(f"[reflection] proposed fix (attempt {state.retry_count})")

        # Clear the failure signal so the retried run can succeed, and hand the
        # fix to the Coder via review_feedback.
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
