"""DockerTool — run a command inside a fresh, disposable container.

The safest tool: AI-generated code must never run on the host. Each run creates
a container, executes the command with the workspace mounted read-only-ish,
collects logs, and destroys the container. Resource/network limits are applied.

If the Docker daemon is unavailable, every action returns a structured
UNAVAILABLE error rather than raising — callers (and the Reflection agent) can
handle it gracefully.
"""

from __future__ import annotations

import asyncio
import shutil
from pathlib import Path

from tools.base import Permission, Tool, ToolError, ToolErrorCode, ToolInput, ToolResult

DEFAULT_IMAGE = "python:3.12-slim"


class DockerTool(Tool):
    name = "docker"
    description = "Run a command inside a fresh, isolated, disposable container."

    def __init__(
        self,
        root: str | Path,
        image: str = DEFAULT_IMAGE,
        default_timeout: float = 120.0,
    ):
        self.root = Path(root).resolve()
        self.image = image
        self.default_timeout = default_timeout

    def permission_for(self, action: str) -> Permission | None:
        return Permission.EXECUTE

    async def _docker_available(self) -> bool:
        if shutil.which("docker") is None:
            return False
        try:
            proc = await asyncio.create_subprocess_exec(
                "docker",
                "info",
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            await asyncio.wait_for(proc.wait(), timeout=10)
            return proc.returncode == 0
        except (TimeoutError, OSError):
            return False

    async def execute(self, tool_input: ToolInput) -> ToolResult:
        if tool_input.action != "run":
            return self._unknown_action(tool_input.action)
        command = tool_input.args.get("command")
        if not command:
            return ToolResult.fail(self.name, ToolErrorCode.INVALID_INPUT, "Missing command")

        if not await self._docker_available():
            return ToolResult.fail(
                self.name,
                ToolErrorCode.UNAVAILABLE,
                "Docker daemon is not available",
                retryable=True,
            )

        image = tool_input.args.get("image", self.image)
        timeout = float(tool_input.args.get("timeout", self.default_timeout))

        # Fresh container: mounted workspace, no network, memory-capped, auto-removed.
        docker_args = [
            "docker",
            "run",
            "--rm",
            "--network",
            "none",
            "--memory",
            "512m",
            "--cpus",
            "1",
            "-v",
            f"{self.root}:/workspace",
            "-w",
            "/workspace",
            image,
            "sh",
            "-c",
            command,
        ]
        proc = await asyncio.create_subprocess_exec(
            *docker_args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
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
            metadata={"exit_code": proc.returncode, "image": image, "stderr": err},
        )
