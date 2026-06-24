"""GitHub integration endpoints — drive the live (or fake) provider.

Read endpoints are safe to demo against a real repository. The write/PR flow is
exposed but gated: it requires GitHub to be configured and runs against whatever
repo you point it at, so use a sandbox.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.github_runtime import build_provider, github_configured

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
