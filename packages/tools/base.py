"""Core tool contracts: Tool interface, ToolInput, ToolResult, errors, permissions.

Every tool in ForgeAI implements the SAME interface and returns the SAME result
shape, so agents (and the Tool Manager) consume them uniformly. No tool has a
custom API. (Phase 3)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class Permission(StrEnum):
    """Capabilities a tool action may require. The Tool Manager checks these
    against the set granted for a run before executing (least privilege)."""

    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    EXECUTE = "execute"
    COMMIT = "commit"
    PUSH = "push"
    NETWORK = "network"


class ToolErrorCode(StrEnum):
    """Stable, machine-readable error codes. The Reflection agent branches on
    these (e.g. retry on TIMEOUT, give up on PERMISSION_DENIED)."""

    NOT_FOUND = "NOT_FOUND"
    FILE_NOT_FOUND = "FILE_NOT_FOUND"
    INVALID_INPUT = "INVALID_INPUT"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    PATH_ESCAPE = "PATH_ESCAPE"
    BLOCKED_COMMAND = "BLOCKED_COMMAND"
    TIMEOUT = "TIMEOUT"
    EXECUTION_FAILED = "EXECUTION_FAILED"
    UNAVAILABLE = "UNAVAILABLE"
    UNKNOWN_ACTION = "UNKNOWN_ACTION"


class ToolError(BaseModel):
    """Structured error returned inside a failed ToolResult."""

    code: ToolErrorCode
    message: str
    retryable: bool = False


class ToolInput(BaseModel):
    """Uniform input to every tool: an ``action`` plus its ``args``.

    Tools document which actions they accept and which args each needs
    (see docs/tools.md and specs/tool-spec.md).
    """

    action: str
    args: dict[str, Any] = Field(default_factory=dict)


class ToolResult(BaseModel):
    """Uniform result from every tool invocation."""

    tool_name: str
    success: bool
    output: str = ""
    error: ToolError | None = None
    execution_time: float = 0.0
    metadata: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def ok(cls, tool_name: str, output: str = "", **metadata: Any) -> ToolResult:
        """Build a successful result."""
        return cls(tool_name=tool_name, success=True, output=output, metadata=metadata)

    @classmethod
    def fail(
        cls,
        tool_name: str,
        code: ToolErrorCode,
        message: str,
        retryable: bool = False,
    ) -> ToolResult:
        """Build a failed result with a structured error."""
        return cls(
            tool_name=tool_name,
            success=False,
            error=ToolError(code=code, message=message, retryable=retryable),
        )


class Tool(ABC):
    """Interface every tool implements.

    A tool declares its ``name`` and ``description``, maps each action to the
    ``Permission`` it requires, and implements ``execute``. Timing, permission
    enforcement, and logging are handled by the Tool Manager — the tool only
    does its job and returns a ToolResult.
    """

    name: str = "tool"
    description: str = ""

    def permission_for(self, action: str) -> Permission | None:
        """Return the permission an action requires, or None if unrestricted.

        Override per tool. Default: no permission required (read-only helpers).
        """
        return None

    @abstractmethod
    async def execute(self, tool_input: ToolInput) -> ToolResult:
        """Perform the action and return a standardized result."""
        raise NotImplementedError

    def _unknown_action(self, action: str) -> ToolResult:
        """Helper: standard error for an unsupported action."""
        return ToolResult.fail(
            self.name,
            ToolErrorCode.UNKNOWN_ACTION,
            f"{self.name}: unknown action '{action}'",
        )
