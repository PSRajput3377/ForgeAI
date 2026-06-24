"""FilesystemTool — read/write/list files within a sandboxed project root.

All paths are resolved relative to ``root`` and validated to stay inside it, so
an agent cannot read or write outside the project workspace.
"""

from __future__ import annotations

from pathlib import Path

from tools.base import Tool, ToolResult


class FilesystemTool(Tool):
    """Confined file operations rooted at a project directory."""

    name = "filesystem"

    def __init__(self, root: str | Path):
        self.root = Path(root).resolve()

    def _resolve(self, relative_path: str) -> Path:
        """Resolve a path and ensure it stays within the sandbox root."""
        target = (self.root / relative_path).resolve()
        if target != self.root and self.root not in target.parents:
            raise ValueError(f"Path escapes project root: {relative_path}")
        return target

    def run(self, action: str, path: str = "", content: str = "") -> ToolResult:
        """Dispatch a filesystem action: read | write | list | exists."""
        try:
            if action == "read":
                return self._read(path)
            if action == "write":
                return self._write(path, content)
            if action == "list":
                return self._list(path)
            if action == "exists":
                return ToolResult(
                    ok=True, data={"exists": self._resolve(path).exists()}
                )
            return ToolResult(ok=False, error=f"Unknown action: {action}")
        except Exception as exc:  # noqa: BLE001 - report any failure as a result
            return ToolResult(ok=False, error=str(exc))

    def _read(self, path: str) -> ToolResult:
        target = self._resolve(path)
        if not target.is_file():
            return ToolResult(ok=False, error=f"Not a file: {path}")
        return ToolResult(ok=True, output=target.read_text(encoding="utf-8"))

    def _write(self, path: str, content: str) -> ToolResult:
        target = self._resolve(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return ToolResult(ok=True, data={"bytes": len(content.encode("utf-8"))})

    def _list(self, path: str) -> ToolResult:
        target = self._resolve(path or ".")
        if not target.is_dir():
            return ToolResult(ok=False, error=f"Not a directory: {path}")
        entries = sorted(p.relative_to(self.root).as_posix() for p in target.iterdir())
        return ToolResult(ok=True, data={"entries": entries})
