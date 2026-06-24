"""runtime — production reliability, scale, and operations primitives.

Turns ForgeAI from a dev system into a production platform:
- queue + worker pool (non-blocking, scalable agent runs)
- reliability: retry policy, circuit breaker, dead-letter queue
- rate limiting (token bucket per key)
- health checks + Prometheus-style metrics
- feature flags + agent network policy
- multi-agent parallelism (split → parallel → merge)

All offline-testable with injected clocks/sleeps; production backends
(Celery/Redis/Prometheus) implement the same interfaces (ADR-0022).
"""

from runtime.features import FeatureFlags, NetworkPolicy
from runtime.health import Health, HealthRegistry, MetricsRegistry
from runtime.parallelism import SubResult, SubTask, merge_results, run_parallel
from runtime.queue import Job, JobQueue, JobStatus
from runtime.ratelimit import RateLimiter, TokenBucket
from runtime.reliability import (
    CircuitBreaker,
    CircuitBreakerError,
    CircuitState,
    DeadLetterQueue,
    RetryPolicy,
    run_with_retry,
)

__all__ = [
    "CircuitBreaker",
    "CircuitBreakerError",
    "CircuitState",
    "DeadLetterQueue",
    "FeatureFlags",
    "Health",
    "HealthRegistry",
    "Job",
    "JobQueue",
    "JobStatus",
    "MetricsRegistry",
    "NetworkPolicy",
    "RateLimiter",
    "RetryPolicy",
    "SubResult",
    "SubTask",
    "TokenBucket",
    "merge_results",
    "run_parallel",
    "run_with_retry",
]
