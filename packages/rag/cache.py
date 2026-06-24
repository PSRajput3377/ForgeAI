"""Caching layer for retrieval (and other) results.

Three backends behind one interface:
- ``NullCache``     no-op (always miss); the default.
- ``InMemoryCache`` dict-based with TTL; offline, used in tests.
- ``RedisCache``    real Redis (lazy import); used in production.

Values are JSON-serializable (lists/dicts of primitives).
"""

from __future__ import annotations

import json
import time
from abc import ABC, abstractmethod
from typing import Any


class Cache(ABC):
    @abstractmethod
    async def get(self, key: str) -> Any | None: ...

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: int = 300) -> None: ...


class NullCache(Cache):
    """Disables caching (always a miss)."""

    async def get(self, key: str) -> Any | None:
        return None

    async def set(self, key: str, value: Any, ttl: int = 300) -> None:
        return None


class InMemoryCache(Cache):
    """In-process cache with TTL. Deterministic time source is injectable."""

    def __init__(self, clock=time.monotonic):
        self._store: dict[str, tuple[float, Any]] = {}
        self._clock = clock

    async def get(self, key: str) -> Any | None:
        item = self._store.get(key)
        if item is None:
            return None
        expires_at, value = item
        if expires_at < self._clock():
            del self._store[key]
            return None
        return value

    async def set(self, key: str, value: Any, ttl: int = 300) -> None:
        self._store[key] = (self._clock() + ttl, value)


class RedisCache(Cache):
    """Redis-backed cache (lazy import so redis isn't required for tests)."""

    def __init__(self, url: str, prefix: str = "forge:cache:"):
        self.url = url
        self.prefix = prefix
        self._client = None

    def _ensure(self):
        if self._client is None:
            import redis.asyncio as redis  # lazy import

            self._client = redis.from_url(self.url, decode_responses=True)
        return self._client

    async def get(self, key: str) -> Any | None:
        raw = await self._ensure().get(self.prefix + key)
        return json.loads(raw) if raw is not None else None

    async def set(self, key: str, value: Any, ttl: int = 300) -> None:
        await self._ensure().set(self.prefix + key, json.dumps(value), ex=ttl)
