"""OpenAI provider — a hosted backend for real code generation.

Talks to the OpenAI-compatible Chat Completions API (``/chat/completions`` and
``/embeddings``). Requires ``OPENAI_API_KEY``. Because the endpoint is the
standard OpenAI shape, this also works against any OpenAI-compatible gateway by
overriding ``base_url`` (ADR-0003: providers are configurable, agent code
doesn't change).
"""

from __future__ import annotations

import httpx

from models.base import CompletionRequest, CompletionResponse, LLMProvider


class OpenAIProvider(LLMProvider):
    """Calls the OpenAI Chat Completions API over HTTP."""

    name = "openai"

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.openai.com/v1",
        timeout: float = 120.0,
    ):
        if not api_key:
            raise ValueError(
                "OpenAIProvider requires an API key. Set OPENAI_API_KEY in your .env "
                "(or switch MODEL_PROVIDER to 'echo' for the offline demo)."
            )
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    @staticmethod
    def _raise_for_status(resp: httpx.Response) -> None:
        """Raise with the API's own error message so failures are actionable.

        OpenAI returns a JSON ``error.message`` (e.g. ``insufficient_quota`` when
        the account has no credits/billing) that's far more useful than a bare
        status code. Surface it.
        """
        if resp.is_success:
            return
        detail = ""
        try:
            detail = (resp.json().get("error") or {}).get("message", "")
        except (ValueError, AttributeError):
            detail = resp.text[:300]
        raise RuntimeError(f"OpenAI API error {resp.status_code}: {detail or 'request failed'}")

    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        payload: dict = {
            "model": request.model,
            "messages": [m.model_dump() for m in request.messages],
            "temperature": request.temperature,
        }
        if request.max_tokens is not None:
            payload["max_tokens"] = request.max_tokens
        if request.response_format is not None:
            payload["response_format"] = request.response_format

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(
                f"{self.base_url}/chat/completions",
                headers=self._headers(),
                json=payload,
            )
            self._raise_for_status(resp)
            data = resp.json()

        content = ""
        choices = data.get("choices") or []
        if choices:
            content = choices[0].get("message", {}).get("content", "") or ""
        return CompletionResponse(model=request.model, content=content, raw=data)

    async def embed(self, model: str, text: str) -> list[float]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(
                f"{self.base_url}/embeddings",
                headers=self._headers(),
                json={"model": model, "input": text},
            )
            self._raise_for_status(resp)
            data = resp.json()
        items = data.get("data") or []
        return items[0].get("embedding", []) if items else []
