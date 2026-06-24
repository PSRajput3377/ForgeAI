"""Agent Analytics endpoints (Phase 12.8).

Surfaces the measurement substrate built in 12.1–12.7: per-agent stats with
deltas, prompt-version comparison, and the benchmark trend. Reads from the
durable PerformanceStore / BenchmarkStore (spec §2, §5, Dashboard).

Per spec §8 the *Promote* action a dashboard offers must be approval-gated and
never automatic; this router is read-only and exposes no promotion endpoint.
"""

from __future__ import annotations

from core.roles import AgentRole
from fastapi import APIRouter, Depends
from prompts import active_versions
from sqlalchemy.ext.asyncio import AsyncSession

from app.benchmark_store import BenchmarkStore
from app.db.base import get_session
from app.performance import PerformanceStore

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/overview")
async def overview(session: AsyncSession = Depends(get_session)) -> dict:
    """Aggregate run stats across all recorded evaluations."""
    stats = await PerformanceStore(session).stats()
    return stats.model_dump()


@router.get("/prompts/{role}")
async def prompt_comparison(role: str, session: AsyncSession = Depends(get_session)) -> dict:
    """Per-prompt-version stats for a role, plus which version is active.

    Powers the "v3 92% vs v4 95% → Promote v4" comparison. Promotion itself is
    an approval-gated action (spec §8), not offered here.
    """
    store = PerformanceStore(session)
    groups = await store.prompt_version_stats(role)
    try:
        active = active_versions().get(role)
    except Exception:
        active = None
    return {
        "role": role,
        "active_version": active,
        "versions": {version: stats.model_dump() for version, stats in groups.items()},
    }


@router.get("/prompts")
async def prompt_comparison_all(session: AsyncSession = Depends(get_session)) -> dict:
    """Prompt-version stats for every agent role (one call for the dashboard)."""
    store = PerformanceStore(session)
    active = active_versions()
    out: dict[str, dict] = {}
    for role in AgentRole:
        groups = await store.prompt_version_stats(role.value)
        if groups:
            out[role.value] = {
                "active_version": active.get(role.value),
                "versions": {v: s.model_dump() for v, s in groups.items()},
            }
    return {"roles": out}


@router.get("/benchmarks/trend")
async def benchmark_trend(session: AsyncSession = Depends(get_session)) -> dict:
    """Version-over-version benchmark pass-rate trend."""
    trend = await BenchmarkStore(session).trend()
    return {"trend": [{"forge_version": v, "pass_rate": rate} for v, rate in trend]}
