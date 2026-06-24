"""Performance database — durable, queryable run scores (Phase 12.2).

The PostgreSQL-backed counterpart to ``evaluation.EvaluationStore``: it persists
``Evaluation`` records and answers the same comparison queries, so the analytics
dashboard (12.8) and benchmarks (12.5) read from a durable source.

Per-agent / per-prompt-version aggregates are *derived* from the rows via the
same pure functions the in-memory store uses (``evaluation.stats``), so the two
back-ends agree by construction and the rollup can never drift from the records
(ADR-0025, spec §2).

Same async-SQLAlchemy backend as the rest of the app: PostgreSQL in production,
SQLite in tests (ADR-0018).
"""

from __future__ import annotations

from evaluation import Evaluation, Stats, aggregate, by_prompt_version
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import EvaluationRecord

# Columns shared 1:1 between the ORM row and the pydantic model.
_FIELDS = (
    "run_id",
    "task",
    "success",
    "tests_passed",
    "review_score",
    "retries",
    "execution_time_s",
    "tokens",
    "prompt_versions",
    "model_routing",
    "pr_accepted",
    "score",
    "rubric_version",
)


def _to_model(row: EvaluationRecord) -> Evaluation:
    return Evaluation(**{f: getattr(row, f) for f in _FIELDS})


class PerformanceStore:
    """CRUD + derived aggregates for persisted evaluation records."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, evaluation: Evaluation) -> EvaluationRecord:
        row = EvaluationRecord(**evaluation.model_dump())
        self.session.add(row)
        await self.session.commit()
        await self.session.refresh(row)
        return row

    async def all(self) -> list[Evaluation]:
        result = await self.session.execute(
            select(EvaluationRecord).order_by(EvaluationRecord.created_at)
        )
        return [_to_model(r) for r in result.scalars().all()]

    async def for_run(self, run_id: str) -> Evaluation | None:
        """The most recent evaluation recorded for a run, if any."""
        result = await self.session.execute(
            select(EvaluationRecord)
            .where(EvaluationRecord.run_id == run_id)
            .order_by(EvaluationRecord.created_at.desc())
            .limit(1)
        )
        row = result.scalars().first()
        return _to_model(row) if row else None

    async def set_pr_accepted(self, run_id: str, accepted: bool) -> bool:
        """Backfill the PR outcome for a run (spec §10). Returns True if updated."""
        result = await self.session.execute(
            select(EvaluationRecord).where(EvaluationRecord.run_id == run_id)
        )
        rows = list(result.scalars().all())
        for row in rows:
            row.pr_accepted = accepted
        if rows:
            await self.session.commit()
        return bool(rows)

    # --- derived aggregates (spec §2; same functions as the in-memory store) -

    async def stats(self) -> Stats:
        return aggregate(await self.all())

    async def prompt_version_stats(self, role: str) -> dict[str, Stats]:
        return by_prompt_version(await self.all(), role)
