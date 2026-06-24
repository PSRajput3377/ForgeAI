"""ORM models for auth, multi-tenancy, collaboration, and governance.

Hierarchy (Phase 7):
    Organization → Workspace → Project → (Task → Run, Memory)
    User —(Membership: role)→ Workspace

RBAC roles live on Membership. Approvals, invitations, comments, activity, and
audit records support governance and collaboration.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import StrEnum

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def _uuid() -> str:
    return uuid.uuid4().hex


def _now() -> datetime:
    return datetime.now(UTC)


class Role(StrEnum):
    """RBAC roles, ordered by privilege (owner highest)."""

    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


# Privilege ranking for "at least this role" checks.
ROLE_RANK = {Role.VIEWER: 0, Role.MEMBER: 1, Role.ADMIN: 2, Role.OWNER: 3}


class ApprovalStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now
    )


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    password_hash: Mapped[str] = mapped_column(String(255))
    avatar: Mapped[str | None] = mapped_column(String(512), nullable=True)

    memberships: Mapped[list[Membership]] = relationship(back_populates="user")


class Organization(Base, TimestampMixin):
    __tablename__ = "organizations"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(255))
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id"))

    workspaces: Mapped[list[Workspace]] = relationship(back_populates="organization")


class Workspace(Base, TimestampMixin):
    __tablename__ = "workspaces"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"))
    name: Mapped[str] = mapped_column(String(255))

    organization: Mapped[Organization] = relationship(back_populates="workspaces")
    memberships: Mapped[list[Membership]] = relationship(back_populates="workspace")
    projects: Mapped[list[Project]] = relationship(back_populates="workspace")


class Membership(Base, TimestampMixin):
    """A user's role within a workspace (the RBAC join)."""

    __tablename__ = "memberships"
    __table_args__ = (UniqueConstraint("user_id", "workspace_id", name="uq_user_workspace"),)

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id"))
    role: Mapped[Role] = mapped_column(String(16), default=Role.MEMBER)

    user: Mapped[User] = relationship(back_populates="memberships")
    workspace: Mapped[Workspace] = relationship(back_populates="memberships")


class Project(Base, TimestampMixin):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id"))
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    workspace: Mapped[Workspace] = relationship(back_populates="projects")


class Invitation(Base, TimestampMixin):
    """Invite-code based workspace invitation (no email for the MVP)."""

    __tablename__ = "invitations"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id"))
    email: Mapped[str] = mapped_column(String(255))
    role: Mapped[Role] = mapped_column(String(16), default=Role.MEMBER)
    token: Mapped[str] = mapped_column(String(64), unique=True, index=True, default=_uuid)
    accepted: Mapped[bool] = mapped_column(default=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class Approval(Base, TimestampMixin):
    """A governance approval request (delete/push/deploy)."""

    __tablename__ = "approvals"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id"))
    action: Mapped[str] = mapped_column(String(64))
    requested_by: Mapped[str] = mapped_column(ForeignKey("users.id"))
    approved_by: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    status: Mapped[ApprovalStatus] = mapped_column(String(16), default=ApprovalStatus.PENDING)


class PRApproval(Base, TimestampMixin):
    """A persisted GitHub PR approval request.

    Stores the full PR plan + repo so a proposal survives a restart and can be
    approved/executed later by id alone. (Initially in-memory for rapid
    iteration; persisted here for durability — ADR-0024.)
    """

    __tablename__ = "pr_approvals"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    status: Mapped[ApprovalStatus] = mapped_column(String(16), default=ApprovalStatus.PENDING)
    repository: Mapped[str] = mapped_column(String(255))  # "owner/name"
    owner: Mapped[str] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(255))
    pr_title: Mapped[str] = mapped_column(String(255))
    pr_plan: Mapped[dict] = mapped_column(JSON)  # serialized PRPlan
    pr_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    decided_by: Mapped[str | None] = mapped_column(String(255), nullable=True)


class Activity(Base, TimestampMixin):
    """Activity-feed / audit record (who did what, where)."""

    __tablename__ = "activity"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id"), index=True)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(128))
    detail: Mapped[str] = mapped_column(Text, default="")


class Comment(Base, TimestampMixin):
    """A comment on a project (task-level threads build on this)."""

    __tablename__ = "comments"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    body: Mapped[str] = mapped_column(Text)


class EvaluationRecord(Base, TimestampMixin):
    """A persisted run score (Phase 12.2 — the ``evaluations`` table).

    One row per scored run, mirroring the ``evaluation.Evaluation`` pydantic
    model. Per-agent aggregates are *derived* from these rows at read time
    (``evaluation.stats``), never stored separately — so they can't drift
    (ADR-0025, spec §2). ``pr_accepted`` is nullable: backfilled when a PR's
    outcome is known (spec §10).
    """

    __tablename__ = "evaluations"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    run_id: Mapped[str] = mapped_column(String(64), index=True)
    task: Mapped[str] = mapped_column(Text)

    success: Mapped[bool] = mapped_column(Boolean)
    tests_passed: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    review_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    retries: Mapped[int] = mapped_column(Integer, default=0)

    execution_time_s: Mapped[float] = mapped_column(Float, default=0.0)
    tokens: Mapped[int] = mapped_column(Integer, default=0)

    prompt_versions: Mapped[dict] = mapped_column(JSON, default=dict)
    model_routing: Mapped[dict] = mapped_column(JSON, default=dict)

    pr_accepted: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    score: Mapped[float] = mapped_column(Float)
    rubric_version: Mapped[str] = mapped_column(String(16))


class FailureRecord(Base, TimestampMixin):
    """A persisted Failure Knowledge Base entry (Phase 12.4 — the ``failures``
    table). Error → cause → fix → outcome, keyed by a normalized signature so
    recurring errors collide on one entry (spec §4, §7)."""

    __tablename__ = "failures"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    signature: Mapped[str] = mapped_column(String(128), index=True)
    error: Mapped[str] = mapped_column(Text)
    cause: Mapped[str] = mapped_column(Text, default="")
    fix: Mapped[str] = mapped_column(Text, default="")
    outcome: Mapped[str] = mapped_column(String(16), default="unknown")
    hits: Mapped[int] = mapped_column(Integer, default=1)


class BenchmarkRun(Base, TimestampMixin):
    """A persisted benchmark report (Phase 12.5 — the ``benchmark_results``
    table). One row per suite run, tagged with the ForgeAI + suite version so
    successive versions are comparable (spec §5). The full report (per-scenario
    results + stats) is stored as JSON; ``pass_rate`` is denormalized for
    cheap trend queries."""

    __tablename__ = "benchmark_results"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    forge_version: Mapped[str] = mapped_column(String(64), index=True)
    suite_version: Mapped[str] = mapped_column(String(16))
    pass_rate: Mapped[float] = mapped_column(Float)
    report: Mapped[dict] = mapped_column(JSON)  # serialized BenchmarkReport
