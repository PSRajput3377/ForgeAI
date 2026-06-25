"""Live GitHub PR execution — clone, commit, push via git, then open PR via REST.

RestGitHubProvider intentionally does not author commits over the REST API
(ADR-0020). This module implements the real write path for ``execute``.
"""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

import httpx
from github.local_repo import GitCommandError, LocalRepository
from github.models import PullRequest, Repository
from github.rest_provider import RestGitHubProvider
from github.services import PullRequestService, branch_name_for
from github.workflow import PRPlan


def _clone_url(repo: Repository, token: str) -> str:
    base = repo.clone_url or f"https://github.com/{repo.full_name}.git"
    if base.startswith("https://") and "x-access-token@" not in base:
        return base.replace("https://", f"https://x-access-token:{token}@", 1)
    return base


async def execute_live_pr(
    repo: Repository,
    plan: PRPlan,
    token: str,
    *,
    author_name: str = "ForgeAI",
    author_email: str = "forgeai@users.noreply.github.com",
) -> tuple[str, PullRequest]:
    """Clone → branch → commit → push → open PR. Raises on git/GitHub errors."""
    branch = plan.branch or branch_name_for(plan.kind, plan.task)
    work = Path(tempfile.mkdtemp(prefix="forgeai-clone-"))
    try:
        local = await LocalRepository.clone(
            _clone_url(repo, token),
            work,
            depth=None,
            author_name=author_name,
            author_email=author_email,
        )
        await local.create_branch(branch)
        await local.commit_all(branch, plan.commit_message, plan.files)
        await local.push(branch)
    except GitCommandError as exc:
        raise RuntimeError(str(exc)) from exc
    finally:
        shutil.rmtree(work, ignore_errors=True)

    provider = RestGitHubProvider(token=token)
    prs = PullRequestService(provider)
    pr = await prs.open(
        repo,
        plan.pr_title,
        plan.pr_summary,
        plan.changes,
        plan.testing,
        head=branch,
        base=repo.default_branch,
    )
    return branch, pr


def github_error_message(exc: Exception) -> str:
    """Turn git/httpx failures into actionable API error text."""
    if isinstance(exc, httpx.HTTPStatusError):
        status = exc.response.status_code
        if status == 403:
            return (
                "GitHub refused the write (403). Regenerate GITHUB_TOKEN with "
                "Contents + Pull requests read/write on forge-demo-fastapi-, "
                "owned by the same account as the repo."
            )
        if status == 404:
            return "GitHub repository not found or token cannot access it (404)."
        return f"GitHub API error ({status}): {exc.response.text[:200]}"
    msg = str(exc)
    if "git push" in msg.lower() or "403" in msg:
        return f"{msg} — check GITHUB_TOKEN has push access to the repository."
    return msg
