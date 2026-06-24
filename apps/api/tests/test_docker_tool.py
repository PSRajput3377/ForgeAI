"""Tests for the DockerTool. Real container runs require a daemon, so we test
the graceful UNAVAILABLE path deterministically by stubbing availability."""

import pytest
from tools.base import ToolErrorCode, ToolInput
from tools.docker import DockerTool


@pytest.mark.asyncio
async def test_unavailable_daemon_returns_structured_error(tmp_path, monkeypatch):
    docker = DockerTool(tmp_path)
    monkeypatch.setattr(docker, "_docker_available", lambda: _false())
    res = await docker.execute(ToolInput(action="run", args={"command": "echo hi"}))
    assert not res.success
    assert res.error.code == ToolErrorCode.UNAVAILABLE
    assert res.error.retryable


async def _false():
    return False


@pytest.mark.asyncio
async def test_missing_command(tmp_path):
    docker = DockerTool(tmp_path)
    res = await docker.execute(ToolInput(action="run", args={}))
    assert not res.success
    assert res.error.code == ToolErrorCode.INVALID_INPUT


@pytest.mark.asyncio
async def test_unknown_action(tmp_path):
    docker = DockerTool(tmp_path)
    res = await docker.execute(ToolInput(action="nope", args={}))
    assert not res.success
    assert res.error.code == ToolErrorCode.UNKNOWN_ACTION
