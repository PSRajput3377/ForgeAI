"""Tests for dynamic agent selection (Phase 12.7).

Proves spec §7: a deterministic rule-based classifier behind a strategy
interface, every selection recorded with its rationale, off by default. Offline.
"""

from agents.workflow import run_workflow
from core.state import ProjectState
from selection import RuleBasedSelector, Selection, SelectionStrategy, TaskType


def _select(request: str) -> Selection:
    return RuleBasedSelector().select(ProjectState(user_request=request))


# --- rule-based classification ----------------------------------------------


def test_classifies_backend():
    sel = _select("Add JWT authentication to the API")
    assert sel.task_type is TaskType.BACKEND
    assert "backend" in sel.rationale


def test_classifies_frontend():
    sel = _select("Add a dark mode toggle to the settings page UI")
    assert sel.task_type is TaskType.FRONTEND


def test_classifies_database():
    sel = _select("Write a migration to add an index on the users table")
    assert sel.task_type is TaskType.DATABASE


def test_defaults_to_general_without_signal():
    sel = _select("Make the thing nicer please")
    assert sel.task_type is TaskType.GENERAL
    assert "No strong task-type signal" in sel.rationale


def test_rationale_names_matched_signals():
    sel = _select("Create a REST endpoint and a route")
    assert "endpoint" in sel.rationale and "route" in sel.rationale


def test_selection_is_deterministic():
    a = _select("Add an API endpoint with auth")
    b = _select("Add an API endpoint with auth")
    assert a == b


def test_strategy_is_swappable_via_interface():
    class AlwaysFrontend(SelectionStrategy):
        name = "always-frontend"

        def select(self, state):
            return Selection(task_type=TaskType.FRONTEND, rationale="stub")

    assert isinstance(AlwaysFrontend(), SelectionStrategy)
    assert AlwaysFrontend().select(ProjectState(user_request="x")).task_type is TaskType.FRONTEND


# --- workflow wiring --------------------------------------------------------


async def test_workflow_records_task_type(echo_router):
    final = await run_workflow(
        echo_router,
        "Add JWT authentication",
        project_id="sel-1",
        selection_strategy=RuleBasedSelector(),
    )
    assert final.task_type == "backend"
    assert final.selection_rationale
    # The intake message reflects the classification.
    intake_msg = next(m for m in final.messages if m.task_id == "intake")
    assert "type=backend" in intake_msg.summary


async def test_workflow_without_strategy_leaves_type_none(echo_router):
    final = await run_workflow(echo_router, "Add JWT authentication", project_id="sel-2")
    assert final.task_type is None
    assert final.selection_rationale == ""
