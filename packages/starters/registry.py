"""Starter registry — discoverable, versioned scaffolds (Phase 13.3).

Maps a starter id to its metadata + a deterministic builder. ``SUITE_VERSION``
bumps when the set changes, so a project records which starter version produced
it. New starters are added here; nothing else changes.
"""

from __future__ import annotations

from collections.abc import Callable

from pydantic import BaseModel

from starters.templates import empty_starter, fastapi_saas_starter

STARTERS_VERSION = "v1"


class StarterInfo(BaseModel):
    """User-facing metadata for a starter (what the chooser shows)."""

    id: str
    name: str
    description: str
    tags: list[str] = []


# id -> (info, builder)
STARTERS: dict[str, tuple[StarterInfo, Callable[[], dict[str, str]]]] = {
    "empty": (
        StarterInfo(
            id="empty",
            name="Empty project",
            description="A blank project — just a README. Start from scratch.",
            tags=["minimal"],
        ),
        empty_starter,
    ),
    "fastapi-saas": (
        StarterInfo(
            id="fastapi-saas",
            name="FastAPI SaaS starter",
            description="FastAPI with JWT auth, PostgreSQL, Docker, and tests.",
            tags=["backend", "fastapi", "jwt", "postgres", "docker"],
        ),
        fastapi_saas_starter,
    ),
}


def list_starters() -> list[StarterInfo]:
    """All available starters (for the project chooser)."""
    return [info for info, _ in STARTERS.values()]


def get_starter(starter_id: str) -> dict[str, str]:
    """The file set for a starter id. Raises KeyError if unknown."""
    if starter_id not in STARTERS:
        raise KeyError(f"unknown starter '{starter_id}'")
    _, builder = STARTERS[starter_id]
    return builder()
