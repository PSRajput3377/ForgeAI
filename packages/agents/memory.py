"""MemoryAgent — surfaces short-term and long-term context.

Phase 2 skeleton holds the seam only; PostgreSQL (long-term) and Qdrant
(semantic recall) wiring lands in Phase 6 (Memory + RAG).
"""

from __future__ import annotations

from core.messages import AgentMessage, MessageStatus
from core.roles import AgentRole
from core.state import ProjectState

from agents.base import BaseAgent


class MemoryAgent(BaseAgent):
    role = AgentRole.MEMORY

    async def run(self, state: ProjectState) -> ProjectState:
        # Placeholder: short-term memory = the request itself. Long-term recall
        # (coding style, past decisions) arrives with the RAG layer in Phase 6.
        recalled = f"Short-term: working on '{state.user_request}'."
        state.project_context = (state.project_context + "\n" + recalled).strip()
        task_id = state.current_task.task_id if state.current_task else "n/a"
        state.record(
            AgentMessage(
                task_id=task_id,
                sender=self.role,
                status=MessageStatus.COMPLETED,
                summary="Loaded memory context",
            )
        )
        return state
