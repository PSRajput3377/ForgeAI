"""Sandbox layer — where commands actually run.

One interface, three backends (mirrors the Phase 4 offline/prod pattern):

- ``DockerSandbox`` real isolated container: create → mount → run → destroy.
  Fresh environment every time; resource-limited; no network by default.
- ``LocalSandbox``  runs allowlisted commands on the host with a timeout, for
  when Docker is unavailable. NOT isolated — used as a degraded fallback.
- ``FakeSandbox``   returns scripted results; deterministic, for tests of the
  reflection/retry loop without running anything.

Security (blocked commands) is enforced centrally in ``security.py`` and applied
by every sandbox before execution.
"""

from __future__ import annotations

import asyncio
import shutil
from abc import ABC, abstractmethod
from collections.abc import Callable
from pathlib import Path

from pydantic import BaseModel

from execution.security import ResourceLimits, check_command


class ExecutionResult(BaseModel):
    """Standardized result of running a command in a sandbox."""

    command: str
    success: bool
    exit_code: int = 0
    stdout: str = ""
    stderr: str = ""
    duration: float = 0.0
    timed_out: bool = False
    blocked: bool = False
    sandbox: str = ""


class Sandbox(ABC):
    """A place to run commands. Manages its own lifecycle."""

    name: str = "sandbox"

    @abstractmethod
    async def run(self, command: str, timeout: float | None = None) -> ExecutionResult:
        """Run a single command and return its result."""

    async def __aenter__(self) -> Sandbox:
        await self.setup()
        return self

    async def __aexit__(self, *exc) -> None:
        await self.teardown()

    # setup/teardown are optional hooks, intentionally non-abstract (not every
    # sandbox needs a lifecycle), so they are not marked @abstractmethod.
    async def setup(self) -> None:  # noqa: B027
        """Create/start the sandbox (no-op by default)."""

    async def teardown(self) -> None:  # noqa: B027
        """Destroy/clean up the sandbox (no-op by default)."""


class FakeSandbox(Sandbox):
    """Returns scripted results. The script maps a substring → ExecutionResult,
    so tests can simulate 'first build fails, retry succeeds'."""

    name = "fake"

    def __init__(self, responder: Callable[[str, int], ExecutionResult] | None = None):
        self.responder = responder
        self.calls: list[str] = []
        self.setup_count = 0
        self.teardown_count = 0

    async def setup(self) -> None:
        self.setup_count += 1

    async def teardown(self) -> None:
        self.teardown_count += 1

    async def run(self, command: str, timeout: float | None = None) -> ExecutionResult:
        blocked = check_command(command)
        if blocked is not None:
            return ExecutionResult(
                command=command,
                success=False,
                blocked=True,
                stderr=blocked,
                sandbox=self.name,
            )
        idx = len(self.calls)
        self.calls.append(command)
        if self.responder is not None:
            return self.responder(command, idx)
        return ExecutionResult(
            command=command, success=True, exit_code=0, sandbox=self.name
        )


class LocalSandbox(Sandbox):
    """Runs allowlisted commands on the host with a timeout. Degraded fallback
    when Docker is unavailable — NOT isolated."""

    name = "local"

    def __init__(self, root: str | Path, limits: ResourceLimits | None = None):
        self.root = Path(root).resolve()
        self.limits = limits or ResourceLimits()

    async def run(self, command: str, timeout: float | None = None) -> ExecutionResult:
        blocked = check_command(command)
        if blocked is not None:
            return ExecutionResult(
                command=command,
                success=False,
                blocked=True,
                stderr=blocked,
                sandbox=self.name,
            )
        timeout = timeout or self.limits.timeout
        loop = asyncio.get_event_loop()
        start = loop.time()
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
            return ExecutionResult(
                command=command,
                success=False,
                timed_out=True,
                duration=loop.time() - start,
                stderr=f"Timed out after {timeout}s",
                sandbox=self.name,
            )
        return ExecutionResult(
            command=command,
            success=proc.returncode == 0,
            exit_code=proc.returncode or 0,
            stdout=stdout.decode(errors="replace"),
            stderr=stderr.decode(errors="replace"),
            duration=loop.time() - start,
            sandbox=self.name,
        )


class DockerSandbox(Sandbox):
    """Real isolated execution in a disposable container.

    A long-lived container is created on ``setup`` (so several commands in a
    task share one environment) and removed on ``teardown``. Falls back to
    ``available()`` checks so callers can degrade gracefully.
    """

    name = "docker"

    def __init__(
        self,
        root: str | Path,
        image: str = "python:3.12-slim",
        limits: ResourceLimits | None = None,
    ):
        self.root = Path(root).resolve()
        self.image = image
        self.limits = limits or ResourceLimits()
        self._container: str | None = None

    @staticmethod
    async def available() -> bool:
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

    async def setup(self) -> None:
        """Start a detached, idle container with the workspace mounted."""
        args = [
            "docker",
            "run",
            "-d",
            "--rm",
            "--network",
            "none",
            "--memory",
            f"{self.limits.memory_mb}m",
            "--cpus",
            str(self.limits.cpus),
            "-v",
            f"{self.root}:/workspace",
            "-w",
            "/workspace",
            self.image,
            "sleep",
            str(int(self.limits.timeout) + 60),
        ]
        proc = await asyncio.create_subprocess_exec(
            *args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        out, _ = await proc.communicate()
        if proc.returncode == 0:
            self._container = out.decode().strip()

    async def teardown(self) -> None:
        if self._container:
            proc = await asyncio.create_subprocess_exec(
                "docker",
                "kill",
                self._container,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            await proc.wait()
            self._container = None

    async def run(self, command: str, timeout: float | None = None) -> ExecutionResult:
        blocked = check_command(command)
        if blocked is not None:
            return ExecutionResult(
                command=command,
                success=False,
                blocked=True,
                stderr=blocked,
                sandbox=self.name,
            )
        if self._container is None:
            return ExecutionResult(
                command=command,
                success=False,
                stderr="Sandbox not started (use 'async with' or call setup())",
                sandbox=self.name,
            )
        timeout = timeout or self.limits.timeout
        loop = asyncio.get_event_loop()
        start = loop.time()
        proc = await asyncio.create_subprocess_exec(
            "docker",
            "exec",
            self._container,
            "sh",
            "-c",
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        except TimeoutError:
            proc.kill()
            await proc.wait()
            return ExecutionResult(
                command=command,
                success=False,
                timed_out=True,
                duration=loop.time() - start,
                sandbox=self.name,
            )
        return ExecutionResult(
            command=command,
            success=proc.returncode == 0,
            exit_code=proc.returncode or 0,
            stdout=stdout.decode(errors="replace"),
            stderr=stderr.decode(errors="replace"),
            duration=loop.time() - start,
            sandbox=self.name,
        )
