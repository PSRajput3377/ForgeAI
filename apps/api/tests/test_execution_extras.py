"""Tests for execution profiles, approval gates, local sandbox, scaffolding."""

import pytest
from execution.approval import ApprovalGate, GatedAction
from execution.profiles import profile_for_framework, profile_for_project
from execution.sandbox import LocalSandbox
from execution.test_generation import scaffold_for


def test_profile_for_known_frameworks():
    assert profile_for_framework("fastapi").test == "pytest -q"
    assert profile_for_framework("nextjs").build == "pnpm build"
    assert profile_for_framework("nextjs").image == "node:22-slim"


def test_profile_steps_skip_undefined():
    p = profile_for_framework("node")  # no lint defined
    names = [name for name, _ in p.steps()]
    assert "lint" not in names
    assert "install" in names and "test" in names


def test_profile_for_project_detects_fastapi(tmp_path):
    (tmp_path / "pyproject.toml").write_text("[project]\ndependencies=['fastapi']")
    (tmp_path / "uv.lock").write_text("")
    profile = profile_for_project(tmp_path)
    assert profile.framework == "fastapi"


def test_profile_for_project_detects_nextjs(tmp_path):
    (tmp_path / "package.json").write_text('{"dependencies":{"next":"15"}}')
    profile = profile_for_project(tmp_path)
    assert profile.framework == "nextjs"


@pytest.mark.asyncio
async def test_approval_gate_denies_by_default():
    gate = ApprovalGate()
    assert await gate.request(GatedAction.GIT_PUSH) is False


@pytest.mark.asyncio
async def test_approval_gate_auto_approve():
    gate = ApprovalGate(auto_approve={GatedAction.DELETE_FILES})
    assert await gate.request(GatedAction.DELETE_FILES) is True
    assert await gate.request(GatedAction.DEPLOY) is False


@pytest.mark.asyncio
async def test_approval_gate_custom_approver():
    async def approve_pushes(action, details):
        return action == "git_push"

    gate = ApprovalGate(approver=approve_pushes)
    assert await gate.request(GatedAction.GIT_PUSH) is True
    assert await gate.request(GatedAction.MERGE_PR) is False


@pytest.mark.asyncio
async def test_local_sandbox_runs_real_command(tmp_path):
    sb = LocalSandbox(tmp_path)
    res = await sb.run("echo hello")
    assert res.success and "hello" in res.stdout


@pytest.mark.asyncio
async def test_local_sandbox_timeout(tmp_path):
    sb = LocalSandbox(tmp_path)
    res = await sb.run('python3 -c "import time; time.sleep(5)"', timeout=0.3)
    assert not res.success and res.timed_out


def test_scaffold_for_languages():
    assert "def test_" in scaffold_for("python", "auth.py")
    assert "describe(" in scaffold_for("typescript", "auth.ts")
