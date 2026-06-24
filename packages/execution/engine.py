"""ExecutionEngine — the autonomous build→run→test→reflect→fix→retry loop.

This is the heart of Phase 5. Given an execution profile and a sandbox, it runs
the project's steps; on failure it classifies the error, asks a *fixer* to
propose/apply a fix, and retries — up to a bounded number of attempts.

    run steps → fail → classify → reflect/fix → retry → … → pass | give up

The ``fixer`` is injected (the Reflection/Coder agents supply the real one). A
fixer receives the ClassifiedError + logs and returns True if it changed
something worth retrying. This keeps the engine independent of how fixes are
generated and makes the whole loop testable offline with a scripted sandbox.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from pydantic import BaseModel

from execution.artifacts import ArtifactManager, LogCollector, RunRecord
from execution.errors import ClassifiedError, classify_error
from execution.profiles import ExecutionProfile
from execution.sandbox import ExecutionResult, Sandbox

# A fixer attempts to fix a classified error. Returns True if it applied a fix
# (so a retry makes sense), False if it cannot help.
Fixer = Callable[[ClassifiedError, str], Awaitable[bool]]


class RetryManager:
    """Bounds retries. Never retries forever."""

    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries

    def should_retry(self, attempt: int, error: ClassifiedError) -> bool:
        return attempt < self.max_retries and error.retryable


class StepOutcome(BaseModel):
    name: str
    result: ExecutionResult
    error: ClassifiedError | None = None


class ExecutionEngine:
    """Runs a profile's steps in a sandbox with self-correcting retries."""

    def __init__(
        self,
        sandbox: Sandbox,
        profile: ExecutionProfile,
        fixer: Fixer | None = None,
        max_retries: int = 3,
    ):
        self.sandbox = sandbox
        self.profile = profile
        self.fixer = fixer
        self.retry = RetryManager(max_retries)
        self.logs = LogCollector()
        self.artifacts = ArtifactManager()

    async def _run_steps(self) -> StepOutcome | None:
        """Run all profile steps in order. Return the first failing outcome, or
        None if every step succeeded."""
        for name, command in self.profile.steps():
            result = await self.sandbox.run(command)
            self.logs.add(result)
            if not result.success:
                error = classify_error(result.stderr, result.stdout, timed_out=result.timed_out)
                return StepOutcome(name=name, result=result, error=error)
        return None

    async def execute(self, *, task: str = "", project: str = "") -> RunRecord:
        """Run the loop: steps → (fail → fix → retry)* → record."""
        attempt = 0
        await self.sandbox.setup()
        try:
            while True:
                failure = await self._run_steps()
                if failure is None:
                    return self._record(task, project, success=True, retries=attempt)

                # A failure occurred. Try to self-correct.
                self.artifacts.store(
                    f"error-attempt-{attempt}",
                    f"[{failure.error.category}] {failure.error.detail}",
                )
                if not self.retry.should_retry(attempt, failure.error):
                    return self._record(task, project, success=False, retries=attempt)

                fixed = False
                if self.fixer is not None:
                    fixed = await self.fixer(failure.error, self.logs.tail_logs())
                if not fixed:
                    # No fix applied → retrying would repeat the failure.
                    return self._record(task, project, success=False, retries=attempt)

                attempt += 1
        finally:
            await self.sandbox.teardown()

    def _record(self, task: str, project: str, *, success: bool, retries: int) -> RunRecord:
        return RunRecord(
            task=task,
            project=project,
            success=success,
            retries=retries,
            duration=self.logs.total_duration,
            results=self.logs.results,
            artifacts=self.artifacts.all(),
        )
