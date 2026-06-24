"""Multi-agent parallelism — split a task, run sub-agents concurrently, merge.

    Planner → task split → [Frontend | Backend | Database] → merge

A big performance gain for independent sub-tasks. Bounded concurrency protects
the worker pool; a failing branch is captured, not allowed to sink the others.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable

from pydantic import BaseModel, Field


class SubTask(BaseModel):
    id: str
    description: str
    lane: str = "general"  # frontend | backend | database | ...


class SubResult(BaseModel):
    id: str
    lane: str
    success: bool
    output: dict = Field(default_factory=dict)
    error: str = ""


async def run_parallel(
    subtasks: list[SubTask],
    runner: Callable[[SubTask], Awaitable[dict]],
    *,
    concurrency: int = 4,
) -> list[SubResult]:
    """Run ``runner`` over subtasks concurrently (bounded), capturing failures."""
    sem = asyncio.Semaphore(concurrency)

    async def one(st: SubTask) -> SubResult:
        async with sem:
            try:
                output = await runner(st)
                return SubResult(id=st.id, lane=st.lane, success=True, output=output)
            except Exception as exc:  # noqa: BLE001 - isolate per-branch failures
                return SubResult(id=st.id, lane=st.lane, success=False, error=str(exc))

    return await asyncio.gather(*(one(st) for st in subtasks))


def merge_results(results: list[SubResult]) -> dict:
    """Merge sub-results into a single summary (the 'merge' step)."""
    return {
        "total": len(results),
        "succeeded": sum(r.success for r in results),
        "failed": sum(not r.success for r in results),
        "by_lane": {r.lane: r.success for r in results},
        "outputs": {r.id: r.output for r in results if r.success},
        "errors": {r.id: r.error for r in results if not r.success},
    }
