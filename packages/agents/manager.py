"""ManagerAgent — the orchestrator. Delegates; never writes code.

The Manager owns intake (interpreting the request) and the final response. The
*sequencing* of specialists is expressed declaratively by the LangGraph
workflow (``agents.workflow``); the Manager produces the user-facing summary
from the completed shared state.
"""

from __future__ import annotations

from core.messages import AgentMessage, MessageStatus
from core.roles import AgentRole
from core.state import ProjectState, ReviewVerdict

from agents.base import BaseAgent


class ManagerAgent(BaseAgent):
    role = AgentRole.MANAGER

    async def intake(self, state: ProjectState) -> ProjectState:
        """Acknowledge and record the incoming request at the start of a run."""
        state.record(
            AgentMessage(
                task_id="intake",
                sender=self.role,
                status=MessageStatus.IN_PROGRESS,
                summary=f"Received request: {state.user_request[:80]}",
            )
        )
        return state

    async def run(self, state: ProjectState) -> ProjectState:
        """Produce the final response from the completed state."""
        approved = state.review_verdict == ReviewVerdict.APPROVED
        if approved:
            verdict = "completed successfully"
        elif state.retry_count >= state.max_retries:
            verdict = f"stopped after {state.retry_count} retries (review not approved)"
        else:
            verdict = "ended in an unexpected state"

        state.final_response = (
            f"Request '{state.user_request}' {verdict}. "
            f"{len(state.tasks)} tasks planned, "
            f"{len(state.generated_code)} file(s) generated, "
            f"review={state.review_verdict.value}."
        )
        state.record(
            AgentMessage(
                task_id="final",
                sender=self.role,
                status=MessageStatus.COMPLETED if approved else MessageStatus.FAILED,
                summary="Produced final response",
            )
        )
        return state
