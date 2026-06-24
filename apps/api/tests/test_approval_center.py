"""Tests for the Human Approval Center (event-driven approval loop)."""

import asyncio

import pytest
from observability.audit import HumanApprovalCenter
from observability.bus import EventBus
from observability.events import EventType
from observability.store import EventStore


@pytest.mark.asyncio
async def test_request_emits_event_and_is_pending():
    bus = EventBus()
    store = EventStore()
    bus.subscribe(store.append)
    center = HumanApprovalCenter(bus)

    await center.request("req-1", "git_push", branch="main")
    assert len(center.pending()) == 1
    assert (
        store.by_type(EventType.APPROVAL_REQUESTED)[0].payload["action"] == "git_push"
    )


@pytest.mark.asyncio
async def test_approval_unblocks_waiter():
    bus = EventBus()
    center = HumanApprovalCenter(bus)
    await center.request("req-2", "deploy")

    async def approver():
        await asyncio.sleep(0.01)
        await center.resolve("req-2", approved=True)

    asyncio.create_task(approver())
    approved = await center.wait_for("req-2", timeout=1.0)
    assert approved is True
    assert center.pending() == []


@pytest.mark.asyncio
async def test_wait_timeout_returns_false():
    bus = EventBus()
    center = HumanApprovalCenter(bus)
    await center.request("req-3", "delete_files")
    approved = await center.wait_for("req-3", timeout=0.05)
    assert approved is False  # nobody resolved it
