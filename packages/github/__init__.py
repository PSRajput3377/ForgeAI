"""github — GitHub integration & autonomous development workflow.

ForgeAI acts like a junior engineer on a repo: branch → commit → open PR →
review → watch CI → fix failures → merge. Orchestrated by ``GitHubManager`` over
a ``GitHubProvider`` (RestGitHubProvider in prod, FakeGitHubProvider offline).

CI failure analysis reuses the Phase 5 error classifier; CI self-correction
mirrors the ExecutionEngine's injected-fixer pattern. (ADR-0019)
"""

from github.approval import ApprovalRequest, ApprovalService, ApprovalStatus
from github.local_repo import CommitResult, GitCommandError, LocalRepository
from github.manager import CIFixer, GitHubManager, WorkflowResult
from github.models import (
    Branch,
    CheckRun,
    CIStatus,
    Commit,
    Issue,
    PRState,
    PullRequest,
    Repository,
    Review,
    ReviewComment,
)
from github.provider import FakeGitHubProvider, GitHubProvider
from github.rest_provider import RestGitHubProvider
from github.rest_support import (
    paginate,
    parse_next_link,
    request_with_backoff,
    retry_after_seconds,
)
from github.services import (
    BranchService,
    CIService,
    CommitService,
    PullRequestService,
    branch_name_for,
)
from github.webhooks import map_webhook, verify_signature
from github.workflow import GitHubWorkflow, PRPlan, WorkflowOutcome

__all__ = [
    "ApprovalRequest",
    "ApprovalService",
    "ApprovalStatus",
    "Branch",
    "BranchService",
    "GitHubWorkflow",
    "PRPlan",
    "WorkflowOutcome",
    "CheckRun",
    "CIFixer",
    "CIService",
    "CIStatus",
    "Commit",
    "CommitResult",
    "CommitService",
    "FakeGitHubProvider",
    "GitCommandError",
    "GitHubManager",
    "GitHubProvider",
    "Issue",
    "LocalRepository",
    "PRState",
    "PullRequest",
    "PullRequestService",
    "Repository",
    "RestGitHubProvider",
    "Review",
    "ReviewComment",
    "WorkflowResult",
    "branch_name_for",
    "map_webhook",
    "paginate",
    "parse_next_link",
    "request_with_backoff",
    "retry_after_seconds",
    "verify_signature",
]
