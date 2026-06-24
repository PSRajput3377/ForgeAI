"""Echo provider — a deterministic, offline fake for tests and local dev.

Lets the entire agent workflow run without a live LLM or pulled models. It
echoes a compact view of the prompt so tests can assert the routing/plumbing
worked, independent of any model's actual output.
"""

from __future__ import annotations

from models.base import CompletionRequest, CompletionResponse, LLMProvider


class EchoProvider(LLMProvider):
    """Returns canned, deterministic responses. Never makes a network call."""

    name = "echo"

    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        last_user = next(
            (m.content for m in reversed(request.messages) if m.role == "user"),
            "",
        )
        return CompletionResponse(
            model=request.model,
            content=f"[echo:{request.model}] {last_user}",
            raw={"provider": "echo"},
        )

    async def embed(self, model: str, text: str) -> list[float]:
        # Tiny deterministic pseudo-embedding; good enough for wiring tests.
        return [float(len(text) % 7), float(len(model) % 5), 0.0]
