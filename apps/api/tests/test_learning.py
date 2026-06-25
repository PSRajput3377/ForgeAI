"""Tests for the learning-loop scaffolds (Phase 12.9).

Proves spec §8/§10: A/B promotion, workflow optimization, and PR-outcome
learning exist as interfaces with safe defaults + approval gates, and none
auto-acts on thin data. All offline.
"""

import pytest
import pytest_asyncio
from evaluation import Evaluation
from evaluation.stats import Stats
from learning import (
    PROutcome,
    evaluate_promotion,
    outcome_to_signal,
    record_pr_outcome,
    suggest_skips,
)
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db.base import Base
from app.performance import PerformanceStore


def _stats(runs, mean_score, success_rate=1.0) -> Stats:
    return Stats(runs=runs, mean_score=mean_score, success_rate=success_rate)


def _eval(run_id, success=True) -> Evaluation:
    return Evaluation(run_id=run_id, task="t", success=success, score=0.8, rubric_version="v1")


# --- A/B promotion gate -----------------------------------------------------


def test_promotion_recommended_when_challenger_clearly_better():
    rec = evaluate_promotion(
        "planner",
        "v1",
        {"v1": _stats(50, 0.70), "v2": _stats(50, 0.80)},
    )
    assert rec.should_promote is True
    assert rec.candidate_version == "v2"
    assert rec.requires_approval is True  # never automatic


def test_promotion_blocked_on_thin_data():
    rec = evaluate_promotion("planner", "v1", {"v1": _stats(5, 0.7), "v2": _stats(5, 0.9)})
    assert rec.should_promote is False
    assert "runs" in rec.reason


def test_promotion_blocked_when_margin_too_small():
    rec = evaluate_promotion(
        "planner",
        "v1",
        {"v1": _stats(50, 0.80), "v2": _stats(50, 0.82)},  # +0.02 < 0.05
    )
    assert rec.should_promote is False
    assert rec.candidate_version == "v2"


def test_promotion_no_active_version():
    rec = evaluate_promotion("planner", None, {})
    assert rec.should_promote is False


def test_promotion_always_requires_approval_flag():
    rec = evaluate_promotion("planner", "v1", {"v1": _stats(50, 0.7), "v2": _stats(50, 0.9)})
    assert rec.requires_approval is True


# --- workflow optimization (advisory) ---------------------------------------


def test_skip_suggestion_fires_on_strong_uniform_success():
    evals = [_eval(f"r{i}", success=True) for i in range(40)]
    suggestions = suggest_skips("backend", evals, ["research"])
    assert len(suggestions) == 1
    assert suggestions[0].node == "research"
    assert suggestions[0].requires_approval is True


def test_skip_suggestion_silent_on_thin_data():
    evals = [_eval(f"r{i}") for i in range(5)]
    assert suggest_skips("backend", evals, ["research"]) == []


def test_skip_suggestion_silent_when_success_imperfect():
    evals = [_eval(f"r{i}", success=(i % 2 == 0)) for i in range(40)]  # 50%
    assert suggest_skips("backend", evals, ["research"]) == []


# --- PR-outcome signal ------------------------------------------------------


def test_outcome_maps_to_signal():
    assert outcome_to_signal(PROutcome.MERGED) is True
    assert outcome_to_signal(PROutcome.CLOSED) is False


@pytest_asyncio.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite://", future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as s:
        yield s
    await engine.dispose()


@pytest.mark.asyncio
async def test_record_pr_outcome_backfills_store(session):
    store = PerformanceStore(session)
    await store.add(_eval("run-pr"))
    assert (await store.for_run("run-pr")).pr_accepted is None

    updated = await record_pr_outcome(store, "run-pr", PROutcome.MERGED)
    assert updated is True
    assert (await store.for_run("run-pr")).pr_accepted is True


@pytest.mark.asyncio
async def test_record_pr_outcome_rejected(session):
    store = PerformanceStore(session)
    await store.add(_eval("run-pr2"))
    await record_pr_outcome(store, "run-pr2", PROutcome.CLOSED)
    assert (await store.for_run("run-pr2")).pr_accepted is False
