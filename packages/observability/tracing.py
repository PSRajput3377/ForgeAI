"""Tracing — Langfuse integration for prompts/outputs/latency/traces.

One interface, two backends (the now-familiar pattern):
- ``NullTracer``     no-op; the default, fully offline.
- ``LangfuseTracer`` real Langfuse (lazy import) for production dashboards.

A tracer can also subscribe to the event bus, turning ForgeAI events into spans.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from contextlib import contextmanager

from observability.events import Event


class Tracer(ABC):
    @abstractmethod
    def trace_event(self, event: Event) -> None:
        """Record an event as a trace/span."""

    @contextmanager
    def span(self, name: str, **metadata):
        """Context manager for a named span (no-op by default)."""
        yield


class NullTracer(Tracer):
    """Default tracer: records nothing. Keeps the system dependency-free."""

    def trace_event(self, event: Event) -> None:
        return None


class LangfuseTracer(Tracer):
    """Sends traces to Langfuse. Imports the SDK lazily so it isn't required
    unless configured."""

    def __init__(self, public_key: str, secret_key: str, host: str):
        self.public_key = public_key
        self.secret_key = secret_key
        self.host = host
        self._client = None

    def _ensure(self):
        if self._client is None:
            from langfuse import Langfuse  # lazy import

            self._client = Langfuse(
                public_key=self.public_key, secret_key=self.secret_key, host=self.host
            )
        return self._client

    def trace_event(self, event: Event) -> None:
        client = self._ensure()
        client.event(
            name=event.type.value,
            metadata={"agent": event.agent, "run_id": event.run_id, **event.payload},
        )
