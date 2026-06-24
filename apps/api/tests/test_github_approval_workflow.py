"""Phase 8.2 — approval-gated GitHub workflow + ApprovalService + manager ops."""

import pytest
from github.approval import ApprovalService, ApprovalStatus
from github.manager import GitHubManager
from github.provider import FakeGitHubProvider
from github.workflow import GitHubWorkflow, PRPlan


@pytest.fixture
def repo_provider():
    provider = FakeGitHubProvider()
    return provider


def make_plan() -> PRPlan:
    return PRPlan(
        kind="feature",
        task="Add JWT authentication",
        branch="feature/add-jwt-authentication",
        commit_message="feat(auth): add JWT authentication",
        files={"auth.py": "import jwt"},
        pr_title="feat(auth): JWT authentication",
        pr_summary="Adds JWT auth",
        changes=["auth routes", "middleware"],
        testing="pytest passed",
    )


# --- ApprovalService ---


def test_approval_request_starts_pending():
    svc = ApprovalService()
    req = svc.request("create_pr", summary="open a PR")
    assert req.status == ApprovalStatus.PENDING
    assert svc.pending() == [req]


def test_approve_and_reject():
    svc = ApprovalService()
    a = svc.request("create_pr")
    svc.approve(a.id, by="prashant")
    assert svc.get(a.id).is_approved
    assert svc.get(a.id).decided_by == "prashant"

    b = svc.request("create_pr")
    svc.reject(b.id)
    assert svc.get(b.id).status == ApprovalStatus.REJECTED
    assert svc.pending() == []  # both decided


def test_cannot_decide_twice():
    svc = ApprovalService()
    req = svc.request("create_pr")
    svc.approve(req.id)
    with pytest.raises(ValueError):
        svc.reject(req.id)


# --- discrete GitHubManager ops ---


@pytest.mark.asyncio
async def test_manager_discrete_ops(repo_provider):
    mgr = GitHubManager(repo_provider)
    repo = await repo_provider.get_repository("psr", "forge")

    branch = await mgr.create_branch(repo, "feature", "dark mode")
    assert branch.name == "feature/dark-mode"
    await mgr.create_commit(repo, branch.name, "feat: dark mode", {"theme.ts": "x"})
    pr = await mgr.create_pr(
        repo,
        title="feat: dark mode",
        summary="s",
        changes=["c"],
        testing="t",
        head=branch.name,
    )
    assert pr.number >= 1
    synced = await mgr.sync_repository(repo)
    assert "feature/dark-mode" in synced["branches"]


# --- the gated workflow ---


@pytest.mark.asyncio
async def test_propose_writes_nothing(repo_provider):
    mgr = GitHubManager(repo_provider)
    wf = GitHubWorkflow(mgr, ApprovalService())
    repo = await repo_provider.get_repository("psr", "forge")

    req = wf.propose(repo, make_plan())
    assert req.status == ApprovalStatus.PENDING
    # No branch, no commit, no PR were created during propose().
    assert {b.name for b in await repo_provider.list_branches(repo)} == {"main"}
    assert repo_provider.prs == {}
    assert repo_provider.commits == []


@pytest.mark.asyncio
async def test_execute_refused_without_approval(repo_provider):
    mgr = GitHubManager(repo_provider)
    approvals = ApprovalService()
    wf = GitHubWorkflow(mgr, approvals)
    repo = await repo_provider.get_repository("psr", "forge")
    plan = make_plan()

    req = wf.propose(repo, plan)
    # Still pending → execute must refuse and write nothing.
    with pytest.raises(PermissionError):
        await wf.execute(repo, plan, req.id)
    assert repo_provider.prs == {}


@pytest.mark.asyncio
async def test_execute_after_approval_creates_pr(repo_provider):
    mgr = GitHubManager(repo_provider)
    approvals = ApprovalService()
    wf = GitHubWorkflow(mgr, approvals)
    repo = await repo_provider.get_repository("psr", "forge")
    plan = make_plan()

    req = wf.propose(repo, plan)
    approvals.approve(req.id, by="prashant")
    outcome = await wf.execute(repo, plan, req.id)

    assert outcome.approved
    assert outcome.pr_number == 1
    assert outcome.pr_url == "https://github.com/psr/forge/pull/1"
    assert "Created branch feature/add-jwt-authentication" in outcome.timeline
    assert "Opened PR #1" in outcome.timeline
    # The PR really exists now.
    assert (await repo_provider.get_pull_request(repo, 1)).title == plan.pr_title


@pytest.mark.asyncio
async def test_execute_refused_after_rejection(repo_provider):
    mgr = GitHubManager(repo_provider)
    approvals = ApprovalService()
    wf = GitHubWorkflow(mgr, approvals)
    repo = await repo_provider.get_repository("psr", "forge")
    plan = make_plan()

    req = wf.propose(repo, plan)
    approvals.reject(req.id)
    with pytest.raises(PermissionError):
        await wf.execute(repo, plan, req.id)
    assert repo_provider.prs == {}
