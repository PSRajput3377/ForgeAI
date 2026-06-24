"""End-to-end tests for the LangGraph multi-agent workflow (offline, EchoProvider).

These prove the whole architecture runs: the Manager intake, every specialist,
the structured message trail, and the reflection retry loop.
"""

import pytest
from agents.workflow import run_workflow
from core.roles import AgentRole
from core.state import ProjectState, ReviewVerdict


@pytest.mark.asyncio
async def test_happy_path_runs_all_agents(echo_router):
    state = await run_workflow(echo_router, "Build JWT Authentication")

    assert isinstance(state, ProjectState)
    assert state.review_verdict == ReviewVerdict.APPROVED
    assert state.test_passed is True
    assert state.tasks, "Planner should have produced tasks"
    assert state.generated_code, "Coder should have generated code"
    assert state.final_response.startswith("Request 'Build JWT Authentication'")

    # Manager delegated to every specialist — verify the audit trail.
    senders = {m.sender for m in state.messages}
    for role in (
        AgentRole.MANAGER,
        AgentRole.PLANNER,
        AgentRole.RESEARCHER,
        AgentRole.MEMORY,
        AgentRole.CODER,
        AgentRole.EXECUTION,
        AgentRole.TESTING,
        AgentRole.REVIEW,
        AgentRole.GIT,
    ):
        assert role in senders, f"{role} never ran"


@pytest.mark.asyncio
async def test_reflection_loop_triggers_on_failure(echo_router):
    """A failing build should drive the reflection→coder retry, then recover."""
    state = ProjectState(user_request="Build a flaky feature")
    state.execution_logs.append("exit 1")  # seed a failure the Testing agent sees

    from agents.workflow import build_workflow

    app = build_workflow(echo_router)
    result = ProjectState.model_validate(await app.ainvoke(state))

    # Reflection ran at least once and the run still terminated.
    assert result.retry_count >= 1
    assert any(m.sender == AgentRole.REFLECTION for m in result.messages)
    assert result.final_response  # Manager always produces a final response


@pytest.mark.asyncio
async def test_manager_never_writes_code(echo_router):
    """Architecture invariant: no file is attributed to the Manager."""
    state = await run_workflow(echo_router, "Add a CRUD API")
    manager_files = [
        f for m in state.messages if m.sender == AgentRole.MANAGER for f in m.files_changed
    ]
    assert manager_files == []
