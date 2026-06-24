"""The Git agent proposes a gated PR inside the full workflow (offline)."""

import pytest
from agents.workflow import build_workflow
from core.roles import AgentRole
from core.state import ProjectState
from github.approval import ApprovalService
from github.manager import GitHubManager
from github.provider import FakeGitHubProvider
from github.workflow import GitHubWorkflow, PRPlan


@pytest.mark.asyncio
async def test_run_produces_gated_pr_proposal(echo_router):
    provider = FakeGitHubProvider()
    approvals = ApprovalService()
    wf = GitHubWorkflow(GitHubManager(provider), approvals)
    repo = await provider.get_repository("psr", "forge")

    app = build_workflow(echo_router, github_workflow=wf, github_repo=repo)
    state = ProjectState(user_request="Add JWT authentication", project_id="run-1")
    result = ProjectState.model_validate(await app.ainvoke(state))

    # The Git agent opened a proposal — but nothing was written to GitHub.
    assert result.pr_approval_id is not None
    assert result.pr_url is None
    assert provider.prs == {}  # no PR created during the run
    assert approvals.get(result.pr_approval_id).status.value == "pending"

    # The Git agent reported the proposal in the audit trail.
    git_msgs = [m for m in result.messages if m.sender == AgentRole.GIT]
    assert git_msgs and "Proposed PR" in git_msgs[0].summary


@pytest.mark.asyncio
async def test_proposal_then_human_approval_creates_pr(echo_router):
    provider = FakeGitHubProvider()
    approvals = ApprovalService()
    wf = GitHubWorkflow(GitHubManager(provider), approvals)
    repo = await provider.get_repository("psr", "forge")

    app = build_workflow(echo_router, github_workflow=wf, github_repo=repo)
    result = ProjectState.model_validate(
        await app.ainvoke(ProjectState(user_request="Add JWT auth", project_id="r"))
    )

    # A human approves, then the proposal is executed → PR exists.
    approvals.approve(result.pr_approval_id, by="prashant")
    plan = PRPlan(
        kind="feature",
        task="Add JWT auth",
        branch="feature/add-jwt-auth",
        commit_message="feat: jwt",
        files={"auth.py": "import jwt"},
        pr_title="feat: jwt",
        pr_summary="jwt",
    )
    outcome = await wf.execute(repo, plan, result.pr_approval_id)
    assert outcome.pr_url.endswith("/pull/1")
    assert (await provider.get_pull_request(repo, 1)).number == 1


@pytest.mark.asyncio
async def test_run_without_github_only_drafts_commit(echo_router):
    # Backward compatible: no workflow wired → no proposal, graph still runs.
    app = build_workflow(echo_router)
    result = ProjectState.model_validate(
        await app.ainvoke(ProjectState(user_request="x"))
    )
    assert result.pr_approval_id is None
    git_msgs = [m for m in result.messages if m.sender == AgentRole.GIT]
    assert git_msgs and "commit" in git_msgs[0].summary.lower()
