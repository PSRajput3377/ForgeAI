"""GitHub domain models — the shapes ForgeAI works with.

Provider-agnostic: a real REST provider and the offline fake both produce these.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class PRState(StrEnum):
    OPEN = "open"
    CLOSED = "closed"
    MERGED = "merged"


class CIStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILURE = "failure"


class Repository(BaseModel):
    owner: str
    name: str
    default_branch: str = "main"
    clone_url: str = ""

    @property
    def full_name(self) -> str:
        return f"{self.owner}/{self.name}"


class Branch(BaseModel):
    name: str
    sha: str = ""


class Commit(BaseModel):
    sha: str
    message: str
    branch: str = ""


class PullRequest(BaseModel):
    number: int
    title: str
    body: str = ""
    head: str  # source branch
    base: str = "main"  # target branch
    state: PRState = PRState.OPEN
    files_changed: list[str] = Field(default_factory=list)


class ReviewComment(BaseModel):
    path: str
    line: int | None = None
    body: str
    severity: str = "info"  # info | suggestion | warning | security


class Review(BaseModel):
    pr_number: int
    approved: bool
    summary: str = ""
    comments: list[ReviewComment] = Field(default_factory=list)


class CheckRun(BaseModel):
    pr_number: int
    name: str
    status: CIStatus
    logs: str = ""


class Issue(BaseModel):
    number: int
    title: str
    body: str = ""
    labels: list[str] = Field(default_factory=list)
