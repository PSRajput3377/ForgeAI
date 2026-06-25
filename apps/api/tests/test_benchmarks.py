"""Tests for the Benchmark Suite + harness (Phase 12.5).

Proves spec §5: a versioned suite with expected outcomes, a harness that runs
scenarios through the real workflow (echo provider here) and emits per-scenario
+ aggregate metrics, and durable per-version storage for comparison. All offline.
"""

import pytest
import pytest_asyncio
from benchmarks import SUITE, SUITE_VERSION, Scenario, run_benchmarks
from benchmarks.suite import Category
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.benchmark_store import BenchmarkStore
from app.db.base import Base

# --- suite integrity --------------------------------------------------------


def test_suite_is_versioned_and_nonempty():
    assert SUITE_VERSION
    assert len(SUITE) >= 5


def test_suite_ids_are_unique():
    ids = [s.id for s in SUITE]
    assert len(ids) == len(set(ids))


def test_suite_covers_every_category():
    covered = {s.category for s in SUITE}
    assert covered == set(Category)


# --- harness (echo, deterministic) ------------------------------------------


@pytest.mark.asyncio
async def test_harness_runs_full_suite(echo_router):
    report = await run_benchmarks(echo_router, forge_version="test-1")
    assert report.forge_version == "test-1"
    assert report.suite_version == SUITE_VERSION
    assert len(report.results) == len(SUITE)
    # Echo path: tests pass → review approves → every scenario meets expectations.
    assert report.pass_rate == 1.0
    assert report.stats.runs == len(SUITE)


@pytest.mark.asyncio
async def test_harness_scores_each_scenario(echo_router):
    report = await run_benchmarks(echo_router, forge_version="test-1")
    for result in report.results:
        assert 0.0 <= result.evaluation.score <= 1.0
        assert result.evaluation.run_id == result.scenario_id


@pytest.mark.asyncio
async def test_harness_flags_unmet_expectation(echo_router):
    # A scenario that expects failure won't be met on the (successful) echo path.
    impossible = Scenario(
        id="expect-fail",
        name="expects failure",
        category=Category.FIX_BUG,
        request="this will actually succeed under echo",
        expect_success=False,
    )
    report = await run_benchmarks(echo_router, forge_version="t", scenarios=[impossible])
    assert report.results[0].met_expectations is False
    assert report.pass_rate == 0.0


# --- durable storage --------------------------------------------------------


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
async def test_store_saves_and_reads_latest(session, echo_router):
    store = BenchmarkStore(session)
    report = await run_benchmarks(echo_router, forge_version="v-abc")
    await store.save(report)
    latest = await store.latest("v-abc")
    assert latest is not None
    assert latest.pass_rate == report.pass_rate
    assert len(latest.results) == len(SUITE)


@pytest.mark.asyncio
async def test_store_latest_missing_is_none(session):
    assert await BenchmarkStore(session).latest("never-run") is None


@pytest.mark.asyncio
async def test_store_trend_is_chronological(session, echo_router):
    store = BenchmarkStore(session)
    for version in ("v1", "v2", "v3"):
        await store.save(await run_benchmarks(echo_router, forge_version=version))
    trend = await store.trend()
    assert [v for v, _ in trend] == ["v1", "v2", "v3"]
