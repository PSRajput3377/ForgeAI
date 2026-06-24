# Production Specification

Contracts for production reliability, scale, and operations. Narrative in
[`../docs/production.md`](../docs/production.md). Source: `packages/runtime/`.

## Queue & workers

- Agent work MUST be enqueueable and processed by a worker pool with bounded
  concurrency (non-blocking API).
- Enqueueing an unregistered task MUST be rejected.
- A job that exhausts its retries MUST move to the dead-letter queue with its
  error and attempt count.
- Queue depth MUST be observable.

## Reliability

- Retry MUST use bounded exponential backoff with a cap; sleep MUST be injectable.
- The circuit breaker MUST trip OPEN after N consecutive failures, fail fast
  while OPEN, probe HALF_OPEN after a cooldown, and close on success. Time MUST
  be injectable.

## Rate limiting

- Limits MUST be per-key (user/org) via a token bucket that refills over time.

## Health & metrics

- `/health` MUST be a cheap liveness probe.
- `/health/ready` MUST aggregate dependency checks into healthy/degraded/
  unhealthy and MUST treat a throwing check as down (not a crash).
- `/metrics` MUST emit Prometheus text format (counters, gauges, summaries).

## Security & isolation

- Sensitive egress MUST be deny-by-default with an allow-list (NetworkPolicy).
- Secrets MUST be encrypted at rest (Phase 9).
- Tenant isolation MUST hold at DB/API/memory/vector levels (Phase 7).

## Feature flags

- Flags MUST support a global default and per-workspace overrides, togglable
  without redeploying.

## Parallelism

- Independent sub-tasks MUST run concurrently (bounded); a failing branch MUST
  be captured, not abort the others; results MUST be mergeable.

## Acceptance criteria

- [ ] Queue processes jobs with N workers; depth observable.
- [ ] Failed job retries then dead-letters.
- [ ] Circuit breaker trips, fails fast, and recovers.
- [ ] Rate limiter is per-key and refills.
- [ ] /health, /health/ready, /metrics behave per spec.
- [ ] Feature flag default + per-workspace override.
- [ ] Network policy allow-list denies by default.
- [ ] Parallel split → merge isolates failures.
- [ ] All offline-testable with injected clocks/sleeps.
