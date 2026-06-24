"""observability — make ForgeAI transparent.

Every action becomes an Event on the EventBus, which fans out to:
- EventStore   (timeline, replay, audit trail)
- MetricsCollector (per-agent/tool/cost dashboards)
- Tracer       (Langfuse, optional)
- WebSocket subscribers (live frontend updates — wired in the API)

Offline by default (NullTracer, in-memory store); Langfuse/PostgreSQL drop in
behind the same interfaces (ADR-0017).
"""

from observability.audit import ApprovalRequest, HumanApprovalCenter
from observability.bus import EventBus, Subscriber
from observability.events import Event, EventType
from observability.metrics import AgentStat, MetricsCollector, ToolStat
from observability.store import EventStore
from observability.tracing import LangfuseTracer, NullTracer, Tracer

__all__ = [
    "AgentStat",
    "ApprovalRequest",
    "Event",
    "EventBus",
    "EventStore",
    "EventType",
    "HumanApprovalCenter",
    "LangfuseTracer",
    "MetricsCollector",
    "NullTracer",
    "Subscriber",
    "ToolStat",
    "Tracer",
]
