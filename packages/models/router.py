"""ModelRouter — maps an agent role to a configured model on a provider.

This is the single seam between agents and LLMs. Agents ask the router to
``complete_for(role, messages)``; the router knows which model each role uses
and which provider serves it. Reconfiguring models or swapping providers
happens here, never in agent code.
"""

from __future__ import annotations

from core.roles import AgentRole

from models.base import CompletionResponse, LLMProvider, Message


class ModelRouter:
    """Routes completion requests for a given role to the right model."""

    def __init__(
        self,
        provider: LLMProvider,
        role_models: dict[AgentRole, str],
        embed_model: str = "nomic-embed-text",
        default_model: str = "qwen3:8b",
    ):
        self.provider = provider
        self.role_models = role_models
        self.embed_model = embed_model
        self.default_model = default_model

    def model_for(self, role: AgentRole) -> str:
        """Return the configured model name for a role."""
        return self.role_models.get(role, self.default_model)

    async def complete_for(
        self,
        role: AgentRole,
        messages: list[Message],
        temperature: float = 0.2,
        response_format: dict | None = None,
    ) -> CompletionResponse:
        """Run a completion using the model configured for ``role``.

        ``response_format`` is an optional OpenAI-style structured-output hint
        (e.g. ``{"type": "json_object"}``); providers that ignore it are
        unaffected.
        """
        from models.base import CompletionRequest

        request = CompletionRequest(
            model=self.model_for(role),
            messages=messages,
            temperature=temperature,
            response_format=response_format,
        )
        return await self.provider.complete(request)

    async def embed(self, text: str) -> list[float]:
        """Embed text with the configured embedding model."""
        return await self.provider.embed(self.embed_model, text)
