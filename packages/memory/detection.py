"""Automatic project understanding — detect languages, frameworks, tools.

Reads a project's manifest files so agents don't need the stack explained.
Pure/offline: it only reads files. (The Phase 3 ProjectTool exposes this as a
tool; this module is the reusable detection logic the Project Memory builds on.)
"""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, Field


class ProjectProfile(BaseModel):
    languages: list[str] = Field(default_factory=list)
    frameworks: list[str] = Field(default_factory=list)
    package_managers: list[str] = Field(default_factory=list)
    markers: list[str] = Field(default_factory=list)


_NODE_FRAMEWORKS = (
    "next",
    "react",
    "vue",
    "svelte",
    "express",
    "tailwindcss",
    "zustand",
)
_PY_FRAMEWORKS = ("fastapi", "django", "flask", "langgraph", "sqlalchemy", "alembic")


def detect_project(root: str | Path) -> ProjectProfile:
    """Inspect a project root and return its technology profile."""
    root = Path(root)
    profile = ProjectProfile()

    pkg = root / "package.json"
    if pkg.exists():
        profile.languages.append("javascript/typescript")
        profile.markers.append("package.json")
        try:
            data = json.loads(pkg.read_text(encoding="utf-8"))
            deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
        except (json.JSONDecodeError, OSError):
            deps = {}
        if "typescript" in deps:
            profile.languages.append("typescript")
        profile.frameworks += [fw for fw in _NODE_FRAMEWORKS if fw in deps]
        if (root / "pnpm-lock.yaml").exists():
            profile.package_managers.append("pnpm")
        elif (root / "package-lock.json").exists():
            profile.package_managers.append("npm")
        elif (root / "yarn.lock").exists():
            profile.package_managers.append("yarn")

    pyproject = root / "pyproject.toml"
    requirements = root / "requirements.txt"
    py_text = ""
    if pyproject.exists():
        profile.languages.append("python")
        profile.markers.append("pyproject.toml")
        py_text = pyproject.read_text(encoding="utf-8")
        if (root / "uv.lock").exists():
            profile.package_managers.append("uv")
    if requirements.exists():
        if "python" not in profile.languages:
            profile.languages.append("python")
        profile.markers.append("requirements.txt")
        py_text += "\n" + requirements.read_text(encoding="utf-8")
    profile.frameworks += [fw for fw in _PY_FRAMEWORKS if fw in py_text.lower()]

    # De-dup while preserving order.
    profile.languages = list(dict.fromkeys(profile.languages))
    profile.frameworks = list(dict.fromkeys(profile.frameworks))
    profile.package_managers = list(dict.fromkeys(profile.package_managers))
    return profile
