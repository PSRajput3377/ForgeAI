"""Provider-agnostic LLM interface.

Every provider (Ollama now; OpenAI/Claude/Gemini later) implements
``LLMProvider``. Agents depend only on this interface.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from pydantic import BaseModel


class Message(BaseModel):
    """A single chat message."""

    role: str  # "system" | "user" | "assistant"
    content: str


class CompletionRequest(BaseModel):
    """A request for a chat completion."""

    model: str
    messages: list[Message]
    temperature: float = 0.2
    max_tokens: int | None = None


class CompletionResponse(BaseModel):
    """A completion result, normalized across providers."""

    model: str
    content: str
    raw: dict = {}


class LLMProvider(ABC):
    """Interface all model providers implement."""

    name: str = "base"

    @abstractmethod
    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        """Return a completion for the given request."""
        raise NotImplementedError

    @abstractmethod
    async def embed(self, model: str, text: str) -> list[float]:
        """Return an embedding vector for ``text``."""
        raise NotImplementedError
