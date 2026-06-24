"""Process-wide observability wiring for the API.

A single EventBus with an EventStore and MetricsCollector attached. Agents
publish to the bus; the store powers timeline/replay/audit endpoints; the
metrics collector powers the dashboard; WebSocket connections subscribe for
live updates. The tracer is Null unless Langfuse is configured.
"""

from __future__ import annotations

from observability.bus import EventBus
from observability.metrics import MetricsCollector
from observability.store import EventStore
from observability.tracing import NullTracer, Tracer

from app.config import settings


class Observability:
    """Holds the shared bus + subscribers for the running API process."""

    def __init__(self) -> None:
        self.bus = EventBus()
        self.store = EventStore()
        self.metrics = MetricsCollector()
        self.tracer: Tracer = self._build_tracer()
        # Wire the always-on subscribers.
        self.bus.subscribe(self.store.append)
        self.bus.subscribe(self.metrics.handle)
        self.bus.subscribe(self.tracer.trace_event)

    @staticmethod
    def _build_tracer() -> Tracer:
        # Langfuse keys are optional settings; default to a no-op tracer.
        public = getattr(settings, "langfuse_public_key", "")
        secret = getattr(settings, "langfuse_secret_key", "")
        host = getattr(settings, "langfuse_host", "")
        if public and secret and host:
            from observability.tracing import LangfuseTracer

            return LangfuseTracer(public, secret, host)
        return NullTracer()


# Module-level singleton for the process.
observability = Observability()
