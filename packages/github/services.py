"""GitHub services — focused operations the manager composes.

Each service wraps the provider for one concern (branches, commits, PRs,
reviews, CI). Kept thin so the provider stays the single integration seam.
"""

from __future__ import annotations

import re

from execution.errors import ClassifiedError, classify_error

from github.models import (
    Branch,
    CheckRun,
    CIStatus,
    Commit,
    PullRequest,
    Repository,
)
from github.provider import GitHubProvider

# Conventional branch prefixes by task kind.
_BRANCH_PREFIX = {
    "feature": "feature",
    "feat": "feature",
    "bug": "fix",
    "fix": "fix",
    "docs": "docs",
}


def branch_name_for(kind: str, task: str) -> str:
    """Generate a conventional branch name, e.g. feature/jwt-auth."""
    prefix = _BRANCH_PREFIX.get(kind.lower(), "feature")
    slug = re.sub(r"[^a-z0-9]+", "-", task.lower()).strip("-")[:40]
    return f"{prefix}/{slug}"


class BranchService:
    def __init__(self, provider: GitHubProvider):
        self.provider = provider

    async def create_task_branch(
        self, repo: Repository, kind: str, task: str
    ) -> Branch:
        return await self.provider.create_branch(
            repo, branch_name_for(kind, task), repo.default_branch
        )


class CommitService:
    def __init__(self, provider: GitHubProvider):
        self.provider = provider

    async def commit(
        self, repo: Repository, branch: str, message: str, files: dict[str, str]
    ) -> Commit:
        return await self.provider.create_commit(repo, branch, message, files)


class PullRequestService:
    def __init__(self, provider: GitHubProvider):
        self.provider = provider

    def render_body(self, summary: str, changes: list[str], testing: str) -> str:
        """Generate a structured PR description."""
        change_lines = "\n".join(f"- {c}" for c in changes) or "- (see diff)"
        return (
            f"## Summary\n\n{summary}\n\n"
            f"## Changes\n\n{change_lines}\n\n"
            f"## Testing\n\n{testing}\n"
        )

    async def open(
        self, repo, title, summary, changes, testing, head, base="main"
    ) -> PullRequest:
        body = self.render_body(summary, changes, testing)
        return await self.provider.open_pull_request(repo, title, body, head, base)

    async def merge(self, repo, number) -> PullRequest:
        return await self.provider.merge_pull_request(repo, number)


class CIService:
    """Watches CI and classifies failures (reusing the Phase 5 classifier)."""

    def __init__(self, provider: GitHubProvider):
        self.provider = provider

    @staticmethod
    def _status(runs: list[CheckRun]) -> CIStatus:
        if any(r.status == CIStatus.FAILURE for r in runs):
            return CIStatus.FAILURE
        if runs and all(r.status == CIStatus.SUCCESS for r in runs):
            return CIStatus.SUCCESS
        return CIStatus.PENDING

    async def poll(
        self, repo: Repository, pr_number: int
    ) -> tuple[CIStatus, ClassifiedError | None]:
        """Fetch check runs ONCE and return (status, classified failure or None).

        A single fetch per poll avoids double-consuming providers that stream
        check results.
        """
        runs = await self.provider.get_check_runs(repo, pr_number)
        status = self._status(runs)
        error = None
        if status == CIStatus.FAILURE:
            failed = next(r for r in runs if r.status == CIStatus.FAILURE)
            error = classify_error(failed.logs)
        return status, error
