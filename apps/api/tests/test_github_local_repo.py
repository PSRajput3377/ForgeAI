"""Local clone → branch → commit → push workflow, using real git on temp repos."""

import asyncio

import pytest
from github.local_repo import GitCommandError, LocalRepository
from tools.base import ToolInput


async def _init_bare_remote(path):
    """A bare repo to act as 'origin' so push works without a network."""
    proc = await asyncio.create_subprocess_exec(
        "git",
        "init",
        "--bare",
        str(path),
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL,
    )
    await proc.wait()


@pytest.mark.asyncio
async def test_clone_branch_commit_push(tmp_path):
    # Set up a bare "remote" and seed it with an initial commit via a temp clone.
    remote = tmp_path / "remote.git"
    await _init_bare_remote(remote)

    seed = tmp_path / "seed"
    repo = await LocalRepository.clone(str(remote), seed, depth=None)
    # Configure identity for commits in this isolated repo.
    await repo._git_checked("config", "user.email", "t@t.t")
    await repo._git_checked("config", "user.name", "t")
    await repo.commit_all("main", "chore: seed", {"README.md": "# seed\n"})
    # Seed repos created from an empty bare remote start on the default branch;
    # push it so clones have something to branch from.
    await repo._git_checked("branch", "-M", "main")
    await repo.push("main")

    # Now ForgeAI clones, branches, commits, and pushes a feature.
    work = tmp_path / "work"
    forge = await LocalRepository.clone(str(remote), work, depth=None)
    await forge._git_checked("config", "user.email", "f@f.f")
    await forge._git_checked("config", "user.name", "forge")

    await forge.create_branch("feature/jwt")
    assert await forge.current_branch() == "feature/jwt"

    result = await forge.commit_all(
        "feature/jwt", "feat: add jwt", {"auth.py": "import jwt\n"}
    )
    assert result.branch == "feature/jwt"

    # Push the feature branch to the bare remote (no network).
    await forge.push("feature/jwt")

    # Verify the file landed and the branch exists on the remote.
    branches = await forge._git_checked("branch", "-a")
    assert "feature/jwt" in branches
    read = await forge.fs.execute(ToolInput(action="read", args={"path": "auth.py"}))
    assert read.output == "import jwt\n"


@pytest.mark.asyncio
async def test_write_files_is_sandboxed(tmp_path):
    repo = LocalRepository(tmp_path)
    # Path escape is rejected by the underlying FilesystemTool.
    with pytest.raises(GitCommandError):
        await repo.write_files({"../escape.txt": "nope"})


@pytest.mark.asyncio
async def test_clone_failure_raises(tmp_path):
    with pytest.raises(GitCommandError):
        await LocalRepository.clone(
            "/nonexistent/repo.git", tmp_path / "dest", depth=None
        )
