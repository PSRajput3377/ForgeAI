"""Tool Manager — the single entry point through which agents use tools.

Agents never touch the OS or a tool directly. They hand the Tool Manager a tool
name and a ToolInput; the Manager runs the SAME lifecycle for every tool:

    request → validation → permission check → execution → logging → result

The Manager owns timing, permission enforcement, and logging, so individual
tools stay focused on their job.
"""

from __future__ import annotations

import time

from tools.base import Permission, ToolErrorCode, ToolInput, ToolResult
from tools.logging import LogSink, build_log, loguru_sink
from tools.registry import ToolRegistry


class ToolManager:
    """Finds, permission-checks, executes, and logs tool calls."""

    def __init__(
        self,
        registry: ToolRegistry,
        granted: set[Permission] | None = None,
        log_sink: LogSink | None = None,
    ) -> None:
        self.registry = registry
        # Permissions granted for this run. Default is least-privilege-ish:
        # read/write/execute/commit, but NOT delete/push/network — those are
        # opt-in (see docs/security.md).
        self.granted = (
            granted
            if granted is not None
            else {
                Permission.READ,
                Permission.WRITE,
                Permission.EXECUTE,
                Permission.COMMIT,
            }
        )
        self.log_sink = log_sink or loguru_sink

    async def run(self, tool_name: str, tool_input: ToolInput) -> ToolResult:
        """Execute a tool call through the full lifecycle."""
        start = time.perf_counter()

        # 1. Find the tool.
        tool = self.registry.get(tool_name)
        if tool is None:
            return self._finish(
                tool_input,
                ToolResult.fail(
                    tool_name, ToolErrorCode.NOT_FOUND, f"No such tool: {tool_name}"
                ),
                start,
            )

        # 2. Validate input shape (Pydantic already validated ToolInput itself;
        #    here we ensure an action was provided).
        if not tool_input.action:
            return self._finish(
                tool_input,
                ToolResult.fail(
                    tool.name, ToolErrorCode.INVALID_INPUT, "Missing action"
                ),
                start,
            )

        # 3. Permission check.
        required = tool.permission_for(tool_input.action)
        if required is not None and required not in self.granted:
            return self._finish(
                tool_input,
                ToolResult.fail(
                    tool.name,
                    ToolErrorCode.PERMISSION_DENIED,
                    f"Action '{tool_input.action}' requires '{required}' permission",
                ),
                start,
            )

        # 4. Execute (tools should not raise for expected failures, but guard).
        try:
            result = await tool.execute(tool_input)
        except Exception as exc:  # noqa: BLE001 - normalize any escape into a result
            result = ToolResult.fail(
                tool.name, ToolErrorCode.EXECUTION_FAILED, str(exc)
            )

        # 5/6. Stamp duration, log, return.
        return self._finish(tool_input, result, start)

    def _finish(
        self, tool_input: ToolInput, result: ToolResult, start: float
    ) -> ToolResult:
        """Stamp execution_time, emit a log, and return the result."""
        if result.execution_time == 0.0:
            result.execution_time = time.perf_counter() - start
        self.log_sink(build_log(tool_input, result))
        return result
