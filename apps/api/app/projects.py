"""Project service — a Project owns a workspace directory on disk (Phase 13.1).

Creating a project provisions ``<WORKSPACES_ROOT>/<project_id>``; deleting it
removes that directory. The path is *derived* from the id, never taken from the
client, so a project can only ever own its own folder under the configured root
(no traversal). A nullable ``repo`` on the model keeps a future git-backed mode
behind the same shape (spec §1).
"""

from __future__ import annotations

import shutil
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.models import Project


class ProjectService:
    """CRUD + on-disk workspace management for projects."""

    def __init__(self, session: AsyncSession, workspaces_root: str | None = None):
        self.session = session
        self.root = Path(workspaces_root or settings.workspaces_root).resolve()

    def _path_for(self, project_id: str) -> Path:
        """The workspace dir for a project — always under the root, derived from
        the id (never client-supplied), so it can't escape the root."""
        return (self.root / project_id).resolve()

    async def create(
        self,
        workspace_id: str,
        name: str,
        description: str | None = None,
        starter: str | None = None,
    ) -> Project:
        """Create a project row and provision its workspace directory."""
        project = Project(
            workspace_id=workspace_id, name=name, description=description, starter=starter
        )
        self.session.add(project)
        await self.session.flush()  # assign id
        path = self._path_for(project.id)
        # Confinement check: the resolved path must sit under the root.
        if self.root not in path.parents and path != self.root:
            raise ValueError("resolved project path escapes the workspaces root")
        path.mkdir(parents=True, exist_ok=True)
        project.path = str(path)
        await self.session.commit()
        await self.session.refresh(project)
        return project

    async def get(self, project_id: str) -> Project | None:
        return await self.session.get(Project, project_id)

    async def list_for_workspace(self, workspace_id: str) -> list[Project]:
        result = await self.session.execute(
            select(Project).where(Project.workspace_id == workspace_id).order_by(Project.created_at)
        )
        return list(result.scalars().all())

    async def delete(self, project: Project) -> None:
        """Remove the project row and its workspace directory."""
        if project.path:
            path = Path(project.path).resolve()
            # Only remove dirs that are genuinely under our root.
            if (self.root in path.parents) and path.exists():
                shutil.rmtree(path, ignore_errors=True)
        await self.session.delete(project)
        await self.session.commit()
