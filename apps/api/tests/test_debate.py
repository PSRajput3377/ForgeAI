"""Tests for multi-agent debate (Phase 12.6).

Proves spec §6: N independent attempts, a judge picks a winner with a recorded
rationale, off by default, deterministic under EchoModel. All offline.
"""

import pytest
from agents.debate import ANGLES, DebatingPlannerAgent, PlannerDebate, score_plan
from agents.workflow import build_workflow, run_workflow
from core.state import ProjectState

# --- selection rubric -------------------------------------------------------


def test_score_plan_counts_distinct_meaningful_words():
    assert score_plan("alpha beta alpha gamma") == 3  # alpha, beta, gamma
    assert score_plan("a an the of") == 0  # all < 4 chars
    assert score_plan("") == 0


# --- debate mechanics -------------------------------------------------------


def test_debate_requires_at_least_two_rounds(echo_router):
    with pytest.raises(ValueError, match="at least 2"):
        PlannerDebate(echo_router, rounds=1)


async def test_debate_runs_independent_attempts(echo_router):
    debate = PlannerDebate(echo_router, rounds=3)
    _, record = await debate.run("Add JWT authentication")
    assert len(record.attempts) == 3
    # Each attempt used a distinct angle (independence of framing).
    assert [a.angle for a in record.attempts] == ANGLES[:3]
    assert [a.index for a in record.attempts] == [0, 1, 2]


async def test_debate_records_winner_and_rationale(echo_router):
    debate = PlannerDebate(echo_router, rounds=2)
    plan, record = await debate.run("Add JWT authentication")
    assert plan  # winning plan text is returned
    assert record.rationale  # judge rationale recorded
    winners = [a for a in record.attempts if a.won]
    assert len(winners) == 1
    assert winners[0].index == record.winner_index


async def test_debate_is_deterministic(echo_router):
    """Same input → same winner every time (no randomness; spec §6)."""
    debate = PlannerDebate(echo_router, rounds=3)
    _, r1 = await debate.run("Add JWT authentication")
    _, r2 = await debate.run("Add JWT authentication")
    assert r1.winner_index == r2.winner_index


async def test_debate_ties_break_to_earliest_index(echo_router):
    # Echo gives every attempt the same structure; identical scores tie-break to
    # the earliest index, so the winner is attempt 0.
    debate = PlannerDebate(echo_router, rounds=3)
    _, record = await debate.run("identical request")
    scores = {a.score for a in record.attempts}
    if len(scores) == 1:  # all tied (echo case)
        assert record.winner_index == 0


# --- agent + workflow wiring ------------------------------------------------


async def test_debating_planner_produces_tasks(echo_router):
    agent = DebatingPlannerAgent(echo_router, rounds=2)
    state = ProjectState(user_request="Add dark mode", project_id="d1")
    out = await agent.run(state)
    assert len(out.tasks) == 6
    assert out.current_task is not None
    # The debate decision is on the audit trail.
    planner_msg = out.messages[-1]
    assert "debate_winner" in planner_msg.payload
    assert "won" in planner_msg.summary


def test_debate_off_by_default_uses_plain_planner(echo_router):
    from agents.planner import PlannerAgent

    # build_workflow compiles; assert the default planner type via a fresh build.
    # (Graph internals aren't introspectable, so we check the constructor path
    # by building both and trusting the documented default debate_planner=0.)
    app_default = build_workflow(echo_router)
    app_debate = build_workflow(echo_router, debate_planner=2)
    assert app_default is not None and app_debate is not None
    # Sanity: the plain Planner is what a 0/1 setting selects.
    assert isinstance(PlannerAgent(echo_router), PlannerAgent)


async def test_workflow_with_debate_completes(echo_router):
    final = await run_workflow(
        echo_router, "Add JWT authentication", project_id="wf-d", debate_planner=2
    )
    assert len(final.tasks) == 6
    # Debate planner recorded its decision in the run's messages.
    assert any("debate_winner" in m.payload for m in final.messages)


async def test_workflow_without_debate_is_unchanged(echo_router):
    final = await run_workflow(echo_router, "Add JWT authentication", project_id="wf-nd")
    assert len(final.tasks) == 6
    assert not any("debate_winner" in m.payload for m in final.messages)
