"""Integration status endpoint (Phase 13.6) — honest readiness, never overstated.

Surfaces each connector's mode (``simulated`` = interface-complete, validated
against an in-memory fake; ``live`` = talks to the real system) so the UI and
docs can show capability truthfully (spec §6). GitHub's provider mode is
reported alongside, since it has a real live path.
"""

from __future__ import annotations

from fastapi import APIRouter
from integrations import build_default_hub

from app.github_runtime import github_configured

router = APIRouter(prefix="/integrations", tags=["integrations"])

# Built once; connectors are stateless w.r.t. status.
_hub = build_default_hub()


@router.get("/status")
def status() -> dict:
    """Per-integration mode + capabilities, plus the GitHub provider mode."""
    return {
        "github_mode": "live" if github_configured() else "fake",
        "connectors": _hub.status(),
    }
