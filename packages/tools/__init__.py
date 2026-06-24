"""tools — the abstraction layer between agents and the machine.

Agents never access the filesystem, shell, or git directly. They invoke tools
that return structured ``ToolResult`` objects. This keeps side effects
auditable and lets us sandbox execution later (Phase 8).

Phase 2 ships the interface and a real, sandboxed-to-a-root ``FilesystemTool``.
Terminal/Docker (Phase 8), Git (Phase 9), Search and Database tools are
declared here and implemented in their phases.
"""

from tools.base import Tool, ToolResult
from tools.filesystem import FilesystemTool

__all__ = ["FilesystemTool", "Tool", "ToolResult"]
