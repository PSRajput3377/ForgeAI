"""MemoryAgent — surfaces relevant context via the MemoryManager + ContextBuilder.

The agent no longer fabricates context: it asks the ContextBuilder to assemble
scored memories (session/project/user) plus RAG hits for the current request and
writes the result into ``state.project_context`` for downstream agents.

If no ContextBuilder is wired (e.g. the Phase 2 default workflow), it falls back
to the lightweight behavior so the graph still runs.
"""

from __future__ import annotations

from core.messages import AgentMessage, MessageStatus
from core.roles import AgentRole
from core.state import ProjectState

from agents.base import BaseAgent


class MemoryAgent(BaseAgent):
    role = AgentRole.MEMORY

    def __init__(self, router, context_builder=None):
        super().__init__(router)
        self.context_builder = context_builder

    async def run(self, state: ProjectState) -> ProjectState:
        if self.context_builder is not None:
            context = await self.context_builder.build(
                state.user_request, project_id=state.project_id
            )
            if context:
                state.project_context = (state.project_context + "\n" + context).strip()
            summary = "Built context from memory + RAG"
        else:
            recalled = f"Short-term: working on '{state.user_request}'."
            state.project_context = (state.project_context + "\n" + recalled).strip()
            summary = "Loaded memory context (no RAG configured)"

        task_id = state.current_task.task_id if state.current_task else "n/a"
        state.record(
            AgentMessage(
                task_id=task_id,
                sender=self.role,
                status=MessageStatus.COMPLETED,
                summary=summary,
            )
        )
        return state
