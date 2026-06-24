"""BaseAgent — shared behavior for every specialist.

An agent knows its role, holds a reference to the ``ModelRouter``, and can build
a chat message list from its system prompt plus a user payload. Subclasses
implement ``run(state)`` to do their one job against the shared ``ProjectState``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from core.roles import AgentRole
from core.state import ProjectState
from models.base import Message
from models.router import ModelRouter
from prompts import system_prompt


class BaseAgent(ABC):
    """Common scaffolding for all agents."""

    role: AgentRole

    def __init__(self, router: ModelRouter):
        self.router = router

    def _messages(self, user_content: str) -> list[Message]:
        """Build a [system, user] message list for this agent's role."""
        return [
            Message(role="system", content=system_prompt(self.role)),
            Message(role="user", content=user_content),
        ]

    async def _ask(self, user_content: str, temperature: float = 0.2) -> str:
        """Convenience: run a completion for this role and return the text."""
        resp = await self.router.complete_for(
            self.role, self._messages(user_content), temperature=temperature
        )
        return resp.content

    @abstractmethod
    async def run(self, state: ProjectState) -> ProjectState:
        """Perform this agent's job, mutating and returning the shared state."""
        raise NotImplementedError
