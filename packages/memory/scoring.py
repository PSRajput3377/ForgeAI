"""Memory scoring — rank memories by value so the Context Builder picks the best.

Score combines four signals from the Phase 4 design: recency, importance, usage
frequency, and project relevance. Recency uses a logical "tick" clock (a
monotonic counter) so scoring is deterministic and testable — no wall-clock.
"""

from __future__ import annotations

import math

from memory.types import MemoryItem


def score_memory(
    item: MemoryItem,
    *,
    now_tick: int,
    current_project_id: str | None = None,
    recency_halflife: float = 50.0,
) -> float:
    """Return a value score for a memory item (higher = more valuable)."""
    # Recency: exponential decay on ticks since last use.
    age = max(0, now_tick - item.last_used_tick)
    recency = math.exp(-age / recency_halflife)

    # Usage frequency: diminishing returns.
    frequency = math.log1p(item.usage_count)

    # Project relevance: bonus if it belongs to the active project.
    relevance = 1.0
    if current_project_id and item.project_id == current_project_id:
        relevance = 1.5

    return (item.importance + frequency) * recency * relevance


def rank_memories(
    items: list[MemoryItem],
    *,
    now_tick: int,
    current_project_id: str | None = None,
    limit: int | None = None,
) -> list[MemoryItem]:
    """Return items sorted by descending score, optionally truncated."""
    ranked = sorted(
        items,
        key=lambda it: score_memory(
            it, now_tick=now_tick, current_project_id=current_project_id
        ),
        reverse=True,
    )
    return ranked[:limit] if limit else ranked
