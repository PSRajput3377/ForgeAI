"""Tests for retry, circuit breaker, DLQ, rate limiting."""

import pytest
from runtime.ratelimit import RateLimiter, TokenBucket
from runtime.reliability import (
    CircuitBreaker,
    CircuitBreakerError,
    CircuitState,
    DeadLetterQueue,
    RetryPolicy,
    run_with_retry,
)


def test_retry_policy_backoff_capped():
    p = RetryPolicy(base_delay=1.0, factor=2.0, max_delay=5.0, max_attempts=5)
    assert p.delay_for(1) == 1.0
    assert p.delay_for(2) == 2.0
    assert p.delay_for(3) == 4.0
    assert p.delay_for(4) == 5.0  # capped


@pytest.mark.asyncio
async def test_retry_succeeds_after_failures():
    calls = {"n": 0}
    slept = []

    async def record_sleep(delay):
        slept.append(delay)

    async def flaky():
        calls["n"] += 1
        if calls["n"] < 3:
            raise RuntimeError("transient")
        return "ok"

    result = await run_with_retry(
        flaky, RetryPolicy(max_attempts=3, base_delay=0.1), sleep=record_sleep
    )
    assert result == "ok" and calls["n"] == 3
    assert len(slept) == 2  # two backoffs before success


@pytest.mark.asyncio
async def test_retry_reraises_after_exhaustion():
    async def always_fail():
        raise ValueError("nope")

    async def noop(_):
        pass

    with pytest.raises(ValueError):
        await run_with_retry(always_fail, RetryPolicy(max_attempts=2), sleep=noop)


@pytest.mark.asyncio
async def test_circuit_breaker_trips_and_recovers():
    t = {"now": 0.0}
    cb = CircuitBreaker(failure_threshold=2, reset_timeout=10.0, clock=lambda: t["now"])

    async def fail():
        raise RuntimeError("down")

    # Two failures trip the breaker.
    for _ in range(2):
        with pytest.raises(RuntimeError):
            await cb.call(fail)
    assert cb.state == CircuitState.OPEN

    # While OPEN, calls fail fast without invoking fn.
    with pytest.raises(CircuitBreakerError):
        await cb.call(fail)

    # After the cooldown, it half-opens and a success closes it.
    t["now"] = 11.0

    async def ok():
        return "ok"

    assert await cb.call(ok) == "ok"
    assert cb.state == CircuitState.CLOSED


def test_dead_letter_queue():
    dlq = DeadLetterQueue()
    dlq.add("job-1", {"x": 1}, "boom", attempts=3)
    assert len(dlq) == 1 and dlq.all()[0].job_id == "job-1"


def test_token_bucket_limits_then_refills():
    t = {"now": 0.0}
    bucket = TokenBucket(rate=1.0, capacity=2.0, clock=lambda: t["now"])
    assert bucket.allow() and bucket.allow()  # 2 tokens
    assert not bucket.allow()  # empty
    t["now"] = 1.0  # 1 second → 1 token refilled
    assert bucket.allow()
    assert not bucket.allow()


def test_rate_limiter_is_per_key():
    t = {"now": 0.0}
    rl = RateLimiter(rate=1.0, capacity=1.0, clock=lambda: t["now"])
    assert rl.allow("userA")
    assert not rl.allow("userA")
    assert rl.allow("userB")  # separate bucket
