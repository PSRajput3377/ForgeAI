"""SearchTool — search local project files (lexical, Phase 3).

Returns files and matching lines for a query within the workspace. Semantic
retrieval over embeddings (Qdrant) is layered on in the Memory + RAG phase; the
capability system lets that swap in without changing agent code.
"""

from __future__ import annotations

from pathlib import Path

from tools.base import Permission, Tool, ToolErrorCode, ToolInput, ToolResult

_SKIP_DIRS = {".git", "node_modules", ".venv", "__pycache__", ".next", "dist", "build"}


class SearchTool(Tool):
    name = "search"
    description = "Search project files for a query (lexical)."

    def __init__(self, root: str | Path):
        self.root = Path(root).resolve()

    def permission_for(self, action: str) -> Permission | None:
        return Permission.READ

    async def execute(self, tool_input: ToolInput) -> ToolResult:
        if tool_input.action != "search":
            return self._unknown_action(tool_input.action)
        query = tool_input.args.get("query")
        if not query:
            return ToolResult.fail(self.name, ToolErrorCode.INVALID_INPUT, "Missing query")
        limit = int(tool_input.args.get("limit", 50))

        results: list[dict] = []
        for path in self.root.rglob("*"):
            if not path.is_file():
                continue
            if any(part in _SKIP_DIRS for part in path.parts):
                continue
            try:
                lines = path.read_text(encoding="utf-8").splitlines()
            except (UnicodeDecodeError, OSError):
                continue
            for lineno, line in enumerate(lines, 1):
                if query in line:
                    results.append(
                        {
                            "file": path.relative_to(self.root).as_posix(),
                            "line": lineno,
                            "text": line.strip()[:200],
                        }
                    )
                    if len(results) >= limit:
                        break
            if len(results) >= limit:
                break

        return ToolResult.ok(
            self.name,
            output=f"{len(results)} match(es)",
            matches=results,
        )
