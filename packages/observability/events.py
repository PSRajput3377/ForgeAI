"""Event types — every action in ForgeAI becomes an Event.

Events are the backbone of observability: agents, tools, and the execution
engine emit them; the event bus fans them out to storage, metrics, and live
WebSocket subscribers. One typed envelope keeps producers and consumers
decoupled.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class EventType(StrEnum):
    """The vocabulary of things that happen during a run."""

    # Run lifecycle
    RUN_STARTED = "run.started"
    RUN_COMPLETED = "run.completed"
    # Agent lifecycle
    AGENT_STARTED = "agent.started"
    AGENT_COMPLETED = "agent.completed"
    AGENT_FAILED = "agent.failed"
    # Tool calls
    TOOL_STARTED = "tool.started"
    TOOL_COMPLETED = "tool.completed"
    # Execution / build-test
    BUILD_STARTED = "build.started"
    BUILD_FAILED = "build.failed"
    BUILD_PASSED = "build.passed"
    REFLECTION_STARTED = "reflection.started"
    # Memory / RAG
    MEMORY_RETRIEVED = "memory.retrieved"
    RAG_RETRIEVED = "rag.retrieved"
    # File changes
    FILE_CHANGED = "file.changed"
    # Human approval
    APPROVAL_REQUESTED = "approval.requested"
    APPROVAL_RESOLVED = "approval.resolved"
    # Notifications
    NOTIFICATION = "notification"


class Event(BaseModel):
    """A single observable event.

    ``tick`` is a logical, monotonic sequence number assigned by the bus — used
    for deterministic ordering and replay without relying on wall-clock time.
    """

    type: EventType
    # Correlation: which run/task/agent this belongs to.
    run_id: str | None = None
    task_id: str | None = None
    agent: str | None = None
    # Arbitrary structured detail (tool args, durations, diffs, …).
    payload: dict = Field(default_factory=dict)
    # Assigned by the bus on publish.
    tick: int = 0
    # Optional wall-clock stamp (ISO string), injected by the caller if needed.
    timestamp: str | None = None
