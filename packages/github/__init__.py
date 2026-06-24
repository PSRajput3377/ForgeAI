"""github — GitHub integration & autonomous development workflow.

ForgeAI acts like a junior engineer on a repo: branch → commit → open PR →
review → watch CI → fix failures → merge. Orchestrated by ``GitHubManager`` over
a ``GitHubProvider`` (RestGitHubProvider in prod, FakeGitHubProvider offline).

CI failure analysis reuses the Phase 5 error classifier; CI self-correction
mirrors the ExecutionEngine's injected-fixer pattern. (ADR-0019)
"""

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
from github.services import (
    BranchService,
    CIService,
    CommitService,
    PullRequestService,
    branch_name_for,
)

__all__ = [
    "Branch",
    "BranchService",
    "CheckRun",
    "CIFixer",
    "CIService",
    "CIStatus",
    "Commit",
    "CommitService",
    "FakeGitHubProvider",
    "GitHubManager",
    "GitHubProvider",
    "Issue",
    "PRState",
    "PullRequest",
    "PullRequestService",
    "Repository",
    "Review",
    "ReviewComment",
    "WorkflowResult",
    "branch_name_for",
]
