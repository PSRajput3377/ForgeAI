"""The MemoryAgent uses the ContextBuilder inside the full workflow (offline)."""

import pytest
from agents.workflow import build_workflow
from core.roles import AgentRole
from core.state import ProjectState
from memory.context_builder import ContextBuilder
from memory.manager import MemoryManager
from memory.store import InMemoryStore
from memory.types import MemoryScope as Scope


@pytest.mark.asyncio
async def test_memory_agent_injects_project_context(echo_router):
    mem = MemoryManager(InMemoryStore())
    await mem.store_memory(
        Scope.PROJECT, "stack", "Tailwind + Zustand + TypeScript", project_id="p1"
    )
    builder = ContextBuilder(mem)

    app = build_workflow(echo_router, context_builder=builder)
    state = ProjectState(user_request="Add dark mode", project_id="p1")
    result = ProjectState.model_validate(await app.ainvoke(state))

    # The project's remembered stack made it into the shared context.
    assert "Tailwind + Zustand + TypeScript" in result.project_context
    assert any(
        m.sender == AgentRole.MEMORY and "context" in m.summary.lower() for m in result.messages
    )
