# Observability Specification

Contracts for the observability subsystem. Narrative in
[`../docs/observability.md`](../docs/observability.md). Source:
`packages/observability/`.

## Events & bus

- Every significant action MUST be published as a typed `Event`.
- The bus MUST assign a strictly increasing `tick` per published event (for
  deterministic ordering and replay).
- The bus MUST fan out to all subscribers; a failing subscriber MUST NOT break
  publishing or other subscribers.
- Subscribers MAY be sync or async.

## Instrumentation

- An instrumented workflow MUST emit `agent.started` and then `agent.completed`
  (or `agent.failed`) for each node, and MUST bracket a run with `run.started` /
  `run.completed`.
- Instrumentation MUST be opt-in: with no bus, the workflow behaves exactly as
  before (no events, same result).

## Store, timeline, audit

- The store MUST preserve insertion via ticks; `timeline(run_id)` MUST return
  that run's events in tick order.
- An audit trail MUST be derivable for any run (who → what → when).

## Metrics

- Metrics MUST be computed from events alone (no separate code path).
- MUST expose per-agent success rate + avg duration, per-tool calls/failures,
  task success rate, and token totals.

## Tracing

- A `Tracer` MUST be swappable; `NullTracer` MUST be a no-op so the system runs
  with no external tracing service.

## Live updates

- A WebSocket endpoint MUST stream events in real time (no polling) and MUST
  unsubscribe on disconnect.

## Human approval

- Gated actions MUST emit `approval.requested`, block until resolved, then emit
  `approval.resolved`; an unresolved request MUST time out to denied.

## Acceptance criteria

- [ ] Monotonic ticks; failing subscriber isolated.
- [ ] Instrumented workflow yields a complete, ordered timeline.
- [ ] No-bus workflow still runs (backward compatible).
- [ ] Metrics aggregate correctly from events.
- [ ] WebSocket streams a run's events end-to-end.
- [ ] Approval request → resolve loop works and times out safely.
