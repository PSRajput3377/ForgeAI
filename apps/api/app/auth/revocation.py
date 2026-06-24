"""Token revocation — logout immediately invalidates a session.

A denylist of token JTIs/refresh tokens. Phase 7 ships an in-memory denylist
(offline-testable); a Redis-backed denylist (shared across processes, TTL =
token lifetime) drops in behind the same interface in production.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class TokenDenylist(ABC):
    @abstractmethod
    async def revoke(self, token: str) -> None: ...

    @abstractmethod
    async def is_revoked(self, token: str) -> bool: ...


class InMemoryDenylist(TokenDenylist):
    def __init__(self) -> None:
        self._revoked: set[str] = set()

    async def revoke(self, token: str) -> None:
        self._revoked.add(token)

    async def is_revoked(self, token: str) -> bool:
        return token in self._revoked


# Process-wide denylist (swap for a Redis-backed one in production).
denylist: TokenDenylist = InMemoryDenylist()
