"""PlannerAgent — turns a request into a list of executable tasks. Never codes."""

from __future__ import annotations

from core.messages import AgentMessage, MessageStatus, TaskSpec
from core.roles import AgentRole
from core.state import ProjectState

from agents.base import BaseAgent


class PlannerAgent(BaseAgent):
    role = AgentRole.PLANNER

    async def run(self, state: ProjectState) -> ProjectState:
        # Ask the model for a plan (recorded for traceability / future parsing).
        plan_text = await self._ask(f"Break this request into tasks:\n{state.user_request}")

        # Phase 2 skeleton: a deterministic default plan mirroring the design.
        # Phase 4 replaces this with structured parsing of ``plan_text``.
        titles = [
            "Read project",
            "Inspect backend",
            "Add required dependency",
            "Implement the feature",
            "Run tests",
            "Review",
        ]
        state.tasks = [
            TaskSpec(title=t, assigned_to=AgentRole.CODER, description=state.user_request)
            for t in titles
        ]
        state.current_task = state.tasks[0]
        state.record(
            AgentMessage(
                task_id=state.current_task.task_id,
                sender=self.role,
                status=MessageStatus.COMPLETED,
                summary=f"Produced {len(state.tasks)} tasks",
                payload={"plan_preview": plan_text[:200]},
            )
        )
        return state
