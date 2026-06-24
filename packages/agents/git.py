"""GitAgent — stages, commits, and (later) opens PRs.

Phase 2 skeleton produces a commit message only. Real git operations land in
Phase 9 (GitHub Integration) via the Git tool.
"""

from __future__ import annotations

from core.messages import AgentMessage, MessageStatus
from core.roles import AgentRole
from core.state import ProjectState

from agents.base import BaseAgent


class GitAgent(BaseAgent):
    role = AgentRole.GIT

    async def run(self, state: ProjectState) -> ProjectState:
        message = await self._ask(
            f"Write a conventional-commit message for: {state.user_request}"
        )
        task_id = state.current_task.task_id if state.current_task else "n/a"
        state.record(
            AgentMessage(
                task_id=task_id,
                sender=self.role,
                status=MessageStatus.COMPLETED,
                summary="Prepared commit (not yet pushed)",
                payload={"commit_message": message[:120]},
            )
        )
        return state
