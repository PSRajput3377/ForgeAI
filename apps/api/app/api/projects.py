"""Project endpoints (Phase 13.1) — first-class projects that own a workspace.

CRUD over projects, scoped to the caller's workspace via the existing RBAC
(auth-spec): you only see and manage projects in workspaces you belong to.
Creating a project provisions its on-disk workspace directory; the agent
pipeline (13.2) runs against that path.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from starters import list_starters

from app.auth.deps import current_user, require_workspace_role
from app.db.base import get_session
from app.db.models import Project, Role, User
from app.projects import ProjectService

router = APIRouter(prefix="/projects", tags=["projects"])


class CreateProject(BaseModel):
    workspace_id: str
    name: str
    description: str | None = None
    starter: str | None = None  # used by bootstrap (13.3); plain create ignores it


class BootstrapProject(BaseModel):
    workspace_id: str
    name: str
    starter: str  # the starter id to scaffold from
    description: str | None = None


def _view(p: Project) -> dict:
    return {
        "id": p.id,
        "workspace_id": p.workspace_id,
        "name": p.name,
        "description": p.description,
        "path": p.path,
        "repo": p.repo,
        "starter": p.starter,
    }


async def _owned_project(
    project_id: str, user: User, session: AsyncSession, minimum: Role = Role.VIEWER
) -> Project:
    """Load a project and enforce that the caller belongs to its workspace."""
    svc = ProjectService(session)
    project = await svc.get(project_id)
    if project is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found")
    await require_workspace_role(project.workspace_id, minimum, user, session)
    return project


@router.post("", status_code=201)
async def create_project(
    body: CreateProject,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Create a project (and its workspace dir). Requires MEMBER+ in the workspace."""
    await require_workspace_role(body.workspace_id, Role.MEMBER, user, session)
    project = await ProjectService(session).create(
        workspace_id=body.workspace_id,
        name=body.name,
        description=body.description,
        starter=body.starter,
    )
    return _view(project)


@router.get("/starters")
async def starters() -> dict:
    """List available project starters (for the chooser). Public metadata."""
    return {"starters": [s.model_dump() for s in list_starters()]}


@router.post("/bootstrap", status_code=201)
async def bootstrap_project(
    body: BootstrapProject,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Create a project and scaffold it from a starter template (Phase 13.3).

    Deterministic + offline; the scaffolded project is then ready for the agent
    pipeline. Requires MEMBER+ in the workspace.
    """
    await require_workspace_role(body.workspace_id, Role.MEMBER, user, session)
    svc = ProjectService(session)
    project = await svc.create(
        workspace_id=body.workspace_id,
        name=body.name,
        description=body.description,
        starter=body.starter,
    )
    try:
        written = svc.scaffold(project, body.starter)
    except KeyError:
        # Unknown starter — roll back the just-created project + dir.
        await svc.delete(project)
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, f"Unknown starter '{body.starter}'"
        ) from None
    out = _view(project)
    out["scaffolded_files"] = written
    return out


@router.get("")
async def list_projects(
    workspace_id: str,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """List projects in a workspace the caller belongs to."""
    await require_workspace_role(workspace_id, Role.VIEWER, user, session)
    projects = await ProjectService(session).list_for_workspace(workspace_id)
    return {"projects": [_view(p) for p in projects]}


@router.get("/{project_id}")
async def get_project(
    project_id: str,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    project = await _owned_project(project_id, user, session)
    return _view(project)


@router.delete("/{project_id}")
async def delete_project(
    project_id: str,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Delete a project and its workspace dir. Requires ADMIN+ in the workspace."""
    project = await _owned_project(project_id, user, session, minimum=Role.ADMIN)
    await ProjectService(session).delete(project)
    return {"deleted": project_id}
