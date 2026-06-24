"""GitHub provider abstraction.

``GitHubProvider`` is the interface ForgeAI's services depend on. Two backends:
- ``RestGitHubProvider`` — real GitHub REST API via httpx (PAT auth).
- ``FakeGitHubProvider`` — in-memory simulation for offline tests; models the
  full lifecycle (branches, commits, PRs, reviews, CI) deterministically.

Following the project-wide pattern (ADR-0011/0015/0016/0017/0018), the entire
GitHub workflow is testable with no network and no token.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

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
)


class GitHubProvider(ABC):
    @abstractmethod
    async def get_repository(self, owner: str, name: str) -> Repository: ...

    @abstractmethod
    async def list_branches(self, repo: Repository) -> list[Branch]: ...

    @abstractmethod
    async def create_branch(self, repo: Repository, name: str, base: str) -> Branch: ...

    @abstractmethod
    async def create_commit(
        self, repo: Repository, branch: str, message: str, files: dict[str, str]
    ) -> Commit: ...

    @abstractmethod
    async def open_pull_request(
        self, repo: Repository, title: str, body: str, head: str, base: str
    ) -> PullRequest: ...

    @abstractmethod
    async def get_pull_request(self, repo: Repository, number: int) -> PullRequest: ...

    @abstractmethod
    async def merge_pull_request(
        self, repo: Repository, number: int
    ) -> PullRequest: ...

    @abstractmethod
    async def post_review(self, repo: Repository, review: Review) -> Review: ...

    @abstractmethod
    async def get_check_runs(self, repo: Repository, number: int) -> list[CheckRun]: ...

    @abstractmethod
    async def list_issues(self, repo: Repository) -> list[Issue]: ...


class FakeGitHubProvider(GitHubProvider):
    """In-memory GitHub. Deterministic; supports scripting CI outcomes so the
    'CI fails → fix → re-run → passes' loop can be tested."""

    def __init__(self, default_branch: str = "main"):
        self.default_branch = default_branch
        self.branches: dict[str, Branch] = {
            default_branch: Branch(name=default_branch, sha="base0")
        }
        self.commits: list[Commit] = []
        self.prs: dict[int, PullRequest] = {}
        self.reviews: dict[int, Review] = {}
        self.issues: list[Issue] = []
        self._pr_counter = 0
        self._sha_counter = 0
        # pr_number -> list of CI outcomes to return on successive checks.
        self._ci_script: dict[int, list[CIStatus]] = {}

    def _next_sha(self) -> str:
        self._sha_counter += 1
        return f"sha{self._sha_counter:04d}"

    async def get_repository(self, owner: str, name: str) -> Repository:
        return Repository(
            owner=owner,
            name=name,
            default_branch=self.default_branch,
            clone_url=f"https://github.com/{owner}/{name}.git",
        )

    async def list_branches(self, repo: Repository) -> list[Branch]:
        return list(self.branches.values())

    async def create_branch(self, repo: Repository, name: str, base: str) -> Branch:
        if name in self.branches:
            raise ValueError(f"Branch already exists: {name}")
        if base not in self.branches:
            raise ValueError(f"Base branch not found: {base}")
        branch = Branch(name=name, sha=self.branches[base].sha)
        self.branches[name] = branch
        return branch

    async def create_commit(self, repo, branch, message, files) -> Commit:
        if branch not in self.branches:
            raise ValueError(f"Branch not found: {branch}")
        commit = Commit(sha=self._next_sha(), message=message, branch=branch)
        self.branches[branch].sha = commit.sha
        self.commits.append(commit)
        return commit

    async def open_pull_request(self, repo, title, body, head, base) -> PullRequest:
        self._pr_counter += 1
        pr = PullRequest(
            number=self._pr_counter, title=title, body=body, head=head, base=base
        )
        self.prs[pr.number] = pr
        return pr

    async def get_pull_request(self, repo, number) -> PullRequest:
        return self.prs[number]

    async def merge_pull_request(self, repo, number) -> PullRequest:
        pr = self.prs[number]
        pr.state = PRState.MERGED
        return pr

    async def post_review(self, repo, review) -> Review:
        self.reviews[review.pr_number] = review
        return review

    async def get_check_runs(self, repo, number) -> list[CheckRun]:
        script = self._ci_script.get(number)
        status = script.pop(0) if script else CIStatus.SUCCESS
        logs = (
            "ModuleNotFoundError: No module named 'jwt'"
            if status == CIStatus.FAILURE
            else ""
        )
        return [CheckRun(pr_number=number, name="ci", status=status, logs=logs)]

    async def list_issues(self, repo) -> list[Issue]:
        return list(self.issues)

    # --- test helpers ---
    def script_ci(self, pr_number: int, statuses: list[CIStatus]) -> None:
        """Queue CI outcomes for a PR (consumed one per get_check_runs call)."""
        self._ci_script[pr_number] = list(statuses)
