"""tools — the Action Engine: the abstraction layer between agents and the machine.

Agents never access the filesystem, shell, git, or network directly. They go
through the Tool Manager, which runs the same lifecycle for every tool:

    request → validation → permission check → execution → logging → result

Agents may also declare a *capability* (what they want) and let the
``CapabilityResolver`` pick the tool (the ⭐ Phase 3 abstraction).

Public surface:
- Contracts:   Tool, ToolInput, ToolResult, ToolError, Permission, ToolErrorCode
- Plumbing:    ToolRegistry, ToolManager, Capability, CapabilityResolver
- Tools:       Filesystem, Terminal, Docker, Git, Browser, Search, Project, Memory
- Factory:     build_default_registry(root)
"""

from __future__ import annotations

from pathlib import Path

from tools.base import (
    Permission,
    Tool,
    ToolError,
    ToolErrorCode,
    ToolInput,
    ToolResult,
)
from tools.browser import BrowserTool
from tools.capabilities import Capability, CapabilityResolver
from tools.docker import DockerTool
from tools.filesystem import FilesystemTool
from tools.git import GitTool
from tools.manager import ToolManager
from tools.memory import MemoryTool
from tools.project import ProjectTool
from tools.registry import ToolRegistry
from tools.search import SearchTool
from tools.terminal import TerminalTool

__all__ = [
    "BrowserTool",
    "Capability",
    "CapabilityResolver",
    "DockerTool",
    "FilesystemTool",
    "GitTool",
    "MemoryTool",
    "Permission",
    "ProjectTool",
    "SearchTool",
    "TerminalTool",
    "Tool",
    "ToolError",
    "ToolErrorCode",
    "ToolInput",
    "ToolManager",
    "ToolRegistry",
    "ToolResult",
    "build_default_registry",
]


def build_default_registry(root: str | Path) -> ToolRegistry:
    """Register the standard tool set scoped to a workspace ``root``."""
    registry = ToolRegistry()
    registry.register(FilesystemTool(root))
    registry.register(TerminalTool(root))
    registry.register(DockerTool(root))
    registry.register(GitTool(root))
    registry.register(SearchTool(root))
    registry.register(ProjectTool(root))
    registry.register(BrowserTool())
    registry.register(MemoryTool())
    return registry
