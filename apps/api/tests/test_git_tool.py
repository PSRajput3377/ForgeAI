"""Unit tests for the GitTool against a real temporary repo."""

import asyncio

import pytest
from tools.base import Permission, ToolInput
from tools.git import GitTool


async def _init_repo(path):
    for args in (
        ["init"],
        ["config", "user.email", "t@t.t"],
        ["config", "user.name", "t"],
    ):
        proc = await asyncio.create_subprocess_exec(
            "git",
            *args,
            cwd=str(path),
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        await proc.wait()


@pytest.mark.asyncio
async def test_status_and_commit_flow(tmp_path):
    await _init_repo(tmp_path)
    (tmp_path / "a.txt").write_text("hi")
    git = GitTool(tmp_path)

    status = await git.execute(ToolInput(action="status", args={}))
    assert status.success
    assert "a.txt" in status.output

    add = await git.execute(ToolInput(action="add", args={"paths": ["a.txt"]}))
    assert add.success

    commit = await git.execute(ToolInput(action="commit", args={"message": "feat: add a"}))
    assert commit.success

    log = await git.execute(ToolInput(action="log", args={"n": 1}))
    assert "feat: add a" in log.output


def test_push_requires_push_permission(tmp_path):
    git = GitTool(tmp_path)
    assert git.permission_for("push") == Permission.PUSH
    assert git.permission_for("commit") == Permission.COMMIT
    assert git.permission_for("status") == Permission.READ
