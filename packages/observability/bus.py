"""Event Bus — agents publish events; subscribers (storage, metrics, WebSockets)
receive them.

Async pub/sub. The bus assigns each event a monotonic ``tick`` for ordering and
replay, then fans it out to every subscriber. Subscribers are simple callables
(sync or async). A failing subscriber never breaks publishing or other
subscribers.
"""

from __future__ import annotations

import inspect
from collections.abc import Awaitable, Callable

from observability.events import Event

Subscriber = Callable[[Event], None | Awaitable[None]]


class EventBus:
    """In-process async event bus with monotonic ordering."""

    def __init__(self) -> None:
        self._subscribers: list[Subscriber] = []
        self._tick = 0

    def subscribe(self, subscriber: Subscriber) -> Callable[[], None]:
        """Register a subscriber. Returns an unsubscribe function."""
        self._subscribers.append(subscriber)

        def unsubscribe() -> None:
            if subscriber in self._subscribers:
                self._subscribers.remove(subscriber)

        return unsubscribe

    async def publish(self, event: Event) -> Event:
        """Stamp the event with the next tick and fan it out to subscribers."""
        self._tick += 1
        event.tick = self._tick
        for sub in list(self._subscribers):
            try:
                result = sub(event)
                if inspect.isawaitable(result):
                    await result
            except Exception:  # noqa: BLE001 - a bad subscriber must not break others
                continue
        return event

    async def emit(self, type_, **fields) -> Event:
        """Convenience: build and publish an Event in one call."""
        return await self.publish(Event(type=type_, **fields))
