"""Reliability primitives: retry policy, circuit breaker, dead-letter queue.

Production agent workflows are long-running and depend on flaky external systems
(GitHub, Jira, …). These primitives keep the platform resilient: retry transient
failures, stop hammering a down dependency, and quarantine permanently-failed
jobs for debugging. All deterministic and offline-testable (injectable
clock/sleep).
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class RetryPolicy(BaseModel):
    """Bounded exponential backoff with a cap."""

    max_attempts: int = 3
    base_delay: float = 0.5
    factor: float = 2.0
    max_delay: float = 30.0

    def delay_for(self, attempt: int) -> float:
        """Backoff delay before ``attempt`` (1-indexed)."""
        return min(self.max_delay, self.base_delay * (self.factor ** (attempt - 1)))


async def run_with_retry(
    fn: Callable[[], Awaitable[Any]],
    policy: RetryPolicy,
    *,
    sleep: Callable[[float], Awaitable[None]],
    retry_on: type[Exception] | tuple[type[Exception], ...] = Exception,
) -> Any:
    """Run ``fn`` with retries per ``policy``. Re-raises the last error if all
    attempts fail. ``sleep`` is injected so tests run instantly."""
    last_exc: Exception | None = None
    for attempt in range(1, policy.max_attempts + 1):
        try:
            return await fn()
        except retry_on as exc:  # noqa: B902 - caller chooses the exception set
            last_exc = exc
            if attempt < policy.max_attempts:
                await sleep(policy.delay_for(attempt))
    raise last_exc  # type: ignore[misc]


class CircuitState(StrEnum):
    CLOSED = "closed"  # normal: calls flow
    OPEN = "open"  # tripped: calls fail fast
    HALF_OPEN = "half_open"  # probing: allow one trial call


class CircuitBreakerError(RuntimeError):
    """Raised when the circuit is OPEN and a call is rejected."""


class CircuitBreaker:
    """Trips OPEN after N consecutive failures; fails fast until a cooldown,
    then probes HALF_OPEN. A success closes it again.

    Time is injected via ``clock`` for deterministic tests.
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        reset_timeout: float = 30.0,
        clock: Callable[[], float] = lambda: 0.0,
    ):
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self._clock = clock
        self._failures = 0
        self._opened_at: float | None = None
        self.state = CircuitState.CLOSED

    def _can_attempt(self) -> bool:
        if self.state == CircuitState.OPEN:
            if (
                self._opened_at is not None
                and self._clock() - self._opened_at >= self.reset_timeout
            ):
                self.state = CircuitState.HALF_OPEN
                return True
            return False
        return True

    async def call(self, fn: Callable[[], Awaitable[Any]]) -> Any:
        if not self._can_attempt():
            raise CircuitBreakerError("Circuit is OPEN; failing fast")
        try:
            result = await fn()
        except Exception:
            self._on_failure()
            raise
        self._on_success()
        return result

    def _on_success(self) -> None:
        self._failures = 0
        self.state = CircuitState.CLOSED
        self._opened_at = None

    def _on_failure(self) -> None:
        self._failures += 1
        if (
            self._failures >= self.failure_threshold
            or self.state == CircuitState.HALF_OPEN
        ):
            self.state = CircuitState.OPEN
            self._opened_at = self._clock()


class DeadLetterEntry(BaseModel):
    job_id: str
    payload: dict = Field(default_factory=dict)
    error: str = ""
    attempts: int = 0


class DeadLetterQueue:
    """Quarantine for jobs that exhausted their retries — kept for debugging."""

    def __init__(self) -> None:
        self._entries: list[DeadLetterEntry] = []

    def add(self, job_id: str, payload: dict, error: str, attempts: int) -> None:
        self._entries.append(
            DeadLetterEntry(
                job_id=job_id, payload=payload, error=error, attempts=attempts
            )
        )

    def all(self) -> list[DeadLetterEntry]:
        return list(self._entries)

    def __len__(self) -> int:
        return len(self._entries)
