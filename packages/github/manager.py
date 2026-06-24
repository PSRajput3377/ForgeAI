"""GitHubManager — orchestrates the autonomous development workflow.

Composes the services into the end-to-end loop a junior engineer follows:

    branch → commit → open PR → review → watch CI
           → (CI fails → classify → fix → commit → re-run)* → merge

The *fixer* is injected (the Reflection/Coder agents supply the real one,
exactly like the Phase 5 ExecutionEngine), so CI self-correction is decoupled
and testable offline with the FakeGitHubProvider.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from execution.errors import ClassifiedError
from pydantic import BaseModel, Field

from github.models import CIStatus, PullRequest, Repository, Review
from github.provider import GitHubProvider
from github.services import BranchService, CIService, CommitService, PullRequestService

# Fixer: given the CI failure, apply a fix and return the files to commit, or
# None if it can't help.
CIFixer = Callable[[ClassifiedError], Awaitable[dict[str, str] | None]]


class WorkflowResult(BaseModel):
    branch: str
    pr_number: int
    merged: bool
    ci_status: CIStatus
    ci_attempts: int = 0
    review_approved: bool = False
    timeline: list[str] = Field(default_factory=list)


class GitHubManager:
    """End-to-end GitHub automation for one task."""

    def __init__(self, provider: GitHubProvider, max_ci_retries: int = 3):
        self.provider = provider
        self.branches = BranchService(provider)
        self.commits = CommitService(provider)
        self.prs = PullRequestService(provider)
        self.ci = CIService(provider)
        self.max_ci_retries = max_ci_retries

    # --- discrete operations (composable; used by GitHubWorkflow) ---

    async def create_branch(self, repo, kind: str, task: str):
        """Create a conventional task branch off the default branch."""
        return await self.branches.create_task_branch(repo, kind, task)

    async def create_commit(
        self, repo, branch: str, message: str, files: dict[str, str]
    ):
        """Commit files to a branch."""
        return await self.commits.commit(repo, branch, message, files)

    async def create_pr(
        self, repo, *, title, summary, changes, testing, head, base=None
    ):
        """Open a pull request with a structured body. Returns the PullRequest."""
        return await self.prs.open(
            repo,
            title,
            summary,
            changes,
            testing,
            head=head,
            base=base or repo.default_branch,
        )

    async def get_review_status(self, repo, pr_number: int):
        """Return the current CI status + any classified failure for a PR."""
        return await self.ci.poll(repo, pr_number)

    async def sync_repository(self, repo):
        """Refresh repo state (branches) — the hook for pull→re-index→memory."""
        branches = await self.provider.list_branches(repo)
        return {"branches": [b.name for b in branches]}

    async def run_task(
        self,
        repo: Repository,
        *,
        kind: str,
        task: str,
        commit_message: str,
        files: dict[str, str],
        pr_title: str,
        pr_summary: str,
        changes: list[str],
        testing: str,
        reviewer: Callable[[PullRequest], Awaitable[Review]] | None = None,
        ci_fixer: CIFixer | None = None,
        auto_merge: bool = False,
    ) -> WorkflowResult:
        """Execute the full branch→PR→CI→(fix)→merge workflow for one task."""
        timeline: list[str] = []

        branch = await self.branches.create_task_branch(repo, kind, task)
        timeline.append(f"Created branch {branch.name}")

        await self.commits.commit(repo, branch.name, commit_message, files)
        timeline.append(f"Committed: {commit_message}")

        pr = await self.prs.open(
            repo,
            pr_title,
            pr_summary,
            changes,
            testing,
            head=branch.name,
            base=repo.default_branch,
        )
        timeline.append(f"Opened PR #{pr.number}")

        review_approved = False
        if reviewer is not None:
            review = await reviewer(pr)
            await self.provider.post_review(repo, review)
            review_approved = review.approved
            timeline.append(
                f"Review: {'approved' if review.approved else 'changes requested'} "
                f"({len(review.comments)} comments)"
            )

        # Watch CI and self-correct on failure. One poll per iteration.
        ci_status, error = await self.ci.poll(repo, pr.number)
        attempts = 0
        while ci_status == CIStatus.FAILURE and attempts < self.max_ci_retries:
            timeline.append(f"CI failed: {error.category if error else 'unknown'}")
            if ci_fixer is None or error is None:
                break
            fix_files = await ci_fixer(error)
            if not fix_files:
                break
            attempts += 1
            await self.commits.commit(
                repo,
                branch.name,
                f"fix: address CI failure (attempt {attempts})",
                fix_files,
            )
            timeline.append(f"Pushed CI fix (attempt {attempts}); re-running")
            ci_status, error = await self.ci.poll(repo, pr.number)

        if ci_status == CIStatus.SUCCESS:
            timeline.append("CI passed")

        merged = False
        if (
            auto_merge
            and ci_status == CIStatus.SUCCESS
            and (reviewer is None or review_approved)
        ):
            await self.prs.merge(repo, pr.number)
            merged = True
            timeline.append(f"Merged PR #{pr.number}")

        return WorkflowResult(
            branch=branch.name,
            pr_number=pr.number,
            merged=merged,
            ci_status=ci_status,
            ci_attempts=attempts,
            review_approved=review_approved,
            timeline=timeline,
        )
