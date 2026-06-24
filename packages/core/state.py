"""ProjectState — the single shared state object for a workflow run.

Every agent reads from and writes to this object instead of passing dozens of
variables around (see the Phase 2 design). LangGraph threads one instance
through the whole graph.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field

from core.messages import AgentMessage, TaskSpec


class ReviewVerdict(StrEnum):
    """Outcome of the Review agent."""

    APPROVED = "approved"
    CHANGES_REQUESTED = "changes_requested"
    PENDING = "pending"


class ProjectState(BaseModel):
    """Shared state threaded through the agent workflow.

    Field names match the Phase 2 ``ProjectState`` design so the docs and the
    code stay in lockstep.
    """

    # --- input ---
    user_request: str
    project_id: str | None = None
    project_path: str | None = None

    # --- planning ---
    tasks: list[TaskSpec] = Field(default_factory=list)
    current_task: TaskSpec | None = None

    # --- context gathered by Research + Memory ---
    project_context: str = ""
    retrieved_docs: list[str] = Field(default_factory=list)

    # --- work products ---
    generated_code: dict[str, str] = Field(default_factory=dict)  # path -> content
    execution_logs: list[str] = Field(default_factory=list)
    test_passed: bool | None = None
    review_feedback: str = ""
    review_verdict: ReviewVerdict = ReviewVerdict.PENDING

    # --- control flow ---
    retry_count: int = 0
    max_retries: int = 2
    needs_reflection: bool = False

    # --- GitHub PR proposal (gated; set by the Git agent, executed after approval) ---
    pr_branch: str | None = None
    pr_title: str | None = None
    pr_approval_id: str | None = None  # the human must approve this before any write
    pr_url: str | None = None  # set only once an approved proposal is executed

    # --- audit trail ---
    messages: list[AgentMessage] = Field(default_factory=list)

    # --- output ---
    final_response: str = ""

    def record(self, message: AgentMessage) -> None:
        """Append an agent message to the audit trail."""
        self.messages.append(message)
