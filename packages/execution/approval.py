"""Human approval gates.

Some actions (delete files, git push, merge PR, deploy) require a human to
approve before the agent proceeds. The gate pauses by asking an approver
callback; the default denies (safe by default). A run can be configured to
auto-approve specific actions in trusted contexts.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from enum import StrEnum

# An approver receives the action name + details and returns True to allow.
Approver = Callable[[str, dict], Awaitable[bool]]


class GatedAction(StrEnum):
    DELETE_FILES = "delete_files"
    GIT_PUSH = "git_push"
    MERGE_PR = "merge_pr"
    DEPLOY = "deploy"


async def deny_all(action: str, details: dict) -> bool:
    """Default approver: deny everything (safe by default)."""
    return False


class ApprovalGate:
    """Checks whether a gated action may proceed."""

    def __init__(
        self,
        approver: Approver | None = None,
        auto_approve: set[GatedAction] | None = None,
    ):
        self.approver = approver or deny_all
        self.auto_approve = auto_approve or set()

    async def request(self, action: GatedAction, **details) -> bool:
        """Return True if the action is permitted."""
        if action in self.auto_approve:
            return True
        return await self.approver(action.value, details)
