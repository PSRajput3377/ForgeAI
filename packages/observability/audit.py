"""Human Approval Center — pause for approval on sensitive actions.

When an agent wants to delete files, push git, merge a PR, or deploy, it opens
an ApprovalRequest here. The center emits an ``approval.requested`` event (so the
UI can prompt) and blocks until resolved, then emits ``approval.resolved``.

This is the event-driven companion to the Phase 5 ``ApprovalGate``: the gate
decides *policy* (what needs approval); the center coordinates the *human loop*
and the audit trail.
"""

from __future__ import annotations

import asyncio

from pydantic import BaseModel

from observability.bus import EventBus
from observability.events import EventType


class ApprovalRequest(BaseModel):
    id: str
    action: str
    details: dict = {}
    resolved: bool = False
    approved: bool = False


class HumanApprovalCenter:
    """Tracks pending approvals and bridges them to the event bus."""

    def __init__(self, bus: EventBus) -> None:
        self.bus = bus
        self._pending: dict[str, ApprovalRequest] = {}
        self._waiters: dict[str, asyncio.Event] = {}

    async def request(self, request_id: str, action: str, **details) -> ApprovalRequest:
        """Open an approval request and emit the event. Does not block."""
        req = ApprovalRequest(id=request_id, action=action, details=details)
        self._pending[request_id] = req
        self._waiters[request_id] = asyncio.Event()
        await self.bus.emit(
            EventType.APPROVAL_REQUESTED,
            payload={"id": request_id, "action": action, "details": details},
        )
        return req

    async def resolve(self, request_id: str, approved: bool) -> None:
        """Approve or deny a pending request; unblocks any waiter."""
        req = self._pending.get(request_id)
        if req is None or req.resolved:
            return
        req.resolved = True
        req.approved = approved
        await self.bus.emit(
            EventType.APPROVAL_RESOLVED,
            payload={"id": request_id, "approved": approved},
        )
        if request_id in self._waiters:
            self._waiters[request_id].set()

    async def wait_for(self, request_id: str, timeout: float | None = None) -> bool:
        """Block until the request is resolved; return whether it was approved."""
        waiter = self._waiters.get(request_id)
        if waiter is None:
            return False
        try:
            await asyncio.wait_for(waiter.wait(), timeout=timeout)
        except TimeoutError:
            return False
        return self._pending[request_id].approved

    def pending(self) -> list[ApprovalRequest]:
        return [r for r in self._pending.values() if not r.resolved]
