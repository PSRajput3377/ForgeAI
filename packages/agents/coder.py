"""CoderAgent — the engineer. Writes code from task + context. Never guesses."""

from __future__ import annotations

from core.messages import AgentMessage, MessageStatus
from core.roles import AgentRole
from core.state import ProjectState

from agents.base import BaseAgent


class CoderAgent(BaseAgent):
    role = AgentRole.CODER

    async def run(self, state: ProjectState) -> ProjectState:
        task = state.current_task
        title = task.title if task else state.user_request
        context = "\n".join(state.retrieved_docs)

        code = await self._ask(f"Task: {title}\nContext:\n{context}\nWrite the code.")

        # Phase 2 skeleton: record the generated artifact under a placeholder
        # path. Phase 4/5 replace this with real multi-file generation + tools.
        state.generated_code["generated/output.txt"] = code
        # If reflection produced a fix, consume it so a retry differs.
        if state.review_feedback:
            state.generated_code["generated/output.txt"] += f"\n# applied: {state.review_feedback}"

        task_id = task.task_id if task else "n/a"
        state.record(
            AgentMessage(
                task_id=task_id,
                sender=self.role,
                status=MessageStatus.COMPLETED,
                summary="Generated code",
                files_changed=list(state.generated_code.keys()),
            )
        )
        return state
