"""Tests for the evaluation substrate (Phase 12.1): rubric, engine, store.

All deterministic and offline — no models or services. Proves the foundation
spec §1/§2 acceptance: a run yields a versioned, rubric-scored record, and
per-agent/comparison reads are derivable from the records.
"""

from core.messages import TaskSpec
from core.state import ProjectState, ReviewVerdict
from evaluation import (
    ACTIVE_RUBRIC,
    Evaluation,
    EvaluationEngine,
    EvaluationStore,
    extract_review_score,
    score_v1,
)
from pytest import approx


def _approved_state(**kwargs) -> ProjectState:
    state = ProjectState(user_request="Add JWT authentication", project_id="run-1", **kwargs)
    state.review_verdict = ReviewVerdict.APPROVED
    state.test_passed = True
    state.review_feedback = "APPROVED. review_score: 9"
    state.current_task = TaskSpec(task_id="t1", title="add auth")
    return state


# --- rubric -----------------------------------------------------------------


def test_score_v1_perfect_run():
    # success + 10/10 review + 0 retries == full marks.
    assert score_v1(success=True, review_score=10, retries=0) == 1.0


def test_score_v1_failure_floor():
    # No success, no review, retries exhausted == 0.
    assert score_v1(success=False, review_score=None, retries=2, max_retries=2) == 0.0


def test_score_v1_retry_penalty_is_linear():
    full = score_v1(success=True, review_score=10, retries=0)
    one = score_v1(success=True, review_score=10, retries=1, max_retries=2)
    two = score_v1(success=True, review_score=10, retries=2, max_retries=2)
    # Retry weight (0.1) decays linearly: 0 → +0.1, 1 → +0.05, 2 → +0.0.
    assert full - one == approx(0.05)
    assert one - two == approx(0.05)


def test_score_v1_unreviewed_earns_no_review_credit():
    assert score_v1(success=True, review_score=None, retries=0) == 0.7  # 0.6 + 0 + 0.1


# --- review-score extraction ------------------------------------------------


def test_extract_review_score_variants():
    assert extract_review_score("review_score: 9") == 9
    assert extract_review_score("Overall score 8/10") == 8
    assert extract_review_score("no number here") is None
    assert extract_review_score("") is None


def test_extract_review_score_rejects_out_of_range():
    # A two-digit match above 10 is not a valid 0-10 score.
    assert extract_review_score("score 42") is None


# --- engine -----------------------------------------------------------------


def test_engine_evaluates_approved_run():
    engine = EvaluationEngine()
    ev = engine.evaluate(_approved_state(), execution_time_s=42.0, tokens=5120)
    assert ev.run_id == "run-1"
    assert ev.success is True
    assert ev.review_score == 9
    assert ev.tests_passed is True
    assert ev.execution_time_s == 42.0
    assert ev.tokens == 5120
    assert ev.rubric_version == ACTIVE_RUBRIC
    assert 0.0 < ev.score <= 1.0


def test_engine_marks_non_approved_run_as_failure():
    state = _approved_state()
    state.review_verdict = ReviewVerdict.CHANGES_REQUESTED
    ev = EvaluationEngine().evaluate(state)
    assert ev.success is False


def test_engine_records_provenance():
    ev = EvaluationEngine().evaluate(
        _approved_state(),
        prompt_versions={"planner": "v3"},
        model_routing={"coder": "deepseek-coder"},
    )
    assert ev.prompt_versions["planner"] == "v3"
    assert ev.model_routing["coder"] == "deepseek-coder"
    assert ev.pr_accepted is None  # backfilled later (spec §10)


# --- store ------------------------------------------------------------------


def test_store_aggregates_are_derived():
    store = EvaluationStore()
    engine = EvaluationEngine()
    store.add(engine.evaluate(_approved_state()))
    failed = _approved_state()
    failed.review_verdict = ReviewVerdict.CHANGES_REQUESTED
    failed.project_id = "run-2"
    store.add(engine.evaluate(failed))

    assert len(store.all()) == 2
    assert store.success_rate() == 0.5
    assert store.for_run("run-1").success is True
    assert store.for_run("missing") is None
    assert 0.0 < store.mean_score() < 1.0


def test_store_slices_by_prompt_version():
    store = EvaluationStore()
    engine = EvaluationEngine()
    store.add(engine.evaluate(_approved_state(), prompt_versions={"planner": "v1"}))
    s2 = _approved_state()
    s2.project_id = "run-2"
    store.add(engine.evaluate(s2, prompt_versions={"planner": "v2"}))

    assert len(store.by_prompt_version("planner", "v1")) == 1
    assert len(store.by_prompt_version("planner", "v2")) == 1
    assert store.by_prompt_version("planner", "v9") == []


def test_empty_store_is_safe():
    store = EvaluationStore()
    assert store.mean_score() == 0.0
    assert store.success_rate() == 0.0
    assert store.all() == []


def test_evaluation_is_serializable():
    ev = EvaluationEngine().evaluate(_approved_state())
    assert Evaluation.model_validate(ev.model_dump()) == ev


# --- workflow wiring --------------------------------------------------------


async def test_run_workflow_records_an_evaluation(echo_router):
    """Every run produces a record when a store is passed (spec §1 acceptance)."""
    from agents.workflow import run_workflow

    store = EvaluationStore()
    await run_workflow(
        echo_router,
        "Add a health endpoint",
        project_id="run-wf",
        evaluation_store=store,
    )
    assert len(store.all()) == 1
    ev = store.for_run("run-wf")
    assert ev is not None
    assert ev.task == "Add a health endpoint"
    assert ev.rubric_version == ACTIVE_RUBRIC
    assert ev.execution_time_s >= 0.0


async def test_run_workflow_without_store_is_unchanged(echo_router):
    """No store → no evaluation side effects (default offline path)."""
    from agents.workflow import run_workflow

    final = await run_workflow(echo_router, "Add a health endpoint", project_id="run-x")
    assert final.user_request == "Add a health endpoint"
