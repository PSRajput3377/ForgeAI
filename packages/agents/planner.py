"""PlannerAgent — turns a request into a list of executable tasks. Never codes."""

from __future__ import annotations

from core.messages import AgentMessage, MessageStatus, TaskSpec
from core.roles import AgentRole
from core.state import ProjectState

from agents.base import BaseAgent


class PlannerAgent(BaseAgent):
    role = AgentRole.PLANNER

    async def run(self, state: ProjectState) -> ProjectState:
        # Ask the model for a structured plan. With a real provider this yields
        # task titles tailored to the request; with the offline EchoProvider it
        # returns None and we fall back to the deterministic default plan.
        plan = await self._ask_json(
            "Break the following software request into a short ordered list of "
            "concrete engineering tasks (3-8 items). Respond with JSON of the "
            'form {"tasks": [{"title": "..."}, ...]}.\n\n'
            f"Request:\n{state.user_request}"
        )
        titles = self._titles_from_plan(plan)
        plan_preview = ""
        if titles is None:
            # Offline / unparseable: the deterministic default plan (unchanged).
            titles = [
                "Read project",
                "Inspect backend",
                "Add required dependency",
                "Implement the feature",
                "Run tests",
                "Review",
            ]
        else:
            plan_preview = ", ".join(titles)[:200]

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
                payload={"plan_preview": plan_preview},
            )
        )
        return state

    @staticmethod
    def _titles_from_plan(plan) -> list[str] | None:
        """Extract a clean list of task titles from a parsed plan, or None."""
        if not isinstance(plan, dict):
            return None
        raw = plan.get("tasks")
        if not isinstance(raw, list) or not raw:
            return None
        titles: list[str] = []
        for item in raw:
            if isinstance(item, dict):
                title = item.get("title") or item.get("task") or item.get("name")
            else:
                title = item
            if isinstance(title, str) and title.strip():
                titles.append(title.strip())
        return titles or None
