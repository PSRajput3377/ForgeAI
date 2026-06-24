"""Unit + security tests for the TerminalTool."""

import pytest
from tools.base import ToolErrorCode, ToolInput
from tools.terminal import TerminalTool


def inp(command, **extra):
    return ToolInput(action="run", args={"command": command, **extra})


@pytest.mark.asyncio
async def test_allowed_command_runs(tmp_path):
    term = TerminalTool(tmp_path)
    res = await term.execute(inp("echo hello"))
    assert res.success
    assert "hello" in res.output
    assert res.metadata["exit_code"] == 0


@pytest.mark.asyncio
async def test_blocked_command_rm(tmp_path):
    term = TerminalTool(tmp_path)
    res = await term.execute(inp("rm -rf /"))
    assert not res.success
    assert res.error.code == ToolErrorCode.BLOCKED_COMMAND


@pytest.mark.asyncio
async def test_blocked_command_sudo(tmp_path):
    term = TerminalTool(tmp_path)
    res = await term.execute(inp("sudo ls"))
    assert not res.success
    assert res.error.code == ToolErrorCode.BLOCKED_COMMAND


@pytest.mark.asyncio
async def test_command_not_on_allowlist(tmp_path):
    term = TerminalTool(tmp_path)
    res = await term.execute(inp("curl http://example.com"))
    assert not res.success
    assert res.error.code == ToolErrorCode.BLOCKED_COMMAND


@pytest.mark.asyncio
async def test_timeout_kills_process(tmp_path):
    term = TerminalTool(tmp_path)
    # python is allowlisted; sleep longer than the timeout.
    res = await term.execute(
        inp('python3 -c "import time; time.sleep(5)"', timeout=0.3)
    )
    assert not res.success
    assert res.error.code == ToolErrorCode.TIMEOUT
    assert res.error.retryable


@pytest.mark.asyncio
async def test_nonzero_exit_is_failure(tmp_path):
    term = TerminalTool(tmp_path)
    res = await term.execute(inp('python3 -c "import sys; sys.exit(3)"'))
    assert not res.success
    assert res.metadata["exit_code"] == 3
