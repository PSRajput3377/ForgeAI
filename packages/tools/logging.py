"""Tool execution logging.

The Tool Manager emits a ToolLog for every invocation: time, tool, action,
input, result summary, duration, status. These records back the Logs UI and let
a run be replayed later. The default sink uses Loguru; tests can inject a list
sink to assert on what was logged.
"""

from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel, Field

from tools.base import ToolInput, ToolResult


class ToolLog(BaseModel):
    """A single tool-execution log entry."""

    tool: str
    action: str
    input_args: dict = Field(default_factory=dict)
    success: bool = False
    duration: float = 0.0
    error_code: str | None = None


class LogSink(Protocol):
    """Anything that can receive a ToolLog."""

    def __call__(self, log: ToolLog) -> None: ...


class ListSink:
    """Collects logs in a list — useful for tests and run replay."""

    def __init__(self) -> None:
        self.logs: list[ToolLog] = []

    def __call__(self, log: ToolLog) -> None:
        self.logs.append(log)


def loguru_sink(log: ToolLog) -> None:
    """Default sink: write a structured line via Loguru if available."""
    try:
        from loguru import logger

        logger.bind(tool=log.tool).info(
            "tool={} action={} success={} dur={:.3f}s err={}",
            log.tool,
            log.action,
            log.success,
            log.duration,
            log.error_code,
        )
    except ImportError:  # pragma: no cover - loguru is a backend dep
        pass


def build_log(tool_input: ToolInput, result: ToolResult) -> ToolLog:
    """Construct a ToolLog from an invocation's input and result."""
    return ToolLog(
        tool=result.tool_name,
        action=tool_input.action,
        input_args=tool_input.args,
        success=result.success,
        duration=result.execution_time,
        error_code=result.error.code if result.error else None,
    )
