"""Rate limiting — token-bucket per key (user/org/endpoint).

Protects the API and expensive agent runs from abuse and runaway loops. The
clock is injectable for deterministic tests; a Redis-backed bucket implements the
same interface in production (shared across API replicas).
"""

from __future__ import annotations

from collections.abc import Callable


class TokenBucket:
    """Classic token bucket: ``rate`` tokens/sec up to ``capacity``."""

    def __init__(
        self, rate: float, capacity: float, clock: Callable[[], float] = lambda: 0.0
    ):
        self.rate = rate
        self.capacity = capacity
        self._clock = clock
        self._tokens = capacity
        self._last = clock()

    def _refill(self) -> None:
        now = self._clock()
        elapsed = now - self._last
        self._tokens = min(self.capacity, self._tokens + elapsed * self.rate)
        self._last = now

    def allow(self, cost: float = 1.0) -> bool:
        self._refill()
        if self._tokens >= cost:
            self._tokens -= cost
            return True
        return False


class RateLimiter:
    """Per-key token buckets (e.g. one per user or org)."""

    def __init__(
        self, rate: float, capacity: float, clock: Callable[[], float] = lambda: 0.0
    ):
        self.rate = rate
        self.capacity = capacity
        self._clock = clock
        self._buckets: dict[str, TokenBucket] = {}

    def allow(self, key: str, cost: float = 1.0) -> bool:
        bucket = self._buckets.get(key)
        if bucket is None:
            bucket = TokenBucket(self.rate, self.capacity, self._clock)
            self._buckets[key] = bucket
        return bucket.allow(cost)
