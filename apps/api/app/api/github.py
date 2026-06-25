"""GitHub integration endpoints — drive the live (or fake) provider.

Read endpoints are safe to demo against a real repository. The write/PR flow is
exposed but gated: it requires GitHub to be configured and runs against whatever
repo you point it at, so use a sandbox.
"""

from __future__ import annotations

import httpx
from fastapi import APIRouter, Depends, HTTPException
from github.manager import GitHubManager
from github.workflow import PRPlan
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import get_session
from app.db.models import ApprovalStatus, PRApproval
from app.github_execute import execute_live_pr, github_error_message
from app.github_runtime import build_provider, github_configured
from app.pr_approvals import PRApprovalStore

router = APIRouter(prefix="/github", tags=["github"])


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


# --- approval-gated write workflow (Phase 8.2 / 11), persisted to PostgreSQL ---


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


def _view(row: PRApproval) -> dict:
    plan = PRApprovalStore.plan_of(row)
    return {
        "approval_id": row.id,
        "status": ApprovalStatus(row.status).value,
        "repo": row.repository,
        "task": plan.task,
        "branch": plan.branch,
        "pr_title": plan.pr_title,
        "pr_summary": plan.pr_summary,
        "files_changed": sorted(plan.files.keys()),
        "testing": plan.testing,
        "pr_url": row.pr_url,
    }


@router.post("/pr/propose", status_code=201)
async def propose_pr(body: ProposePR, session: AsyncSession = Depends(get_session)) -> dict:
    """Propose a PR — persists a pending approval. Writes NOTHING to GitHub."""
    store = PRApprovalStore(session)
    row = await store.create(body.owner, body.name, _plan_from(body))
    return _view(row)


@router.get("/pr/pending")
async def list_pending(session: AsyncSession = Depends(get_session)) -> dict:
    """All pending PR proposals — the Approval Center's data source."""
    store = PRApprovalStore(session)
    return {"pending": [_view(r) for r in await store.pending()]}


@router.get("/pr/{approval_id}")
async def get_proposal(approval_id: str, session: AsyncSession = Depends(get_session)) -> dict:
    """A single proposal (metadata + changed files)."""
    row = await PRApprovalStore(session).get(approval_id)
    if row is None:
        raise HTTPException(404, "No such proposal")
    return _view(row)


@router.get("/pr/{approval_id}/diff")
async def get_diff(approval_id: str, session: AsyncSession = Depends(get_session)) -> dict:
    """The proposed file contents — powers the Diff Viewer before approval."""
    row = await PRApprovalStore(session).get(approval_id)
    if row is None:
        raise HTTPException(404, "No such proposal")
    plan = PRApprovalStore.plan_of(row)
    return {
        "approval_id": approval_id,
        "files": [{"path": p, "content": c} for p, c in sorted(plan.files.items())],
    }


@router.post("/pr/{approval_id}/approve")
async def approve_pr(approval_id: str, session: AsyncSession = Depends(get_session)) -> dict:
    """Approve a pending PR proposal."""
    try:
        row = await PRApprovalStore(session).decide(approval_id, ApprovalStatus.APPROVED, by=None)
    except KeyError as exc:
        raise HTTPException(404, "No such proposal") from exc
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    return _view(row)


@router.post("/pr/{approval_id}/reject")
async def reject_pr(approval_id: str, session: AsyncSession = Depends(get_session)) -> dict:
    """Reject a pending PR proposal."""
    try:
        row = await PRApprovalStore(session).decide(approval_id, ApprovalStatus.REJECTED, by=None)
    except KeyError as exc:
        raise HTTPException(404, "No such proposal") from exc
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    return _view(row)


@router.post("/pr/{approval_id}/execute")
async def execute_pr(approval_id: str, session: AsyncSession = Depends(get_session)) -> dict:
    """One-click: create the PR from the stored plan — only if approved."""
    from app.config import settings

    store = PRApprovalStore(session)
    row = await store.get(approval_id)
    if row is None:
        raise HTTPException(404, "No such proposal")
    if ApprovalStatus(row.status) != ApprovalStatus.APPROVED:
        raise HTTPException(403, f"Not approved (status={row.status}); refusing to write")

    plan = PRApprovalStore.plan_of(row)

    try:
        if github_configured():
            provider = build_provider()
            repo = await provider.get_repository(row.owner, row.name)
            branch, pr = await execute_live_pr(
                repo,
                plan,
                settings.github_token,
                author_name=settings.git_author_name,
                author_email=settings.git_author_email,
            )
        else:
            manager = GitHubManager(build_provider())
            repo = await build_provider().get_repository(row.owner, row.name)
            branch = await manager.create_branch(repo, plan.kind, plan.task)
            await manager.create_commit(repo, branch.name, plan.commit_message, plan.files)
            pr = await manager.create_pr(
                repo,
                title=plan.pr_title,
                summary=plan.pr_summary,
                changes=plan.changes,
                testing=plan.testing,
                head=branch.name,
            )
            branch = branch.name
    except (httpx.HTTPError, RuntimeError, NotImplementedError) as exc:
        raise HTTPException(502, github_error_message(exc)) from exc

    url = f"https://github.com/{row.owner}/{row.name}/pull/{pr.number}"
    await store.set_pr_url(approval_id, url)
    return {"approved": True, "branch": branch, "pr_number": pr.number, "pr_url": url}
