"""RestGitHubProvider — the real GitHub REST API backend (httpx + PAT).

Used in production. Imports/network only happen when this class is used; tests
run against FakeGitHubProvider. Commit creation here delegates file writes to
git (the Phase 3 GitTool / local clone); the REST calls cover refs, PRs,
reviews, and checks.
"""

from __future__ import annotations

import httpx

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
from github.provider import GitHubProvider

_CI_MAP = {
    "success": CIStatus.SUCCESS,
    "failure": CIStatus.FAILURE,
    "in_progress": CIStatus.RUNNING,
    "queued": CIStatus.PENDING,
}


class RestGitHubProvider(GitHubProvider):
    """GitHub REST v3 client. Implements the GitHubProvider interface."""

    def __init__(self, token: str, api_url: str = "https://api.github.com"):
        self.token = token
        self.api_url = api_url.rstrip("/")

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    async def _request(self, method: str, path: str, **kwargs):
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.request(
                method, f"{self.api_url}{path}", headers=self._headers(), **kwargs
            )
            resp.raise_for_status()
            return resp.json() if resp.content else {}

    async def get_repository(self, owner: str, name: str) -> Repository:
        data = await self._request("GET", f"/repos/{owner}/{name}")
        return Repository(
            owner=owner,
            name=name,
            default_branch=data.get("default_branch", "main"),
            clone_url=data.get("clone_url", ""),
        )

    async def list_branches(self, repo: Repository) -> list[Branch]:
        data = await self._request("GET", f"/repos/{repo.full_name}/branches")
        return [Branch(name=b["name"], sha=b["commit"]["sha"]) for b in data]

    async def create_branch(self, repo: Repository, name: str, base: str) -> Branch:
        ref = await self._request(
            "GET", f"/repos/{repo.full_name}/git/ref/heads/{base}"
        )
        base_sha = ref["object"]["sha"]
        await self._request(
            "POST",
            f"/repos/{repo.full_name}/git/refs",
            json={"ref": f"refs/heads/{name}", "sha": base_sha},
        )
        return Branch(name=name, sha=base_sha)

    async def create_commit(self, repo, branch, message, files) -> Commit:
        # Real commits are produced by git against a local clone (GitTool); the
        # REST contents API is used for single-file edits. Kept minimal here.
        raise NotImplementedError(
            "Use the local clone + GitTool to author commits; REST is used for refs/PRs."
        )

    async def open_pull_request(self, repo, title, body, head, base) -> PullRequest:
        data = await self._request(
            "POST",
            f"/repos/{repo.full_name}/pulls",
            json={"title": title, "body": body, "head": head, "base": base},
        )
        return PullRequest(
            number=data["number"], title=title, body=body, head=head, base=base
        )

    async def get_pull_request(self, repo, number) -> PullRequest:
        d = await self._request("GET", f"/repos/{repo.full_name}/pulls/{number}")
        state = PRState.MERGED if d.get("merged") else PRState(d["state"])
        return PullRequest(
            number=number,
            title=d["title"],
            body=d.get("body") or "",
            head=d["head"]["ref"],
            base=d["base"]["ref"],
            state=state,
        )

    async def merge_pull_request(self, repo, number) -> PullRequest:
        await self._request("PUT", f"/repos/{repo.full_name}/pulls/{number}/merge")
        pr = await self.get_pull_request(repo, number)
        pr.state = PRState.MERGED
        return pr

    async def post_review(self, repo, review) -> Review:
        event = "APPROVE" if review.approved else "REQUEST_CHANGES"
        comments = [
            {"path": c.path, "line": c.line or 1, "body": c.body}
            for c in review.comments
            if c.line is not None
        ]
        await self._request(
            "POST",
            f"/repos/{repo.full_name}/pulls/{review.pr_number}/reviews",
            json={"body": review.summary, "event": event, "comments": comments},
        )
        return review

    async def get_check_runs(self, repo, number) -> list[CheckRun]:
        pr = await self.get_pull_request(repo, number)
        ref = await self._request(
            "GET", f"/repos/{repo.full_name}/git/ref/heads/{pr.head}"
        )
        sha = ref["object"]["sha"]
        data = await self._request(
            "GET", f"/repos/{repo.full_name}/commits/{sha}/check-runs"
        )
        runs = []
        for r in data.get("check_runs", []):
            status = _CI_MAP.get(
                r.get("conclusion") or r.get("status"), CIStatus.PENDING
            )
            runs.append(CheckRun(pr_number=number, name=r["name"], status=status))
        return runs

    async def list_issues(self, repo) -> list[Issue]:
        data = await self._request("GET", f"/repos/{repo.full_name}/issues")
        return [
            Issue(
                number=i["number"],
                title=i["title"],
                body=i.get("body") or "",
                labels=[lbl["name"] for lbl in i.get("labels", [])],
            )
            for i in data
            if "pull_request" not in i
        ]
