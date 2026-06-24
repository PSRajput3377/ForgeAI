"""Memory persistence backend.

One interface; an in-memory backend for tests/offline. The production backend
(PostgreSQL via SQLAlchemy) is added in the Database phase and implements the
same interface, so the MemoryManager doesn't change.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from memory.types import MemoryItem, MemoryScope


class MemoryStore(ABC):
    @abstractmethod
    async def put(self, item: MemoryItem) -> None: ...

    @abstractmethod
    async def get(
        self, scope: MemoryScope, key: str, **owner: str
    ) -> MemoryItem | None: ...

    @abstractmethod
    async def query(self, scope: MemoryScope, **owner: str) -> list[MemoryItem]: ...

    @abstractmethod
    async def delete(self, scope: MemoryScope, key: str, **owner: str) -> None: ...


def _owner_matches(item: MemoryItem, owner: dict[str, str]) -> bool:
    return all(getattr(item, k, None) == v for k, v in owner.items())


class InMemoryStore(MemoryStore):
    """Dict-backed store keyed by (scope, key, owner tuple)."""

    def __init__(self) -> None:
        self._items: list[MemoryItem] = []

    def _find(
        self, scope: MemoryScope, key: str, owner: dict[str, str]
    ) -> MemoryItem | None:
        for it in self._items:
            if it.scope == scope and it.key == key and _owner_matches(it, owner):
                return it
        return None

    async def put(self, item: MemoryItem) -> None:
        owner = {
            k: v
            for k, v in {
                "session_id": item.session_id,
                "project_id": item.project_id,
                "user_id": item.user_id,
            }.items()
            if v is not None
        }
        existing = self._find(item.scope, item.key, owner)
        if existing is not None:
            self._items.remove(existing)
        self._items.append(item)

    async def get(
        self, scope: MemoryScope, key: str, **owner: str
    ) -> MemoryItem | None:
        return self._find(scope, key, owner)

    async def query(self, scope: MemoryScope, **owner: str) -> list[MemoryItem]:
        return [
            it for it in self._items if it.scope == scope and _owner_matches(it, owner)
        ]

    async def delete(self, scope: MemoryScope, key: str, **owner: str) -> None:
        found = self._find(scope, key, owner)
        if found is not None:
            self._items.remove(found)
