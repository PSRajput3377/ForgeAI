"""Wire agent runs to durable GitHub PR proposals (Approval Center).

When ``GITHUB_OWNER`` + ``GITHUB_REPO`` are set, completed runs with generated
code propose a gated PR — persisted to PostgreSQL, visible in Pending Approvals.
"""

from __future__ import annotations

from github.approval import ApprovalRequest, ApprovalStatus
from github.models import Repository
from github.services import branch_name_for
from github.workflow import PRPlan
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.github_runtime import github_configured
from app.pr_approvals import PRApprovalStore
from core.state import ProjectState, ReviewVerdict


class CollectingGitHubWorkflow:
    """Captures ``propose()`` calls from the Git agent; persists after the run."""

    def __init__(self) -> None:
        self.collected: PRPlan | None = None

    def propose(self, repo: Repository, plan: PRPlan) -> ApprovalRequest:
        if plan.files:
            normalized = plan.model_copy(
                update={"branch": plan.branch or branch_name_for(plan.kind, plan.task)}
            )
            self.collected = normalized
        return ApprovalRequest(
            id="pending-persist",
            action="create_pr",
            summary=f"Open PR '{plan.pr_title}' on {repo.full_name}",
            status=ApprovalStatus.PENDING,
        )


def github_auto_propose_enabled() -> bool:
    return bool(github_configured() and settings.github_owner and settings.github_repo)


async def persist_agent_pr_proposal(session: AsyncSession, state: ProjectState) -> str | None:
    """Save a collected PR plan to the database. Returns the approval id."""
    if not github_auto_propose_enabled():
        return None
    if state.review_verdict != ReviewVerdict.APPROVED:
        return None
    if not state.generated_code:
        return None

    # Rebuild plan from state if the Git agent did not wire a collector (fallback).
    plan = _plan_from_state(state)
    if plan is None:
        return None

    row = await PRApprovalStore(session).create(
        settings.github_owner,
        settings.github_repo,
        plan,
    )
    return row.id


def _plan_from_state(state: ProjectState) -> PRPlan | None:
    if not state.generated_code:
        return None
    commit_message = state.pr_title or f"feat: {state.user_request[:60]}"
    return PRPlan(
        kind="feature",
        task=state.user_request,
        branch=state.pr_branch or branch_name_for("feature", state.user_request),
        commit_message=commit_message[:100],
        files=dict(state.generated_code),
        pr_title=commit_message[:100],
        pr_summary=state.user_request,
        changes=sorted(state.generated_code.keys()),
        testing="tests passed" if state.test_passed else "tests not run",
    )
