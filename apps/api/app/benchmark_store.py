"""Durable benchmark-result store (PostgreSQL via the async DB layer).

Persists each ``BenchmarkReport`` so successive ForgeAI versions are comparable
over time (spec §5): the analytics dashboard (12.8) reads the latest report per
version and the trend across versions. The full report is stored as JSON;
``pass_rate`` is denormalized for cheap trend queries.

Same async-SQLAlchemy backend as the rest of the app: PostgreSQL in production,
SQLite in tests (ADR-0018).
"""

from __future__ import annotations

from benchmarks import BenchmarkReport
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import BenchmarkRun


class BenchmarkStore:
    """CRUD + comparison queries for persisted benchmark reports."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, report: BenchmarkReport) -> BenchmarkRun:
        row = BenchmarkRun(
            forge_version=report.forge_version,
            suite_version=report.suite_version,
            pass_rate=report.pass_rate,
            report=report.model_dump(),
        )
        self.session.add(row)
        await self.session.commit()
        await self.session.refresh(row)
        return row

    async def latest(self, forge_version: str) -> BenchmarkReport | None:
        """The most recent report for a version, if any."""
        result = await self.session.execute(
            select(BenchmarkRun)
            .where(BenchmarkRun.forge_version == forge_version)
            .order_by(BenchmarkRun.created_at.desc())
            .limit(1)
        )
        row = result.scalars().first()
        return BenchmarkReport.model_validate(row.report) if row else None

    async def trend(self) -> list[tuple[str, float]]:
        """(forge_version, pass_rate) for every stored report, oldest first —
        the version-over-version trend line."""
        result = await self.session.execute(select(BenchmarkRun).order_by(BenchmarkRun.created_at))
        return [(r.forge_version, r.pass_rate) for r in result.scalars().all()]
