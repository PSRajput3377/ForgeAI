"""Structured agent communication contracts.

Agents never exchange raw prompts. They pass typed, validated messages so the
system stays reliable and inspectable. Two shapes matter:

- ``TaskSpec``      a unit of work the Planner produces and the Manager routes.
- ``AgentMessage``  the envelope an agent returns when it finishes a task.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from uuid import uuid4

from pydantic import BaseModel, Field

from core.roles import AgentRole


def _new_id() -> str:
    return uuid4().hex


def _now() -> datetime:
    return datetime.now(UTC)


class MessageStatus(StrEnum):
    """Lifecycle of a task/message."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class Priority(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class TaskSpec(BaseModel):
    """A single executable task. Produced by the Planner, routed by the Manager.

    Mirrors the contract from the Phase 2 design:
        {"task_id": "123", "title": "Create Login API",
         "priority": "high", "status": "pending"}
    """

    task_id: str = Field(default_factory=_new_id)
    title: str
    description: str = ""
    assigned_to: AgentRole | None = None
    priority: Priority = Priority.MEDIUM
    status: MessageStatus = MessageStatus.PENDING


class AgentMessage(BaseModel):
    """The envelope an agent returns to the Manager when it finishes work.

    Mirrors the contract from the Phase 2 design:
        {"task_id": "123", "status": "completed",
         "files_changed": ["auth.py", "routes.py"]}
    """

    task_id: str
    sender: AgentRole
    status: MessageStatus
    summary: str = ""
    files_changed: list[str] = Field(default_factory=list)
    # Free-form structured payload for role-specific data (logs, docs, etc.).
    payload: dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=_now)
