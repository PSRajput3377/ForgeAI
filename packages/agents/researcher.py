"""ResearcherAgent — gathers only the context relevant to the task."""

from __future__ import annotations

from core.messages import AgentMessage, MessageStatus
from core.roles import AgentRole
from core.state import ProjectState

from agents.base import BaseAgent


class ResearcherAgent(BaseAgent):
    role = AgentRole.RESEARCHER

    async def run(self, state: ProjectState) -> ProjectState:
        context = await self._ask(
            f"Find context relevant to: {state.user_request}\n"
            f"Known project context:\n{state.project_context or '(none yet)'}"
        )
        state.retrieved_docs.append(context)
        task_id = state.current_task.task_id if state.current_task else "n/a"
        state.record(
            AgentMessage(
                task_id=task_id,
                sender=self.role,
                status=MessageStatus.COMPLETED,
                summary="Gathered relevant context",
            )
        )
        return state
