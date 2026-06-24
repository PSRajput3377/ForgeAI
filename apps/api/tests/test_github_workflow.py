"""End-to-end autonomous GitHub workflow tests (offline, FakeGitHubProvider).

The centerpiece: branch → commit → PR → review → CI fails → classify → fix →
re-run → CI passes → merge.
"""

import pytest
from execution.errors import ErrorCategory
from github.manager import GitHubManager
from github.models import CIStatus, PRState, Repository, Review, ReviewComment
from github.provider import FakeGitHubProvider


@pytest.fixture
def repo():
    return Repository(owner="psr", name="forge", default_branch="main")


async def _approving_reviewer(pr):
    return Review(pr_number=pr.number, approved=True, summary="LGTM")


@pytest.mark.asyncio
async def test_happy_path_branch_pr_merge(repo):
    provider = FakeGitHubProvider()
    mgr = GitHubManager(provider)
    result = await mgr.run_task(
        repo,
        kind="feature",
        task="Add JWT auth",
        commit_message="feat(auth): add JWT authentication",
        files={"auth.py": "import jwt"},
        pr_title="feat(auth): JWT authentication",
        pr_summary="Adds JWT auth",
        changes=["auth routes", "middleware"],
        testing="pytest passed",
        reviewer=_approving_reviewer,
        auto_merge=True,
    )
    assert result.ci_status == CIStatus.SUCCESS
    assert result.review_approved
    assert result.merged
    assert (
        await provider.get_pull_request(repo, result.pr_number)
    ).state == PRState.MERGED
    # Timeline reads like a junior engineer's workflow.
    joined = " | ".join(result.timeline)
    assert "Created branch feature/add-jwt-auth" in joined
    assert "Opened PR" in joined and "Merged PR" in joined


@pytest.mark.asyncio
async def test_ci_failure_self_corrects_then_merges(repo):
    provider = FakeGitHubProvider()
    mgr = GitHubManager(provider)

    fixes = {"n": 0}

    async def ci_fixer(error):
        # The CI failure is classified as a dependency error (missing 'jwt').
        assert error.category == ErrorCategory.DEPENDENCY
        fixes["n"] += 1
        return {"requirements.txt": "pyjwt"}

    async def open_then_run():
        # Script: first CI check fails, subsequent checks pass.
        result = await mgr.run_task(
            repo,
            kind="feature",
            task="Add JWT auth",
            commit_message="feat(auth): add JWT",
            files={"auth.py": "import jwt"},
            pr_title="feat: jwt",
            pr_summary="jwt",
            changes=["auth"],
            testing="pytest",
            reviewer=_approving_reviewer,
            ci_fixer=ci_fixer,
            auto_merge=True,
        )
        return result

    # Pre-script CI for the PR that will be created (#1): fail once, then pass.
    provider.script_ci(1, [CIStatus.FAILURE, CIStatus.SUCCESS])
    result = await open_then_run()

    assert result.ci_attempts == 1
    assert fixes["n"] == 1
    assert result.ci_status == CIStatus.SUCCESS
    assert result.merged
    assert "CI failed: dependency" in " | ".join(result.timeline)


@pytest.mark.asyncio
async def test_ci_failure_without_fixer_stops_unmerged(repo):
    provider = FakeGitHubProvider()
    mgr = GitHubManager(provider)
    provider.script_ci(
        1, [CIStatus.FAILURE, CIStatus.FAILURE, CIStatus.FAILURE, CIStatus.FAILURE]
    )
    result = await mgr.run_task(
        repo,
        kind="feature",
        task="x",
        commit_message="feat: x",
        files={"a.py": "x"},
        pr_title="x",
        pr_summary="x",
        changes=["x"],
        testing="x",
        auto_merge=True,
    )
    assert result.ci_status == CIStatus.FAILURE
    assert not result.merged  # never merges on red CI


@pytest.mark.asyncio
async def test_review_with_comments_blocks_unapproved_merge(repo):
    provider = FakeGitHubProvider()
    mgr = GitHubManager(provider)

    async def critical_reviewer(pr):
        return Review(
            pr_number=pr.number,
            approved=False,
            summary="Changes requested",
            comments=[
                ReviewComment(
                    path="auth.py",
                    line=1,
                    body="Hash the password",
                    severity="security",
                )
            ],
        )

    result = await mgr.run_task(
        repo,
        kind="feature",
        task="x",
        commit_message="feat: x",
        files={"a.py": "x"},
        pr_title="x",
        pr_summary="x",
        changes=["x"],
        testing="x",
        reviewer=critical_reviewer,
        auto_merge=True,
    )
    # CI is green but review requested changes → not merged.
    assert result.ci_status == CIStatus.SUCCESS
    assert not result.review_approved
    assert not result.merged
    assert provider.reviews[result.pr_number].comments[0].severity == "security"
