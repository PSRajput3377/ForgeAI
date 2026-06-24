"""Ollama provider — the default local backend for the MVP.

Talks to the Ollama HTTP API (``/api/chat``, ``/api/embeddings``). Requires the
ollama service running and the models pulled (``make pull-models``).
"""

from __future__ import annotations

import httpx

from models.base import CompletionRequest, CompletionResponse, LLMProvider


class OllamaProvider(LLMProvider):
    """Calls a local/remote Ollama server over HTTP."""

    name = "ollama"

    def __init__(
        self, base_url: str = "http://localhost:11434", timeout: float = 120.0
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        payload = {
            "model": request.model,
            "messages": [m.model_dump() for m in request.messages],
            "stream": False,
            "options": {"temperature": request.temperature},
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(f"{self.base_url}/api/chat", json=payload)
            resp.raise_for_status()
            data = resp.json()
        return CompletionResponse(
            model=request.model,
            content=data.get("message", {}).get("content", ""),
            raw=data,
        )

    async def embed(self, model: str, text: str) -> list[float]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(
                f"{self.base_url}/api/embeddings",
                json={"model": model, "prompt": text},
            )
            resp.raise_for_status()
            data = resp.json()
        return data.get("embedding", [])
