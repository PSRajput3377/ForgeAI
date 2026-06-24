"""Log collection and artifact storage.

The LogCollector accumulates every command's result for a run; the
ArtifactManager persists logs/reports/generated files so a run is fully
traceable. Phase 5 ships in-memory collectors (offline-testable); the
PostgreSQL-backed store lands in the Database phase behind the same shape.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from execution.sandbox import ExecutionResult


class RunRecord(BaseModel):
    """The full history of one execution run (matches the 'Execution History'
    design: task, status, retries, duration)."""

    task: str = ""
    project: str = ""
    success: bool = False
    retries: int = 0
    duration: float = 0.0
    results: list[ExecutionResult] = Field(default_factory=list)
    artifacts: dict[str, str] = Field(default_factory=dict)


class LogCollector:
    """Collects command results for a single run."""

    def __init__(self) -> None:
        self.results: list[ExecutionResult] = []

    def add(self, result: ExecutionResult) -> None:
        self.results.append(result)

    @property
    def total_duration(self) -> float:
        return sum(r.duration for r in self.results)

    def tail_logs(self, n: int = 3) -> str:
        """Concatenated stdout+stderr of the last n results (for reflection)."""
        recent = self.results[-n:]
        return "\n".join(f"$ {r.command}\n{r.stdout}{r.stderr}".strip() for r in recent)


class ArtifactManager:
    """Stores named artifacts (logs, reports, coverage, generated files)."""

    def __init__(self) -> None:
        self._artifacts: dict[str, str] = {}

    def store(self, name: str, content: str) -> None:
        self._artifacts[name] = content

    def get(self, name: str) -> str | None:
        return self._artifacts.get(name)

    def all(self) -> dict[str, str]:
        return dict(self._artifacts)
