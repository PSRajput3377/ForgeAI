"""GitHub integration endpoints — drive the live (or fake) provider.

Read endpoints are safe to demo against a real repository. The write/PR flow is
exposed but gated: it requires GitHub to be configured and runs against whatever
repo you point it at, so use a sandbox.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from github.approval import ApprovalService
from github.manager import GitHubManager
from github.workflow import GitHubWorkflow, PRPlan
from pydantic import BaseModel, Field

from app.github_runtime import build_provider, github_configured

router = APIRouter(prefix="/github", tags=["github"])

# Process-wide approval service + workflow (the governance layer for writes).
_approvals = ApprovalService()


def _workflow() -> GitHubWorkflow:
    return GitHubWorkflow(GitHubManager(build_provider()), _approvals)


class RepoRef(BaseModel):
    owner: str
    name: str


@router.get("/status")
def status() -> dict:
    """Whether GitHub is live (token configured) or running on the fake provider."""
    return {"mode": "live" if github_configured() else "fake"}


@router.get("/repo/{owner}/{name}")
async def get_repo(owner: str, name: str) -> dict:
    """Fetch repository info (read). Works live against a real repo."""
    provider = build_provider()
    repo = await provider.get_repository(owner, name)
    return repo.model_dump()


@router.get("/repo/{owner}/{name}/branches")
async def list_branches(owner: str, name: str) -> dict:
    """List branches (read)."""
    provider = build_provider()
    repo = await provider.get_repository(owner, name)
    branches = await provider.list_branches(repo)
    return {"branches": [b.model_dump() for b in branches]}


@router.get("/repo/{owner}/{name}/issues")
async def list_issues(owner: str, name: str) -> dict:
    """List open issues — the source for Issue → Planner task conversion (read)."""
    provider = build_provider()
    repo = await provider.get_repository(owner, name)
    issues = await provider.list_issues(repo)
    return {"issues": [i.model_dump() for i in issues]}


@router.get("/repo/{owner}/{name}/pulls/{number}")
async def get_pull_request(owner: str, name: str, number: int) -> dict:
    """Fetch a pull request (read)."""
    if not github_configured():
        raise HTTPException(400, "GitHub is not configured (set GITHUB_TOKEN)")
    provider = build_provider()
    repo = await provider.get_repository(owner, name)
    pr = await provider.get_pull_request(repo, number)
    return pr.model_dump()


# --- approval-gated write workflow (Phase 8.2 / 11) ---

# In-process registry of proposals so the UI can list pending approvals, show
# diffs, and execute by approval_id alone (true one-click approve). A row holds
# the repo coordinates + the PRPlan behind each approval request.
_proposals: dict[str, dict] = {}


class ProposePR(BaseModel):
    owner: str
    name: str
    kind: str = "feature"
    task: str
    commit_message: str
    files: dict[str, str] = Field(default_factory=dict)
    pr_title: str
    pr_summary: str = ""
    changes: list[str] = Field(default_factory=list)
    testing: str = ""


def _plan_from(body: ProposePR) -> PRPlan:
    from github.services import branch_name_for

    return PRPlan(
        kind=body.kind,
        task=body.task,
        branch=branch_name_for(body.kind, body.task),
        commit_message=body.commit_message,
        files=body.files,
        pr_title=body.pr_title,
        pr_summary=body.pr_summary,
        changes=body.changes,
        testing=body.testing,
    )


def _proposal_view(approval_id: str) -> dict:
    row = _proposals[approval_id]
    plan: PRPlan = row["plan"]
    req = _approvals.get(approval_id)
    return {
        "approval_id": approval_id,
        "status": req.status.value if req else "unknown",
        "repo": row["repo"],
        "task": plan.task,
        "branch": plan.branch,
        "pr_title": plan.pr_title,
        "pr_summary": plan.pr_summary,
        "files_changed": sorted(plan.files.keys()),
        "testing": plan.testing,
        "pr_url": row.get("pr_url"),
    }


@router.post("/pr/propose", status_code=201)
async def propose_pr(body: ProposePR) -> dict:
    """Propose a PR — opens an approval request. Writes NOTHING to GitHub."""
    wf = _workflow()
    repo = await build_provider().get_repository(body.owner, body.name)
    plan = _plan_from(body)
    req = wf.propose(repo, plan)
    _proposals[req.id] = {
        "plan": plan,
        "repo": repo.full_name,
        "owner": body.owner,
        "name": body.name,
    }
    return _proposal_view(req.id)


@router.get("/pr/pending")
def list_pending() -> dict:
    """All pending PR proposals — the Approval Center's data source."""
    pending_ids = {r.id for r in _approvals.pending()}
    return {"pending": [_proposal_view(i) for i in _proposals if i in pending_ids]}


@router.get("/pr/{approval_id}")
def get_proposal(approval_id: str) -> dict:
    """A single proposal (metadata + changed files)."""
    if approval_id not in _proposals:
        raise HTTPException(404, "No such proposal")
    return _proposal_view(approval_id)


@router.get("/pr/{approval_id}/diff")
def get_diff(approval_id: str) -> dict:
    """The proposed file contents — powers the Diff Viewer before approval."""
    if approval_id not in _proposals:
        raise HTTPException(404, "No such proposal")
    plan: PRPlan = _proposals[approval_id]["plan"]
    return {
        "approval_id": approval_id,
        "files": [{"path": p, "content": c} for p, c in sorted(plan.files.items())],
    }


@router.post("/pr/{approval_id}/approve")
def approve_pr(approval_id: str) -> dict:
    """Approve a pending PR proposal."""
    try:
        _approvals.approve(approval_id)
    except (KeyError, ValueError) as exc:
        raise HTTPException(400, str(exc)) from exc
    return _proposal_view(approval_id)


@router.post("/pr/{approval_id}/reject")
def reject_pr(approval_id: str) -> dict:
    """Reject a pending PR proposal."""
    try:
        _approvals.reject(approval_id)
    except (KeyError, ValueError) as exc:
        raise HTTPException(400, str(exc)) from exc
    return _proposal_view(approval_id)


@router.post("/pr/{approval_id}/execute")
async def execute_pr(approval_id: str) -> dict:
    """One-click: create the PR from the stored plan — only if approved."""
    if approval_id not in _proposals:
        raise HTTPException(404, "No such proposal")
    row = _proposals[approval_id]
    wf = _workflow()
    repo = await build_provider().get_repository(row["owner"], row["name"])
    try:
        outcome = await wf.execute(repo, row["plan"], approval_id)
    except PermissionError as exc:
        raise HTTPException(403, str(exc)) from exc
    row["pr_url"] = outcome.pr_url
    return outcome.model_dump()
