"""LocalRepository — clone → branch → write → commit → push, via the git CLI.

Real engineers (and ForgeAI) work on a *local clone*, not GitHub REST endpoints
(ADR-0020). This authors commits with git, which integrates naturally with the
Docker sandbox, testing, reflection, review, and CI. The REST provider handles
only refs/PRs/reviews/checks.

Uses the Phase 3 FilesystemTool for sandboxed writes and runs git via asyncio
subprocess with the cwd confined to the clone.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

from pydantic import BaseModel
from tools.base import ToolInput
from tools.filesystem import FilesystemTool


class GitCommandError(RuntimeError):
    """A git command exited non-zero."""


class CommitResult(BaseModel):
    branch: str
    message: str
    pushed: bool = False


class LocalRepository:
    """A local git working copy ForgeAI commits to and pushes from."""

    def __init__(self, path: str | Path):
        self.path = Path(path).resolve()
        self.fs = FilesystemTool(self.path)

    async def _git(self, *args: str) -> tuple[int, str, str]:
        proc = await asyncio.create_subprocess_exec(
            "git",
            *args,
            cwd=str(self.path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        out, err = await proc.communicate()
        return (
            proc.returncode or 0,
            out.decode(errors="replace"),
            err.decode(errors="replace"),
        )

    async def _git_checked(self, *args: str) -> str:
        code, out, err = await self._git(*args)
        if code != 0:
            raise GitCommandError(
                f"git {' '.join(args)} failed: {err.strip() or out.strip()}"
            )
        return out

    @classmethod
    async def clone(
        cls, url: str, dest: str | Path, *, depth: int | None = 1
    ) -> LocalRepository:
        """Clone a repository (shallow by default) into ``dest``."""
        dest = Path(dest)
        args = ["clone"]
        if depth:
            args += ["--depth", str(depth)]
        args += [url, str(dest)]
        proc = await asyncio.create_subprocess_exec(
            "git", *args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        _, err = await proc.communicate()
        if proc.returncode != 0:
            raise GitCommandError(
                f"clone failed: {err.decode(errors='replace').strip()}"
            )
        return cls(dest)

    async def create_branch(self, name: str) -> None:
        """Create and switch to a new branch (never works on the default branch)."""
        await self._git_checked("checkout", "-b", name)

    async def write_files(self, files: dict[str, str]) -> None:
        """Write files into the working copy (sandboxed to the repo root)."""
        for rel_path, content in files.items():
            result = await self.fs.execute(
                ToolInput(action="write", args={"path": rel_path, "content": content})
            )
            if not result.success:
                raise GitCommandError(f"write {rel_path} failed: {result.error}")

    async def commit_all(
        self, branch: str, message: str, files: dict[str, str]
    ) -> CommitResult:
        """Write files, stage, and commit on ``branch``."""
        await self.write_files(files)
        await self._git_checked("add", "-A")
        await self._git_checked("commit", "-m", message)
        return CommitResult(branch=branch, message=message)

    async def push(self, branch: str, *, remote: str = "origin") -> None:
        """Push the branch to the remote (requires PUSH permission upstream)."""
        await self._git_checked("push", "-u", remote, branch)

    async def current_branch(self) -> str:
        return (await self._git_checked("rev-parse", "--abbrev-ref", "HEAD")).strip()
