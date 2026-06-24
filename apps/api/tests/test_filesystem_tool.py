"""Unit tests for the FilesystemTool (Phase 3 contract: async execute)."""

import pytest
from tools.base import Permission, ToolErrorCode, ToolInput
from tools.filesystem import FilesystemTool


def inp(action, **args):
    return ToolInput(action=action, args=args)


@pytest.mark.asyncio
async def test_write_then_read(tmp_path):
    fs = FilesystemTool(tmp_path)
    w = await fs.execute(inp("write", path="sub/file.txt", content="hi"))
    assert w.success
    r = await fs.execute(inp("read", path="sub/file.txt"))
    assert r.success and r.output == "hi"


@pytest.mark.asyncio
async def test_list_directory(tmp_path):
    fs = FilesystemTool(tmp_path)
    await fs.execute(inp("write", path="a.txt", content="1"))
    await fs.execute(inp("write", path="b.txt", content="2"))
    r = await fs.execute(inp("list", path="."))
    assert r.success
    assert set(r.metadata["entries"]) == {"a.txt", "b.txt"}


@pytest.mark.asyncio
async def test_patch(tmp_path):
    fs = FilesystemTool(tmp_path)
    await fs.execute(inp("write", path="f.py", content="x = 1"))
    p = await fs.execute(inp("patch", path="f.py", find="1", replace="2"))
    assert p.success
    r = await fs.execute(inp("read", path="f.py"))
    assert r.output == "x = 2"


@pytest.mark.asyncio
async def test_search(tmp_path):
    fs = FilesystemTool(tmp_path)
    await fs.execute(inp("write", path="a.txt", content="needle here"))
    await fs.execute(inp("write", path="b.txt", content="nothing"))
    r = await fs.execute(inp("search", query="needle"))
    assert r.metadata["matches"] == ["a.txt"]


@pytest.mark.asyncio
async def test_read_missing_file_returns_structured_error(tmp_path):
    fs = FilesystemTool(tmp_path)
    r = await fs.execute(inp("read", path="nope.txt"))
    assert not r.success
    assert r.error.code == ToolErrorCode.FILE_NOT_FOUND


@pytest.mark.asyncio
async def test_path_escape_is_blocked(tmp_path):
    fs = FilesystemTool(tmp_path)
    r = await fs.execute(inp("read", path="../../etc/passwd"))
    assert not r.success
    assert r.error.code == ToolErrorCode.PATH_ESCAPE


def test_delete_requires_delete_permission(tmp_path):
    fs = FilesystemTool(tmp_path)
    assert fs.permission_for("delete") == Permission.DELETE
    assert fs.permission_for("write") == Permission.WRITE
    assert fs.permission_for("read") == Permission.READ
