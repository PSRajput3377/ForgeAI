"""Durable PR-approval store (PostgreSQL via the async DB layer).

Initially PR approvals lived in process memory for rapid iteration; this moves
them into the database so a proposal survives a restart and can be approved /
executed later by id alone (ADR-0024). The full PRPlan is serialized into a JSON
column, so execute() needs only the approval id.

Same async-SQLAlchemy backend as the rest of the app: PostgreSQL in production,
SQLite in tests (ADR-0018).
"""

from __future__ import annotations

from github.workflow import PRPlan
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ApprovalStatus, PRApproval


class PRApprovalStore:
    """CRUD + state transitions for persisted PR approvals."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, owner: str, name: str, plan: PRPlan) -> PRApproval:
        row = PRApproval(
            status=ApprovalStatus.PENDING,
            repository=f"{owner}/{name}",
            owner=owner,
            name=name,
            pr_title=plan.pr_title,
            pr_plan=plan.model_dump(),
        )
        self.session.add(row)
        await self.session.commit()
        await self.session.refresh(row)
        return row

    async def get(self, approval_id: str) -> PRApproval | None:
        return await self.session.get(PRApproval, approval_id)

    async def pending(self) -> list[PRApproval]:
        result = await self.session.execute(
            select(PRApproval)
            .where(PRApproval.status == ApprovalStatus.PENDING)
            .order_by(PRApproval.created_at)
        )
        return list(result.scalars().all())

    async def decide(self, approval_id: str, status: ApprovalStatus, by: str | None) -> PRApproval:
        row = await self.session.get(PRApproval, approval_id)
        if row is None:
            raise KeyError(approval_id)
        # SQLite returns the column as a plain str; coerce before comparing.
        if ApprovalStatus(row.status) != ApprovalStatus.PENDING:
            raise ValueError(f"already {row.status}")
        row.status = status
        row.decided_by = by
        await self.session.commit()
        await self.session.refresh(row)
        return row

    async def set_pr_url(self, approval_id: str, url: str) -> None:
        row = await self.session.get(PRApproval, approval_id)
        if row is not None:
            row.pr_url = url
            await self.session.commit()

    @staticmethod
    def plan_of(row: PRApproval) -> PRPlan:
        return PRPlan.model_validate(row.pr_plan)
