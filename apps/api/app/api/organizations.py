"""Multi-tenant endpoints: organizations, workspaces, invitations, members, activity.

Demonstrates the full RBAC + workspace-isolation model: creating an org makes
the creator its OWNER; only admins+ can invite; members are isolated to their
own workspaces.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import current_user, require_workspace_role
from app.db.base import get_session
from app.db.models import (
    Activity,
    Invitation,
    Membership,
    Organization,
    Role,
    User,
    Workspace,
)

router = APIRouter(prefix="/orgs", tags=["organizations"])


def _slugify(name: str) -> str:
    return "".join(c if c.isalnum() else "-" for c in name.lower()).strip("-")


class CreateOrg(BaseModel):
    name: str


class CreateWorkspace(BaseModel):
    name: str


class InviteRequest(BaseModel):
    email: str
    role: Role = Role.MEMBER


class AcceptInvite(BaseModel):
    token: str


async def _log(
    session: AsyncSession,
    workspace_id: str,
    user_id: str,
    action: str,
    detail: str = "",
):
    session.add(Activity(workspace_id=workspace_id, user_id=user_id, action=action, detail=detail))


@router.post("", status_code=201)
async def create_org(
    body: CreateOrg,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Create an organization with a default workspace; creator becomes OWNER."""
    org = Organization(name=body.name, slug=_slugify(body.name), owner_id=user.id)
    session.add(org)
    await session.flush()
    workspace = Workspace(organization_id=org.id, name="Default")
    session.add(workspace)
    await session.flush()
    session.add(Membership(user_id=user.id, workspace_id=workspace.id, role=Role.OWNER))
    await _log(session, workspace.id, user.id, "org.created", body.name)
    await session.commit()
    return {"organization_id": org.id, "workspace_id": workspace.id}


@router.post("/{org_id}/workspaces", status_code=201)
async def create_workspace(
    org_id: str,
    body: CreateWorkspace,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    org = await session.get(Organization, org_id)
    if org is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Organization not found")
    if org.owner_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only the org owner can add workspaces")
    workspace = Workspace(organization_id=org_id, name=body.name)
    session.add(workspace)
    await session.flush()
    session.add(Membership(user_id=user.id, workspace_id=workspace.id, role=Role.OWNER))
    await session.commit()
    return {"workspace_id": workspace.id}


@router.post("/workspaces/{workspace_id}/invite", status_code=201)
async def invite(
    workspace_id: str,
    body: InviteRequest,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Create an invite code. Requires ADMIN+ in the workspace."""
    await require_workspace_role(workspace_id, Role.ADMIN, user, session)
    inv = Invitation(
        workspace_id=workspace_id,
        email=body.email,
        role=body.role,
        expires_at=datetime.now(UTC) + timedelta(days=7),
    )
    session.add(inv)
    await _log(session, workspace_id, user.id, "member.invited", body.email)
    await session.commit()
    return {"invite_token": inv.token, "role": inv.role}


@router.post("/invite/accept", status_code=201)
async def accept_invite(
    body: AcceptInvite,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    result = await session.execute(select(Invitation).where(Invitation.token == body.token))
    inv = result.scalar_one_or_none()
    if inv is None or inv.accepted:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Invalid or used invite")
    # SQLite returns naive datetimes; coerce to UTC-aware before comparing.
    expires_at = inv.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    if expires_at < datetime.now(UTC):
        raise HTTPException(status.HTTP_410_GONE, "Invite expired")
    # Avoid duplicate membership.
    existing = await session.execute(
        select(Membership).where(
            Membership.user_id == user.id, Membership.workspace_id == inv.workspace_id
        )
    )
    if existing.scalar_one_or_none() is None:
        session.add(Membership(user_id=user.id, workspace_id=inv.workspace_id, role=inv.role))
    inv.accepted = True
    await _log(session, inv.workspace_id, user.id, "member.joined", user.email)
    await session.commit()
    return {"workspace_id": inv.workspace_id, "role": inv.role}


@router.get("/workspaces/{workspace_id}/members")
async def members(
    workspace_id: str,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    await require_workspace_role(workspace_id, Role.VIEWER, user, session)
    result = await session.execute(
        select(Membership, User)
        .join(User, User.id == Membership.user_id)
        .where(Membership.workspace_id == workspace_id)
    )
    return {
        "members": [
            {"user_id": u.id, "email": u.email, "name": u.name, "role": m.role}
            for m, u in result.all()
        ]
    }


@router.get("/workspaces/{workspace_id}/activity")
async def activity(
    workspace_id: str,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Activity feed for a workspace (GitHub-style)."""
    await require_workspace_role(workspace_id, Role.VIEWER, user, session)
    result = await session.execute(
        select(Activity).where(Activity.workspace_id == workspace_id).order_by(Activity.created_at)
    )
    return {
        "activity": [
            {"action": a.action, "detail": a.detail, "user_id": a.user_id}
            for a in result.scalars().all()
        ]
    }
