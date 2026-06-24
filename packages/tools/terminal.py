"""TerminalTool — run an allowlisted command, capture stdout/stderr/exit/duration.

Security: only commands whose executable is on the allowlist run; dangerous
commands (rm -rf, sudo, chmod, ...) are blocked. A timeout kills runaway
processes. The command runs with ``cwd`` confined to the workspace root.

NOTE: this runs on the host. For untrusted AI-generated code the DockerTool
must be used instead (see docs/security.md). The Tool Manager requires the
EXECUTE permission for every action here.
"""

from __future__ import annotations

import asyncio
import shlex
from pathlib import Path

from tools.base import (
    Permission,
    Tool,
    ToolError,
    ToolErrorCode,
    ToolInput,
    ToolResult,
)

# Executables agents are allowed to invoke.
ALLOWED_COMMANDS = {
    "python",
    "python3",
    "uv",
    "pip",
    "pytest",
    "node",
    "npm",
    "pnpm",
    "npx",
    "yarn",
    "git",
    "ls",
    "cat",
    "echo",
    "ruff",
    "black",
    "eslint",
    "tsc",
}

# Hard-blocked tokens anywhere in the command.
BLOCKED_TOKENS = {
    "sudo",
    "chmod",
    "chown",
    "mkfs",
    "dd",
    "shutdown",
    "reboot",
    ":(){:|:&};:",
}


class TerminalTool(Tool):
    name = "terminal"
    description = "Execute an allowlisted shell command and capture its output."

    def __init__(self, root: str | Path, default_timeout: float = 60.0):
        self.root = Path(root).resolve()
        self.default_timeout = default_timeout

    def permission_for(self, action: str) -> Permission | None:
        return Permission.EXECUTE

    def _check(self, command: str) -> ToolResult | None:
        """Return a failure ToolResult if the command is not allowed, else None."""
        try:
            tokens = shlex.split(command)
        except ValueError as exc:
            return ToolResult.fail(self.name, ToolErrorCode.INVALID_INPUT, str(exc))
        if not tokens:
            return ToolResult.fail(
                self.name, ToolErrorCode.INVALID_INPUT, "Empty command"
            )
        lowered = {t.lower() for t in tokens}
        if lowered & BLOCKED_TOKENS or "rm" in lowered:
            return ToolResult.fail(
                self.name,
                ToolErrorCode.BLOCKED_COMMAND,
                f"Blocked command: {tokens[0]}",
            )
        if tokens[0] not in ALLOWED_COMMANDS:
            return ToolResult.fail(
                self.name,
                ToolErrorCode.BLOCKED_COMMAND,
                f"Command not on allowlist: {tokens[0]}",
            )
        return None

    async def execute(self, tool_input: ToolInput) -> ToolResult:
        if tool_input.action != "run":
            return self._unknown_action(tool_input.action)
        command = tool_input.args.get("command")
        if not command:
            return ToolResult.fail(
                self.name, ToolErrorCode.INVALID_INPUT, "Missing command"
            )

        blocked = self._check(command)
        if blocked is not None:
            return blocked

        timeout = float(tool_input.args.get("timeout", self.default_timeout))
        proc = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(self.root),
        )
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        except TimeoutError:
            proc.kill()
            await proc.wait()
            return ToolResult.fail(
                self.name,
                ToolErrorCode.TIMEOUT,
                f"Timed out after {timeout}s",
                retryable=True,
            )

        out = stdout.decode(errors="replace")
        err = stderr.decode(errors="replace")
        return ToolResult(
            tool_name=self.name,
            success=proc.returncode == 0,
            output=out,
            error=(
                None
                if proc.returncode == 0
                else ToolError(
                    code=ToolErrorCode.EXECUTION_FAILED,
                    message=err or f"exit {proc.returncode}",
                    retryable=True,
                )
            ),
            metadata={"exit_code": proc.returncode, "stdout": out, "stderr": err},
        )
