"""Durable Failure Knowledge Base (PostgreSQL via the async DB layer).

The persistent counterpart to ``failures.FailureStore``: same record/reuse
contract (record an error→fix episode, recall the best known fix for a
signature), backed by the ``failures`` table so the KB survives restarts and is
shared across runs and replicas (spec §4, §7).

Reuse policy matches the in-memory store: ``recall`` prefers a RESOLVED fix,
else the most-seen non-failed candidate; a fix that later fails is recorded as a
new FAILED outcome so the KB self-corrects.

Same async-SQLAlchemy backend as the rest of the app: PostgreSQL in production,
SQLite in tests (ADR-0018).
"""

from __future__ import annotations

from failures import Failure, Outcome, error_signature
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import FailureRecord


def _to_model(row: FailureRecord) -> Failure:
    return Failure(
        signature=row.signature,
        error=row.error,
        cause=row.cause,
        fix=row.fix,
        outcome=Outcome(row.outcome),
        hits=row.hits,
    )


class FailureKB:
    """CRUD + reuse policy for the persisted Failure Knowledge Base."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def record(
        self,
        error: str,
        *,
        cause: str = "",
        fix: str = "",
        outcome: Outcome = Outcome.UNKNOWN,
    ) -> Failure:
        """Store an episode. Re-recording a (signature, fix) bumps hits and lets
        an observed outcome supersede UNKNOWN; a new distinct fix is appended."""
        sig = error_signature(error)
        result = await self.session.execute(
            select(FailureRecord).where(FailureRecord.signature == sig)
        )
        rows = list(result.scalars().all())

        for row in rows:
            if row.fix == fix:
                row.hits += 1
                if outcome is not Outcome.UNKNOWN:
                    row.outcome = outcome.value
                if cause and not row.cause:
                    row.cause = cause
                await self.session.commit()
                await self.session.refresh(row)
                return _to_model(row)

        row = FailureRecord(signature=sig, error=error, cause=cause, fix=fix, outcome=outcome.value)
        self.session.add(row)
        await self.session.commit()
        await self.session.refresh(row)
        return _to_model(row)

    async def recall(self, error: str) -> Failure | None:
        """Best known fix for an error's signature, or None if unseen/unfixed."""
        sig = error_signature(error)
        result = await self.session.execute(
            select(FailureRecord).where(FailureRecord.signature == sig)
        )
        rows = list(result.scalars().all())
        candidates = [r for r in rows if r.fix and Outcome(r.outcome) is not Outcome.FAILED]
        if not candidates:
            return None
        resolved = [r for r in candidates if Outcome(r.outcome) is Outcome.RESOLVED]
        pool = resolved or candidates
        return _to_model(max(pool, key=lambda r: r.hits))
