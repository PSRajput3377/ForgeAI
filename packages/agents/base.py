"""BaseAgent — shared behavior for every specialist.

An agent knows its role, holds a reference to the ``ModelRouter``, and can build
a chat message list from its system prompt plus a user payload. Subclasses
implement ``run(state)`` to do their one job against the shared ``ProjectState``.
"""

from __future__ import annotations

import json
import re
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

    async def _ask_json(self, user_content: str, temperature: float = 0.2):
        """Ask the model for a JSON object and parse it.

        Returns the parsed object (dict/list) on success, or ``None`` when the
        response isn't valid JSON. The offline ``EchoProvider`` echoes the
        prompt back (never JSON), so this returns ``None`` there — every caller
        falls back to its deterministic skeleton, keeping the offline workflow
        and its tests unchanged. With a real provider (OpenAI), the structured
        output drives genuine multi-file generation.
        """
        resp = await self.router.complete_for(
            self.role,
            self._messages(user_content),
            temperature=temperature,
            response_format={"type": "json_object"},
        )
        return self._parse_json(resp.content)

    @staticmethod
    def _parse_json(text: str):
        """Best-effort parse of a model's text into JSON. ``None`` on failure."""
        if not text:
            return None
        try:
            return json.loads(text)
        except (json.JSONDecodeError, ValueError):
            pass
        # Tolerate ```json fenced blocks or prose around a single JSON object.
        fenced = re.search(r"```(?:json)?\s*(\{.*?\}|\[.*?\])\s*```", text, re.DOTALL)
        candidate = fenced.group(1) if fenced else None
        if candidate is None:
            brace = re.search(r"(\{.*\}|\[.*\])", text, re.DOTALL)
            candidate = brace.group(1) if brace else None
        if candidate is None:
            return None
        try:
            return json.loads(candidate)
        except (json.JSONDecodeError, ValueError):
            return None

    @abstractmethod
    async def run(self, state: ProjectState) -> ProjectState:
        """Perform this agent's job, mutating and returning the shared state."""
        raise NotImplementedError
