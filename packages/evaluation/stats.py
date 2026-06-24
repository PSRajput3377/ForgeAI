"""Derived aggregates over Evaluation records (spec §2).

Per-agent / per-prompt-version stats are *computed* from the records here, never
stored as an independent writable source of truth that could drift. Both the
in-memory store and the PostgreSQL-backed store (12.2) call these pure functions
on the same records, so they agree by construction.
"""

from __future__ import annotations

from pydantic import BaseModel

from evaluation.types import Evaluation


class Stats(BaseModel):
    """A derived rollup over a set of runs."""

    runs: int = 0
    success_rate: float = 0.0
    mean_score: float = 0.0
    avg_retries: float = 0.0
    avg_time_s: float = 0.0
    # None when no PR outcome has been recorded yet (pr_accepted all null).
    accepted_pr_rate: float | None = None


def aggregate(evals: list[Evaluation]) -> Stats:
    """Roll a list of evaluations up into one ``Stats`` (empty → zeros)."""
    n = len(evals)
    if n == 0:
        return Stats()

    decided = [e for e in evals if e.pr_accepted is not None]
    accepted_pr_rate = sum(1 for e in decided if e.pr_accepted) / len(decided) if decided else None

    return Stats(
        runs=n,
        success_rate=sum(1 for e in evals if e.success) / n,
        mean_score=round(sum(e.score for e in evals) / n, 4),
        avg_retries=round(sum(e.retries for e in evals) / n, 4),
        avg_time_s=round(sum(e.execution_time_s for e in evals) / n, 4),
        accepted_pr_rate=accepted_pr_rate,
    )


def by_prompt_version(evals: list[Evaluation], role: str) -> dict[str, Stats]:
    """Stats grouped by the prompt version ``role`` used — powers prompt
    comparison (12.8). Runs where the role recorded no version are skipped."""
    groups: dict[str, list[Evaluation]] = {}
    for e in evals:
        version = e.prompt_versions.get(role)
        if version is not None:
            groups.setdefault(version, []).append(e)
    return {version: aggregate(group) for version, group in groups.items()}
