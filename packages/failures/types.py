"""The Failure record — one entry in the Failure Knowledge Base (spec §4, §7).

Error → Cause → Fix → Outcome. Keyed by a normalized ``signature`` so recurring
errors collide on one entry. ``outcome`` records whether the stored fix actually
worked, so a fix that later fails can be demoted (no fix is trusted forever).
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class Outcome(StrEnum):
    """Whether a stored fix resolved the failure when applied."""

    RESOLVED = "resolved"  # fix worked
    FAILED = "failed"  # fix was applied but the run still failed
    UNKNOWN = "unknown"  # proposed, outcome not yet observed


class Failure(BaseModel):
    """A single error→fix episode in the knowledge base."""

    signature: str
    error: str  # the raw error text (first observation)
    cause: str = ""  # diagnosed root cause
    fix: str = ""  # the proposed/applied fix
    outcome: Outcome = Outcome.UNKNOWN
    hits: int = Field(default=1)  # times this signature has been seen
