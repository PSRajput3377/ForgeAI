"""GitHubWorkflow — approval-gated branch → commit → PR.

Two phases, so nothing is written to GitHub without explicit human approval:

    propose()  → prepare the plan + open an approval request   (NO writes)
    approve the request
    execute()  → create branch → commit → open PR → return URL  (writes)

This is the safer, governance-first model: the agent drafts a PR proposal, a
human approves, *then* the PR is created. ``execute()`` refuses to run on an
unapproved request.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from github.approval import ApprovalRequest, ApprovalService
from github.manager import GitHubManager
from github.models import Repository


class PRPlan(BaseModel):
    """What the workflow will do once approved (the proposal)."""

    kind: str
    task: str
    branch: str
    commit_message: str
    files: dict[str, str] = Field(default_factory=dict)
    pr_title: str
    pr_summary: str
    changes: list[str] = Field(default_factory=list)
    testing: str = ""


class WorkflowOutcome(BaseModel):
    approved: bool
    branch: str | None = None
    pr_number: int | None = None
    pr_url: str | None = None
    timeline: list[str] = Field(default_factory=list)


class GitHubWorkflow:
    """Drives the approval-gated PR workflow."""

    def __init__(self, manager: GitHubManager, approvals: ApprovalService):
        self.manager = manager
        self.approvals = approvals

    def propose(self, repo: Repository, plan: PRPlan) -> ApprovalRequest:
        """Open an approval request describing the PR. Writes NOTHING to GitHub."""
        return self.approvals.request(
            "create_pr",
            summary=f"Open PR '{plan.pr_title}' on {repo.full_name}",
            repo=repo.full_name,
            branch=plan.branch,
            pr_title=plan.pr_title,
            files=sorted(plan.files.keys()),
        )

    async def execute(self, repo: Repository, plan: PRPlan, request_id: str) -> WorkflowOutcome:
        """Execute the plan — but only if the approval request is approved.

        Raises PermissionError if the request is missing or not approved, so a
        write can never happen without an explicit human decision.
        """
        req = self.approvals.get(request_id)
        if req is None:
            raise PermissionError(f"Unknown approval request: {request_id}")
        if not req.is_approved:
            raise PermissionError(
                f"PR creation not approved (status={req.status}); refusing to write"
            )

        timeline: list[str] = []
        branch = await self.manager.create_branch(repo, plan.kind, plan.task)
        timeline.append(f"Created branch {branch.name}")

        await self.manager.create_commit(repo, branch.name, plan.commit_message, plan.files)
        timeline.append(f"Committed: {plan.commit_message}")

        pr = await self.manager.create_pr(
            repo,
            title=plan.pr_title,
            summary=plan.pr_summary,
            changes=plan.changes,
            testing=plan.testing,
            head=branch.name,
        )
        url = f"https://github.com/{repo.full_name}/pull/{pr.number}"
        timeline.append(f"Opened PR #{pr.number}")

        return WorkflowOutcome(
            approved=True,
            branch=branch.name,
            pr_number=pr.number,
            pr_url=url,
            timeline=timeline,
        )
