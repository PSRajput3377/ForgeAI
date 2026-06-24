"""Tests for the observability subsystem: bus, store, metrics, tracing, approvals."""

import pytest
from observability.bus import EventBus
from observability.events import Event, EventType
from observability.metrics import MetricsCollector
from observability.store import EventStore
from observability.tracing import NullTracer


@pytest.mark.asyncio
async def test_bus_assigns_monotonic_ticks_and_fans_out():
    bus = EventBus()
    received = []
    bus.subscribe(received.append)
    e1 = await bus.emit(EventType.AGENT_STARTED, agent="planner")
    e2 = await bus.emit(EventType.AGENT_COMPLETED, agent="planner")
    assert e1.tick == 1 and e2.tick == 2
    assert [e.type for e in received] == [
        EventType.AGENT_STARTED,
        EventType.AGENT_COMPLETED,
    ]


@pytest.mark.asyncio
async def test_bus_isolates_failing_subscriber():
    bus = EventBus()
    good = []

    def boom(_):
        raise RuntimeError("bad subscriber")

    bus.subscribe(boom)
    bus.subscribe(good.append)
    await bus.emit(EventType.NOTIFICATION)
    assert len(good) == 1  # the good subscriber still received it


@pytest.mark.asyncio
async def test_async_subscriber_supported():
    bus = EventBus()
    received = []

    async def asub(e):
        received.append(e)

    bus.subscribe(asub)
    await bus.emit(EventType.RUN_STARTED, run_id="r1")
    assert received[0].run_id == "r1"


@pytest.mark.asyncio
async def test_store_timeline_and_audit():
    bus = EventBus()
    store = EventStore()
    bus.subscribe(store.append)
    await bus.emit(EventType.AGENT_STARTED, agent="planner", run_id="r1")
    await bus.emit(EventType.AGENT_COMPLETED, agent="planner", run_id="r1")
    await bus.emit(EventType.AGENT_STARTED, agent="coder", run_id="r2")

    timeline = store.timeline("r1")
    assert [e.agent for e in timeline] == ["planner", "planner"]
    assert [e.tick for e in timeline] == sorted(e.tick for e in timeline)

    audit = store.audit_trail("r1")
    assert len(audit) == 2 and audit[0]["type"] == "agent.started"


@pytest.mark.asyncio
async def test_metrics_aggregation():
    bus = EventBus()
    metrics = MetricsCollector()
    bus.subscribe(metrics.handle)

    await bus.emit(EventType.AGENT_COMPLETED, agent="planner", payload={"duration": 1.0})
    await bus.emit(EventType.AGENT_COMPLETED, agent="planner", payload={"duration": 3.0})
    await bus.emit(EventType.AGENT_FAILED, agent="coder", payload={"duration": 2.0})
    await bus.emit(
        EventType.TOOL_COMPLETED,
        payload={"tool": "filesystem", "duration": 0.1, "success": True},
    )
    await bus.emit(EventType.RUN_COMPLETED, payload={"success": True, "prompt_tokens": 100})

    snap = metrics.snapshot()
    assert snap["agents"]["planner"]["success_rate"] == 1.0
    assert snap["agents"]["planner"]["avg_duration"] == 2.0
    assert snap["agents"]["coder"]["success_rate"] == 0.0
    assert snap["tools"]["filesystem"]["calls"] == 1
    assert snap["success_rate"] == 1.0
    assert snap["tokens"]["prompt"] == 100


def test_null_tracer_is_noop():
    tracer = NullTracer()
    tracer.trace_event(Event(type=EventType.NOTIFICATION))
    with tracer.span("x"):
        pass  # no error
