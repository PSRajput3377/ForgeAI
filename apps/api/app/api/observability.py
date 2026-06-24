"""Observability endpoints: timeline, audit, metrics, and a live event WebSocket."""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from observability.events import Event

from app.observability_runtime import observability

router = APIRouter(prefix="/observability", tags=["observability"])


@router.get("/metrics")
def metrics() -> dict:
    """Dashboard-ready metrics snapshot (agents, tools, tasks, tokens)."""
    return observability.metrics.snapshot()


@router.get("/timeline/{run_id}")
def timeline(run_id: str) -> dict:
    """Ordered event timeline for a run (Agent Timeline / replay source)."""
    return {
        "run_id": run_id,
        "events": [e.model_dump() for e in observability.store.timeline(run_id)],
    }


@router.get("/audit/{run_id}")
def audit(run_id: str) -> dict:
    """Flat audit trail for a run."""
    return {"run_id": run_id, "audit": observability.store.audit_trail(run_id)}


@router.websocket("/live")
async def live(websocket: WebSocket) -> None:
    """Stream events to the frontend in real time (no polling)."""
    await websocket.accept()
    queue: asyncio.Queue[Event] = asyncio.Queue()

    def on_event(event: Event) -> None:
        queue.put_nowait(event)

    unsubscribe = observability.bus.subscribe(on_event)
    try:
        while True:
            event = await queue.get()
            await websocket.send_json(event.model_dump())
    except WebSocketDisconnect:
        pass
    finally:
        unsubscribe()
