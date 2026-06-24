"""Auth dependencies: current user, role guards, and workspace isolation.

These are the route guards: `Auth Required` (current_user), `Role Only`
(require_role), and `Workspace Isolation` (require_workspace_role) — a user
cannot touch a workspace they aren't a member of.
"""

from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.revocation import denylist
from app.auth.security import decode_token
from app.db.base import get_session
from app.db.models import ROLE_RANK, Membership, Role, User

_bearer = HTTPBearer(auto_error=False)


async def current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
    session: AsyncSession = Depends(get_session),
) -> User:
    """Resolve the authenticated user from the bearer access token."""
    if creds is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")
    token = creds.credentials
    if await denylist.is_revoked(token):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token revoked")
    try:
        payload = decode_token(token, expected_type="access")
    except ValueError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, str(exc)) from exc

    user = await session.get(User, payload["sub"])
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found")
    return user


async def require_workspace_role(
    workspace_id: str,
    minimum: Role,
    user: User,
    session: AsyncSession,
) -> Membership:
    """Ensure ``user`` belongs to ``workspace_id`` with at least ``minimum`` role.

    Enforces workspace isolation: non-members get 403, not 404-leak.
    """
    result = await session.execute(
        select(Membership).where(
            Membership.user_id == user.id,
            Membership.workspace_id == workspace_id,
        )
    )
    membership = result.scalar_one_or_none()
    if membership is None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not a member of this workspace")
    if ROLE_RANK[Role(membership.role)] < ROLE_RANK[minimum]:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            f"Requires at least '{minimum}' role",
        )
    return membership
