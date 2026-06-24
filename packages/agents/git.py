"""GitAgent — drafts a commit message and (when wired) proposes a gated PR.

When a ``GitHubWorkflow`` is provided (Phase 8.2), the agent assembles a
``PRPlan`` from the run's generated code + results and calls ``workflow.propose``
— which opens an approval request and **writes nothing**. A human approves out
of band (the API), and only then is the PR executed. The agent never
auto-creates a PR (ADR-0023).

Without a workflow (the offline default), it falls back to producing a
conventional-commit message only.
"""

from __future__ import annotations

from core.messages import AgentMessage, MessageStatus
from core.roles import AgentRole
from core.state import ProjectState

from agents.base import BaseAgent


class GitAgent(BaseAgent):
    role = AgentRole.GIT

    def __init__(self, router, workflow=None, repo=None):
        super().__init__(router)
        # workflow: GitHubWorkflow; repo: github.models.Repository. Both optional.
        self.workflow = workflow
        self.repo = repo

    async def run(self, state: ProjectState) -> ProjectState:
        message = await self._ask(f"Write a conventional-commit message for: {state.user_request}")
        commit_message = message.splitlines()[0][:100] if message else "chore: update"
        task_id = state.current_task.task_id if state.current_task else "n/a"

        if self.workflow is not None and self.repo is not None:
            # Build a PR proposal from the run's work products. Gated: propose
            # opens an approval request and writes nothing.
            from github.workflow import PRPlan

            files = dict(state.generated_code)
            plan = PRPlan(
                kind="feature",
                task=state.user_request,
                branch="",  # filled by the workflow's branch namer on execute
                commit_message=commit_message,
                files=files,
                pr_title=commit_message,
                pr_summary=state.user_request,
                changes=sorted(files.keys()),
                testing="tests passed" if state.test_passed else "tests not run",
            )
            request = self.workflow.propose(self.repo, plan)
            state.pr_branch = plan.branch or None
            state.pr_title = plan.pr_title
            state.pr_approval_id = request.id
            summary = f"Proposed PR (approval required: {request.id})"
            payload = {
                "commit_message": commit_message,
                "approval_id": request.id,
                "pr_title": plan.pr_title,
                "status": request.status.value,
            }
        else:
            summary = "Prepared commit (not yet pushed)"
            payload = {"commit_message": commit_message}

        state.record(
            AgentMessage(
                task_id=task_id,
                sender=self.role,
                status=MessageStatus.COMPLETED,
                summary=summary,
                payload=payload,
            )
        )
        return state
