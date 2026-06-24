"""Execution profiles — the build/test/lint commands for a project.

The AI doesn't guess commands. Each project gets a profile derived from its
detected framework (see memory.detection). A profile maps logical steps
(install/build/test/lint) to concrete commands.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel


class ExecutionProfile(BaseModel):
    """The commands ForgeAI runs for a project."""

    framework: str = "unknown"
    image: str = "python:3.12-slim"
    install: str | None = None
    build: str | None = None
    test: str | None = None
    lint: str | None = None

    def steps(self) -> list[tuple[str, str]]:
        """Return ordered (name, command) pairs for the defined steps."""
        ordered = [
            ("install", self.install),
            ("build", self.build),
            ("test", self.test),
            ("lint", self.lint),
        ]
        return [(name, cmd) for name, cmd in ordered if cmd]


# Framework → profile. Mirrors the examples in the Phase 5 design.
_PROFILES: dict[str, ExecutionProfile] = {
    "fastapi": ExecutionProfile(
        framework="fastapi",
        image="python:3.12-slim",
        install="uv sync",
        build="python -m py_compile $(git ls-files '*.py')",
        test="pytest -q",
        lint="ruff check .",
    ),
    "python": ExecutionProfile(
        framework="python",
        image="python:3.12-slim",
        install="pip install -r requirements.txt",
        test="pytest -q",
        lint="ruff check .",
    ),
    "nextjs": ExecutionProfile(
        framework="nextjs",
        image="node:22-slim",
        install="pnpm install",
        build="pnpm build",
        test="pnpm test",
        lint="pnpm lint",
    ),
    "node": ExecutionProfile(
        framework="node",
        image="node:22-slim",
        install="npm install",
        build="npm run build",
        test="npm test",
    ),
}


def profile_for_framework(framework: str) -> ExecutionProfile:
    """Return the profile for a framework, or a minimal default."""
    return _PROFILES.get(framework, ExecutionProfile(framework=framework))


def profile_for_project(root: str | Path) -> ExecutionProfile:
    """Detect a project's framework and return its execution profile."""
    from memory.detection import detect_project

    profile = detect_project(root)
    # Prefer the most specific framework we recognize.
    for fw in ("nextjs", "fastapi"):
        if fw in profile.frameworks or fw.replace("js", "") in profile.frameworks:
            return profile_for_framework("nextjs" if fw == "nextjs" else "fastapi")
    if "next" in profile.frameworks:
        return profile_for_framework("nextjs")
    if "fastapi" in profile.frameworks:
        return profile_for_framework("fastapi")
    if "python" in profile.languages:
        return profile_for_framework("python")
    if any("javascript" in lang or "typescript" in lang for lang in profile.languages):
        return profile_for_framework("node")
    return ExecutionProfile()
