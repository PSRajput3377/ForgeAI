"""Tests for the FakeGitHubProvider and branch/PR services."""

import pytest
from github.models import CIStatus, PRState, Repository
from github.provider import FakeGitHubProvider
from github.services import BranchService, PullRequestService, branch_name_for, unique_branch_name


@pytest.fixture
def repo():
    return Repository(owner="psr", name="forge", default_branch="main")


def test_branch_naming():
    assert branch_name_for("feature", "Add JWT Auth") == "feature/add-jwt-auth"
    assert branch_name_for("bug", "Token validation fails") == "fix/token-validation-fails"
    assert branch_name_for("docs", "Update README") == "docs/update-readme"


def test_unique_branch_name_avoids_collisions():
    base = branch_name_for("feature", "Add JWT Auth")
    assert unique_branch_name(base, "5187ad4c") == "feature/add-jwt-auth-5187ad4c"
    assert unique_branch_name(base, "5187ad4cc3c5409a") == "feature/add-jwt-auth-5187ad4c"


@pytest.mark.asyncio
async def test_create_branch_from_base(repo):
    provider = FakeGitHubProvider()
    svc = BranchService(provider)
    branch = await svc.create_task_branch(repo, "feature", "dark mode")
    assert branch.name == "feature/dark-mode"
    names = {b.name for b in await provider.list_branches(repo)}
    assert names == {"main", "feature/dark-mode"}


@pytest.mark.asyncio
async def test_cannot_branch_from_missing_base(repo):
    provider = FakeGitHubProvider()
    with pytest.raises(ValueError):
        await provider.create_branch(repo, "x", "nonexistent")


@pytest.mark.asyncio
async def test_commit_advances_branch_sha(repo):
    provider = FakeGitHubProvider()
    await provider.create_branch(repo, "feature/x", "main")
    before = provider.branches["feature/x"].sha
    commit = await provider.create_commit(repo, "feature/x", "feat: x", {"a.py": "x"})
    assert commit.sha != before
    assert provider.branches["feature/x"].sha == commit.sha


@pytest.mark.asyncio
async def test_pr_body_is_structured(repo):
    svc = PullRequestService(FakeGitHubProvider())
    body = svc.render_body("Added auth", ["routes", "middleware"], "pytest passed")
    assert "## Summary" in body and "## Changes" in body and "## Testing" in body
    assert "- routes" in body


@pytest.mark.asyncio
async def test_open_and_merge_pr(repo):
    provider = FakeGitHubProvider()
    await provider.create_branch(repo, "feature/x", "main")
    pr = await provider.open_pull_request(repo, "feat: x", "body", "feature/x", "main")
    assert pr.state == PRState.OPEN
    merged = await provider.merge_pull_request(repo, pr.number)
    assert merged.state == PRState.MERGED


@pytest.mark.asyncio
async def test_ci_status_scripting(repo):
    provider = FakeGitHubProvider()
    pr = await provider.open_pull_request(repo, "t", "b", "feature/x", "main")
    provider.script_ci(pr.number, [CIStatus.FAILURE, CIStatus.SUCCESS])
    runs1 = await provider.get_check_runs(repo, pr.number)
    assert runs1[0].status == CIStatus.FAILURE and "jwt" in runs1[0].logs
    runs2 = await provider.get_check_runs(repo, pr.number)
    assert runs2[0].status == CIStatus.SUCCESS
