"""The ExecutionAgent drives a real ExecutionEngine inside the workflow (offline)."""

import pytest
from agents.workflow import build_workflow
from core.roles import AgentRole
from core.state import ProjectState
from execution.engine import ExecutionEngine
from execution.profiles import ExecutionProfile
from execution.sandbox import FakeSandbox


@pytest.mark.asyncio
async def test_execution_agent_runs_engine_and_sets_test_passed(echo_router):
    def engine_factory(state):
        sb = FakeSandbox()  # all commands succeed
        profile = ExecutionProfile(framework="python", test="pytest -q")
        return ExecutionEngine(sb, profile)

    app = build_workflow(echo_router, engine_factory=engine_factory)
    state = ProjectState(user_request="Add JWT auth", project_id="p1")
    result = ProjectState.model_validate(await app.ainvoke(state))

    assert result.test_passed is True
    exec_msgs = [m for m in result.messages if m.sender == AgentRole.EXECUTION]
    assert exec_msgs and "step" in exec_msgs[0].summary.lower()
    # Real command logs were captured (not the simulation line).
    assert any("pytest" in log for log in result.execution_logs)
