"""Event store + audit trail.

Persists every event so a run can be replayed and audited. Phase 6 ships an
in-memory store (offline-testable); the PostgreSQL-backed store (Events /
AgentRuns / ToolCalls tables) lands in the Database phase behind the same shape.
"""

from __future__ import annotations

from observability.events import Event, EventType


class EventStore:
    """Append-only event log with timeline/replay queries."""

    def __init__(self) -> None:
        self._events: list[Event] = []

    def append(self, event: Event) -> None:
        self._events.append(event)

    def all(self) -> list[Event]:
        return list(self._events)

    def timeline(self, run_id: str) -> list[Event]:
        """Ordered events for a run (the Agent Timeline / replay source)."""
        return sorted((e for e in self._events if e.run_id == run_id), key=lambda e: e.tick)

    def by_type(self, type_: EventType) -> list[Event]:
        return [e for e in self._events if e.type == type_]

    def audit_trail(self, run_id: str | None = None) -> list[dict]:
        """Flat, human-readable audit records (who → what → when)."""
        events = self.timeline(run_id) if run_id else sorted(self._events, key=lambda e: e.tick)
        return [
            {
                "tick": e.tick,
                "type": e.type.value,
                "agent": e.agent,
                "run_id": e.run_id,
                "payload": e.payload,
            }
            for e in events
        ]
