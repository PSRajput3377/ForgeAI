"""Evaluation store — append-only log of run scores, behind one interface.

Phase 12.1 shipped the in-memory store; 12.2 adds the PostgreSQL-backed store
(``apps/api/app/performance.py``) behind the same shape, exactly as
``observability/store.py`` did for events (ADR-0017, ADR-0025).

Per spec §2, per-agent aggregates are *derived* (via ``evaluation.stats``),
never stored as an independent writable source of truth that could drift from
the records. Both stores call the same pure aggregation functions.
"""

from __future__ import annotations

from evaluation.stats import Stats, aggregate, by_prompt_version
from evaluation.types import Evaluation


class EvaluationStore:
    """Append-only store of ``Evaluation`` records with comparison queries."""

    def __init__(self) -> None:
        self._evals: list[Evaluation] = []

    def add(self, evaluation: Evaluation) -> None:
        self._evals.append(evaluation)

    def all(self) -> list[Evaluation]:
        return list(self._evals)

    def for_run(self, run_id: str) -> Evaluation | None:
        """The most recent evaluation recorded for a run, if any."""
        for evaluation in reversed(self._evals):
            if evaluation.run_id == run_id:
                return evaluation
        return None

    # --- derived aggregates (spec §2) ---------------------------------------

    def stats(self) -> Stats:
        """Rollup across all records."""
        return aggregate(self._evals)

    def prompt_version_stats(self, role: str) -> dict[str, Stats]:
        """Stats grouped by the prompt version ``role`` used."""
        return by_prompt_version(self._evals, role)

    def mean_score(self) -> float:
        return self.stats().mean_score

    def success_rate(self) -> float:
        return self.stats().success_rate

    def by_prompt_version(self, role: str, version: str) -> list[Evaluation]:
        """Records where ``role`` ran a given prompt version (for 12.3/12.8)."""
        return [e for e in self._evals if e.prompt_versions.get(role) == version]
