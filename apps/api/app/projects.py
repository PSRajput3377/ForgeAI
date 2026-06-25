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

    def scaffold(self, project: Project, starter_id: str) -> list[str]:
        """Scaffold a starter template into the project dir (Phase 13.3).

        Deterministic and offline. Refuses to scaffold into a non-empty project
        (never silently overwrites — spec §3). Returns the files written.
        """
        from starters import get_starter

        root = Path(project.path).resolve() if project.path else None
        if root is None:
            raise ValueError("project has no workspace path")
        existing = list(root.iterdir()) if root.exists() else []
        if existing:
            raise ValueError("project is not empty; refusing to scaffold over it")
        files = get_starter(starter_id)  # KeyError on unknown starter
        return self.write_files(project, files)

    def write_files(self, project: Project, files: dict[str, str]) -> list[str]:
        """Write generated files into the project's workspace dir (Phase 13.2).

        Each relative path is resolved under the project root and validated to
        stay inside it — a path that would escape (``..``, absolute) is skipped,
        never written. Returns the list of paths actually written.
        """
        if not project.path:
            return []
        root = Path(project.path).resolve()
        written: list[str] = []
        for rel, content in files.items():
            target = (root / rel).resolve()
            if root != target and root not in target.parents:
                continue  # path escapes the project dir — refuse it
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            written.append(rel)
        return written

    async def delete(self, project: Project) -> None:
        """Remove the project row and its workspace directory."""
        if project.path:
            path = Path(project.path).resolve()
            # Only remove dirs that are genuinely under our root.
            if (self.root in path.parents) and path.exists():
                shutil.rmtree(path, ignore_errors=True)
        await self.session.delete(project)
        await self.session.commit()
