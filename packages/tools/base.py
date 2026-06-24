"""Tool interface and result type.

Every tool returns a ``ToolResult`` rather than raising for expected failures,
so agents can reason about outcomes uniformly.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel


class ToolResult(BaseModel):
    """Uniform result for any tool invocation."""

    ok: bool
    output: str = ""
    error: str = ""
    data: dict[str, Any] = {}


class Tool(ABC):
    """Interface all tools implement."""

    name: str = "tool"

    @abstractmethod
    def run(self, **kwargs: Any) -> ToolResult:
        """Execute the tool and return a structured result."""
        raise NotImplementedError
