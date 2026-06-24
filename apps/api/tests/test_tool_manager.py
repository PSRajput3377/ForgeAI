"""Integration tests for the Tool Manager: lifecycle, permissions, logging."""

import pytest
from tools.base import Permission, ToolErrorCode, ToolInput
from tools.filesystem import FilesystemTool
from tools.logging import ListSink
from tools.manager import ToolManager
from tools.registry import ToolRegistry


def make_manager(tmp_path, granted=None):
    registry = ToolRegistry()
    registry.register(FilesystemTool(tmp_path))
    sink = ListSink()
    return ToolManager(registry, granted=granted, log_sink=sink), sink


@pytest.mark.asyncio
async def test_run_through_manager_succeeds(tmp_path):
    mgr, sink = make_manager(tmp_path)
    res = await mgr.run(
        "filesystem", ToolInput(action="write", args={"path": "a.txt", "content": "x"})
    )
    assert res.success
    assert res.execution_time >= 0.0
    # The call was logged.
    assert len(sink.logs) == 1
    assert sink.logs[0].tool == "filesystem" and sink.logs[0].success


@pytest.mark.asyncio
async def test_unknown_tool(tmp_path):
    mgr, _ = make_manager(tmp_path)
    res = await mgr.run("nope", ToolInput(action="read", args={}))
    assert not res.success and res.error.code == ToolErrorCode.NOT_FOUND


@pytest.mark.asyncio
async def test_permission_denied_for_delete_by_default(tmp_path):
    mgr, sink = make_manager(tmp_path)  # default grants exclude DELETE
    await mgr.run("filesystem", ToolInput(action="write", args={"path": "a.txt", "content": "x"}))
    res = await mgr.run("filesystem", ToolInput(action="delete", args={"path": "a.txt"}))
    assert not res.success and res.error.code == ToolErrorCode.PERMISSION_DENIED
    # File still exists because delete was blocked before execution.
    exists = await mgr.run("filesystem", ToolInput(action="exists", args={"path": "a.txt"}))
    assert exists.metadata["exists"] is True


@pytest.mark.asyncio
async def test_delete_allowed_when_granted(tmp_path):
    granted = {Permission.READ, Permission.WRITE, Permission.DELETE}
    mgr, _ = make_manager(tmp_path, granted=granted)
    await mgr.run("filesystem", ToolInput(action="write", args={"path": "a.txt", "content": "x"}))
    res = await mgr.run("filesystem", ToolInput(action="delete", args={"path": "a.txt"}))
    assert res.success
