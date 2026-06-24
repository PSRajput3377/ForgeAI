"""Tests for the ExecutionEngine: the autonomous build→fail→fix→retry→pass loop."""

import pytest
from execution.engine import ExecutionEngine
from execution.errors import ErrorCategory
from execution.profiles import ExecutionProfile
from execution.sandbox import ExecutionResult, FakeSandbox


def fail_then_pass_responder(fail_times: int):
    """Build fails `fail_times` times (missing module), then succeeds."""
    state = {"fixed": 0}

    def responder(command: str, idx: int) -> ExecutionResult:
        if "pytest" in command and state["fixed"] < fail_times:
            return ExecutionResult(
                command=command,
                success=False,
                exit_code=1,
                stderr="ModuleNotFoundError: No module named 'jwt'",
                sandbox="fake",
            )
        return ExecutionResult(command=command, success=True, exit_code=0, sandbox="fake")

    return responder, state


@pytest.mark.asyncio
async def test_happy_path_no_retries():
    sb = FakeSandbox()  # default: everything succeeds
    profile = ExecutionProfile(framework="python", test="pytest -q")
    engine = ExecutionEngine(sb, profile)
    record = await engine.execute(task="t", project="p")
    assert record.success and record.retries == 0
    # Sandbox lifecycle was used.
    assert sb.setup_count == 1 and sb.teardown_count == 1


@pytest.mark.asyncio
async def test_self_correcting_loop_recovers():
    responder, state = fail_then_pass_responder(fail_times=2)
    sb = FakeSandbox(responder=responder)
    profile = ExecutionProfile(framework="python", test="pytest -q")

    async def fixer(error, logs):
        # Verify the engine classified the dependency error and "apply" a fix.
        assert error.category == ErrorCategory.DEPENDENCY
        state["fixed"] += 1
        return True

    engine = ExecutionEngine(sb, profile, fixer=fixer, max_retries=3)
    record = await engine.execute(task="add jwt", project="p")
    assert record.success
    assert record.retries == 2  # failed twice, fixed, passed on the third


@pytest.mark.asyncio
async def test_gives_up_after_max_retries():
    def always_fail(command: str, idx: int) -> ExecutionResult:
        return ExecutionResult(
            command=command,
            success=False,
            exit_code=1,
            stderr="ModuleNotFoundError: No module named 'jwt'",
            sandbox="fake",
        )

    sb = FakeSandbox(responder=always_fail)
    profile = ExecutionProfile(framework="python", test="pytest -q")

    calls = {"n": 0}

    async def fixer(error, logs):
        calls["n"] += 1
        return True  # claims to fix, but the build keeps failing

    engine = ExecutionEngine(sb, profile, fixer=fixer, max_retries=3)
    record = await engine.execute()
    assert not record.success
    assert record.retries == 3  # stopped at the bound
    assert calls["n"] == 3


@pytest.mark.asyncio
async def test_no_fixer_stops_immediately():
    def always_fail(command: str, idx: int) -> ExecutionResult:
        return ExecutionResult(
            command=command, success=False, exit_code=1, stderr="boom", sandbox="fake"
        )

    sb = FakeSandbox(responder=always_fail)
    profile = ExecutionProfile(test="pytest -q")
    engine = ExecutionEngine(sb, profile)  # no fixer
    record = await engine.execute()
    assert not record.success and record.retries == 0


@pytest.mark.asyncio
async def test_security_error_not_retried():
    def leak(command: str, idx: int) -> ExecutionResult:
        return ExecutionResult(
            command=command,
            success=False,
            exit_code=1,
            stderr='API_KEY="sk-live-secret"',
            sandbox="fake",
        )

    sb = FakeSandbox(responder=leak)
    profile = ExecutionProfile(test="pytest -q")
    fixer_calls = {"n": 0}

    async def fixer(error, logs):
        fixer_calls["n"] += 1
        return True

    engine = ExecutionEngine(sb, profile, fixer=fixer, max_retries=3)
    record = await engine.execute()
    assert not record.success
    # Security errors are non-retryable → fixer never invoked.
    assert fixer_calls["n"] == 0
