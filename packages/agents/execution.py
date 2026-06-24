"""ExecutionAgent — runs the generated code's commands and collects logs.

Phase 2 skeleton simulates execution. Real command execution happens inside the
Docker sandbox in Phase 8; this agent will then drive the Terminal/Docker tool.
"""

from __future__ import annotations

from core.messages import AgentMessage, MessageStatus
from core.roles import AgentRole
from core.state import ProjectState

from agents.base import BaseAgent


class ExecutionAgent(BaseAgent):
    role = AgentRole.EXECUTION

    async def run(self, state: ProjectState) -> ProjectState:
        # Placeholder: pretend the build/install ran. Phase 8 runs real commands
        # in Docker and captures stdout/stderr/exit codes.
        state.execution_logs.append("[execution] simulated build: exit 0")
        task_id = state.current_task.task_id if state.current_task else "n/a"
        state.record(
            AgentMessage(
                task_id=task_id,
                sender=self.role,
                status=MessageStatus.COMPLETED,
                summary="Executed build (simulated)",
                payload={"exit_code": 0},
            )
        )
        return state
