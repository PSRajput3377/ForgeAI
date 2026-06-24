"""Evaluation store — append-only log of run scores, behind one interface.

Phase 12.1 ships the in-memory store (offline-testable); the PostgreSQL-backed
store (the ``evaluations`` table, sub-phase 12.2) lands behind the same shape,
exactly as ``observability/store.py`` did for events (ADR-0017).

Per spec §2, per-agent aggregates are *derived* here, never stored as an
independent writable source of truth that could drift from the records.
"""

from __future__ import annotations

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

    def mean_score(self) -> float:
        """Average score across all records (0.0 when empty)."""
        return (sum(e.score for e in self._evals) / len(self._evals)) if self._evals else 0.0

    def success_rate(self) -> float:
        """Fraction of runs that succeeded (0.0 when empty)."""
        if not self._evals:
            return 0.0
        return sum(1 for e in self._evals if e.success) / len(self._evals)

    def by_prompt_version(self, role: str, version: str) -> list[Evaluation]:
        """Records where ``role`` ran a given prompt version (for 12.3/12.8)."""
        return [e for e in self._evals if e.prompt_versions.get(role) == version]
