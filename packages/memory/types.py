"""Memory data types: the four memory scopes and the MemoryItem record.

Scopes (from the Phase 4 design):
- SESSION    one conversation; ephemeral.
- PROJECT    a project's facts; persists forever.
- USER       a user's preferences; persists forever.
- KNOWLEDGE  documents (README, RFCs, …); searchable.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class MemoryScope(StrEnum):
    SESSION = "session"
    PROJECT = "project"
    USER = "user"
    KNOWLEDGE = "knowledge"


class MemoryItem(BaseModel):
    """A single piece of memory plus the signals used to score it."""

    scope: MemoryScope
    key: str
    value: str
    # Owner identifiers (which session/project/user this belongs to).
    session_id: str | None = None
    project_id: str | None = None
    user_id: str | None = None
    # Scoring signals.
    importance: float = 1.0  # caller-assigned 0..1+
    usage_count: int = 0
    # Logical timestamps (monotonic counter, not wall-clock — testable).
    created_tick: int = 0
    last_used_tick: int = 0
    metadata: dict = Field(default_factory=dict)
