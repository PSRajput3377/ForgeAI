"""Tool Registry — register tools by name, look them up without if/else chains.

Instead of ``if tool == "filesystem": ...`` everywhere, tools register once and
are resolved by name. Adding a tool later requires no changes elsewhere.
"""

from __future__ import annotations

from tools.base import Tool


class ToolRegistry:
    """A name → Tool registry."""

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        """Register a tool. Raises if the name is already taken."""
        if tool.name in self._tools:
            raise ValueError(f"Tool already registered: {tool.name}")
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool | None:
        """Return the tool registered under ``name``, or None."""
        return self._tools.get(name)

    def has(self, name: str) -> bool:
        return name in self._tools

    def names(self) -> list[str]:
        return sorted(self._tools)

    def all(self) -> list[Tool]:
        return list(self._tools.values())
