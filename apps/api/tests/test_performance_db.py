"""Tests for the Performance Database (Phase 12.2).

Two layers, both offline:
  - pure ``evaluation.stats`` aggregation (no DB)
  - the PostgreSQL-backed ``PerformanceStore`` on in-memory SQLite (ADR-0018)

Proves spec §2: stats are derived from records (identical to the in-memory
store), and the durable store answers the same comparison queries.
"""

import pytest
import pytest_asyncio
from evaluation import Evaluation, EvaluationStore, aggregate, by_prompt_version
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db.base import Base
from app.performance import PerformanceStore


def _eval(run_id, *, success=True, score=0.9, retries=0, planner="v1", pr=None) -> Evaluation:
    return Evaluation(
        run_id=run_id,
        task="Add JWT auth",
        success=success,
        retries=retries,
        execution_time_s=10.0,
        score=score,
        rubric_version="v1",
        prompt_versions={"planner": planner},
        pr_accepted=pr,
    )


# --- pure aggregation -------------------------------------------------------


def test_aggregate_empty_is_zeros():
    s = aggregate([])
    assert s.runs == 0 and s.success_rate == 0.0 and s.accepted_pr_rate is None


def test_aggregate_basic_rollup():
    s = aggregate([_eval("a", success=True, score=1.0), _eval("b", success=False, score=0.0)])
    assert s.runs == 2
    assert s.success_rate == 0.5
    assert s.mean_score == 0.5


def test_accepted_pr_rate_ignores_undecided():
    evals = [_eval("a", pr=True), _eval("b", pr=False), _eval("c", pr=None)]
    s = aggregate(evals)
    # Only the two decided runs count: 1 of 2 accepted.
    assert s.accepted_pr_rate == 0.5


def test_by_prompt_version_groups_and_skips_unlabeled():
    evals = [
        _eval("a", planner="v1", success=True),
        _eval("b", planner="v2", success=False),
        Evaluation(run_id="c", task="t", success=True, score=1.0, rubric_version="v1"),
    ]
    groups = by_prompt_version(evals, "planner")
    assert set(groups) == {"v1", "v2"}
    assert groups["v1"].success_rate == 1.0
    assert groups["v2"].success_rate == 0.0


def test_in_memory_store_uses_same_aggregation():
    mem = EvaluationStore()
    for e in [_eval("a", success=True), _eval("b", success=False)]:
        mem.add(e)
    assert mem.stats() == aggregate(mem.all())


# --- durable store ----------------------------------------------------------


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
async def test_store_roundtrips_a_record(session):
    store = PerformanceStore(session)
    await store.add(_eval("run-1", score=0.86))
    got = await store.for_run("run-1")
    assert got is not None
    assert got.run_id == "run-1"
    assert got.score == 0.86
    assert got.prompt_versions == {"planner": "v1"}


@pytest.mark.asyncio
async def test_store_for_run_missing_is_none(session):
    store = PerformanceStore(session)
    assert await store.for_run("nope") is None


@pytest.mark.asyncio
async def test_store_derives_same_stats_as_in_memory(session):
    rows = [_eval("a", success=True, score=1.0), _eval("b", success=False, score=0.0)]
    store = PerformanceStore(session)
    mem = EvaluationStore()
    for e in rows:
        await store.add(e)
        mem.add(e)
    assert await store.stats() == mem.stats()


@pytest.mark.asyncio
async def test_store_prompt_version_stats(session):
    store = PerformanceStore(session)
    await store.add(_eval("a", planner="v3", success=True))
    await store.add(_eval("b", planner="v4", success=True))
    groups = await store.prompt_version_stats("planner")
    assert set(groups) == {"v3", "v4"}


@pytest.mark.asyncio
async def test_store_backfills_pr_outcome(session):
    store = PerformanceStore(session)
    await store.add(_eval("run-9", pr=None))
    assert (await store.for_run("run-9")).pr_accepted is None
    updated = await store.set_pr_accepted("run-9", True)
    assert updated is True
    assert (await store.for_run("run-9")).pr_accepted is True
    # Unknown run → no update.
    assert await store.set_pr_accepted("ghost", True) is False
