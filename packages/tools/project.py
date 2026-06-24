"""ProjectTool — understands a project: detect framework, scan dependencies.

Unique to ForgeAI. Inspects the workspace to answer "what kind of project is
this?" so agents can act appropriately (e.g. run pytest vs npm test).
"""

from __future__ import annotations

import json
from pathlib import Path

from tools.base import Permission, Tool, ToolErrorCode, ToolInput, ToolResult

# Marker file -> (language, framework hints)
_MARKERS = {
    "package.json": "node",
    "pyproject.toml": "python",
    "requirements.txt": "python",
    "go.mod": "go",
    "Cargo.toml": "rust",
    "pom.xml": "java",
}


class ProjectTool(Tool):
    name = "project"
    description = "Analyze a project: detect framework, scan dependencies."

    def __init__(self, root: str | Path):
        self.root = Path(root).resolve()

    def permission_for(self, action: str) -> Permission | None:
        return Permission.READ

    async def execute(self, tool_input: ToolInput) -> ToolResult:
        match tool_input.action:
            case "analyze" | "detect_framework":
                return self._analyze()
            case "scan_dependencies":
                return self._dependencies()
            case _:
                return self._unknown_action(tool_input.action)

    def _present_markers(self) -> dict[str, str]:
        return {m: lang for m, lang in _MARKERS.items() if (self.root / m).exists()}

    def _analyze(self) -> ToolResult:
        markers = self._present_markers()
        languages = sorted(set(markers.values()))
        frameworks: list[str] = []

        if "package.json" in markers:
            deps = self._node_deps()
            for fw in ("next", "react", "vue", "svelte", "express", "tailwindcss"):
                if fw in deps:
                    frameworks.append(fw)
        if (self.root / "pyproject.toml").exists():
            text = (self.root / "pyproject.toml").read_text(encoding="utf-8")
            for fw in ("fastapi", "django", "flask", "langgraph"):
                if fw in text:
                    frameworks.append(fw)

        return ToolResult.ok(
            self.name,
            output=f"languages={languages} frameworks={frameworks}",
            languages=languages,
            frameworks=frameworks,
            markers=sorted(markers),
        )

    def _node_deps(self) -> dict:
        try:
            data = json.loads((self.root / "package.json").read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
        return {**data.get("dependencies", {}), **data.get("devDependencies", {})}

    def _dependencies(self) -> ToolResult:
        markers = self._present_markers()
        if not markers:
            return ToolResult.fail(
                self.name, ToolErrorCode.NOT_FOUND, "No dependency manifest found"
            )
        deps: dict[str, list[str]] = {}
        if "package.json" in markers:
            deps["node"] = sorted(self._node_deps())
        return ToolResult.ok(
            self.name, output=f"{sum(len(v) for v in deps.values())} deps", deps=deps
        )
