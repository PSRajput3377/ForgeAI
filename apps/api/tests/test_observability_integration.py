"""Instrumented workflow emits a full event timeline → store + metrics (offline)."""

import pytest
from agents.workflow import build_workflow
from core.state import ProjectState
from observability.bus import EventBus
from observability.events import EventType
from observability.metrics import MetricsCollector
from observability.store import EventStore


@pytest.mark.asyncio
async def test_instrumented_workflow_produces_timeline_and_metrics(echo_router):
    bus = EventBus()
    store = EventStore()
    metrics = MetricsCollector()
    bus.subscribe(store.append)
    bus.subscribe(metrics.handle)

    app = build_workflow(echo_router, bus=bus)
    state = ProjectState(user_request="Add JWT auth", project_id="run-1")
    await app.ainvoke(state)

    timeline = store.timeline("run-1")
    # Every node emitted started + completed.
    started = [e.agent for e in timeline if e.type == EventType.AGENT_STARTED]
    completed = [e.agent for e in timeline if e.type == EventType.AGENT_COMPLETED]
    assert "planner" in started and "coder" in started
    assert len(started) == len(completed)  # all started nodes completed

    # Ticks are strictly increasing (replayable ordering).
    ticks = [e.tick for e in timeline]
    assert ticks == sorted(ticks)

    # Metrics captured per-agent durations.
    snap = metrics.snapshot()
    assert snap["agents"]["planner"]["runs"] == 1
    assert snap["agents"]["planner"]["success_rate"] == 1.0


@pytest.mark.asyncio
async def test_workflow_without_bus_still_runs(echo_router):
    # Backward compatible: no bus → no events, graph still completes.
    app = build_workflow(echo_router)
    result = ProjectState.model_validate(
        await app.ainvoke(ProjectState(user_request="x"))
    )
    assert result.final_response
