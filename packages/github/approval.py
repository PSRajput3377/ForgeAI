"""ApprovalService — explicit human approval gate for write actions.

The governance layer between "the agent wants to write to GitHub" and the write
actually happening. An action is *requested* (recording what will happen),
then a human *approves* or *rejects* it. Only approved requests may proceed.

This is deliberately simple and synchronous (request → approve/reject → check),
which makes the gated workflow easy to reason about and demo. It complements the
Phase 6 event-driven HumanApprovalCenter (which streams approval events to the
UI); a request id links the two.
"""

from __future__ import annotations

from enum import StrEnum
from uuid import uuid4

from pydantic import BaseModel, Field


class ApprovalStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class ApprovalRequest(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    action: str  # e.g. "create_pr"
    summary: str = ""
    details: dict = Field(default_factory=dict)
    status: ApprovalStatus = ApprovalStatus.PENDING
    decided_by: str | None = None

    @property
    def is_approved(self) -> bool:
        return self.status == ApprovalStatus.APPROVED


class ApprovalService:
    """Tracks approval requests and their decisions."""

    def __init__(self) -> None:
        self._requests: dict[str, ApprovalRequest] = {}

    def request(self, action: str, *, summary: str = "", **details) -> ApprovalRequest:
        """Open an approval request for a write action. Does not execute anything."""
        req = ApprovalRequest(action=action, summary=summary, details=details)
        self._requests[req.id] = req
        return req

    def get(self, request_id: str) -> ApprovalRequest | None:
        return self._requests.get(request_id)

    def approve(self, request_id: str, *, by: str | None = None) -> ApprovalRequest:
        return self._decide(request_id, ApprovalStatus.APPROVED, by)

    def reject(self, request_id: str, *, by: str | None = None) -> ApprovalRequest:
        return self._decide(request_id, ApprovalStatus.REJECTED, by)

    def _decide(
        self, request_id: str, status: ApprovalStatus, by: str | None
    ) -> ApprovalRequest:
        req = self._requests.get(request_id)
        if req is None:
            raise KeyError(f"No such approval request: {request_id}")
        if req.status != ApprovalStatus.PENDING:
            raise ValueError(f"Request {request_id} already {req.status}")
        req.status = status
        req.decided_by = by
        return req

    def pending(self) -> list[ApprovalRequest]:
        return [
            r for r in self._requests.values() if r.status == ApprovalStatus.PENDING
        ]
