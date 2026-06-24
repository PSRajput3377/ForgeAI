"""Tests for the Failure Knowledge Base (Phase 12.4).

Proves spec §4/§7: errors normalize to a stable signature, fixes are stored and
reused on recurrence, a failed reuse self-corrects, the Reflection agent reuses
a known fix without a model call, and the durable store mirrors the in-memory
one. All offline.
"""

import pytest
import pytest_asyncio
from app.db.base import Base
from app.failure_kb import FailureKB
from core.state import ProjectState
from failures import FailureStore, Outcome, error_signature
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

# --- signature normalization ------------------------------------------------


def test_signature_collides_on_same_root_cause():
    a = error_signature("ModuleNotFoundError: No module named 'jwt'")
    b = error_signature("Traceback ...\nModuleNotFoundError: No module named 'jwt'\n")
    assert a == b == "modulenotfounderror:jwt"


def test_signature_distinguishes_different_modules():
    assert error_signature("No module named 'jwt'") != error_signature("No module named 'redis'")


def test_signature_strips_volatile_detail():
    # Line numbers / addresses don't change the signature for untyped messages.
    s1 = error_signature("connection refused at 0x7ffe line 42")
    s2 = error_signature("connection refused at 0x1234 line 99")
    assert s1 == s2


def test_signature_empty_is_unknown():
    assert error_signature("") == "unknown"
    assert error_signature("   ") == "unknown"


# --- store record / recall --------------------------------------------------


def test_recall_returns_stored_fix():
    store = FailureStore()
    err = "ModuleNotFoundError: No module named 'jwt'"
    store.record(err, fix="pip install pyjwt", outcome=Outcome.RESOLVED)
    hit = store.recall("ModuleNotFoundError: No module named 'jwt'")
    assert hit is not None
    assert hit.fix == "pip install pyjwt"


def test_recall_misses_for_unseen_error():
    assert FailureStore().recall("SomethingError: brand new") is None


def test_recall_prefers_resolved_over_unknown():
    store = FailureStore()
    err = "ImportError: cannot import name 'Foo'"
    store.record(err, fix="guess fix")  # UNKNOWN
    store.record(err, fix="real fix", outcome=Outcome.RESOLVED)
    assert store.recall(err).fix == "real fix"


def test_failed_fix_is_not_recalled():
    store = FailureStore()
    err = "ValueError: bad config"
    store.record(err, fix="bad fix", outcome=Outcome.FAILED)
    assert store.recall(err) is None


def test_recording_same_fix_bumps_hits_and_upgrades_outcome():
    store = FailureStore()
    err = "KeyError: 'token'"
    store.record(err, fix="add token")  # UNKNOWN
    ep = store.record(err, fix="add token", outcome=Outcome.RESOLVED)
    assert ep.hits == 2
    assert ep.outcome is Outcome.RESOLVED


# --- reflection agent reuse -------------------------------------------------


async def test_reflection_reuses_known_fix_without_model(echo_router):
    from agents.reflection import ReflectionAgent

    store = FailureStore()
    # Seed a known-good fix for this signature.
    store.record(
        "ModuleNotFoundError: No module named 'jwt'",
        fix="pip install pyjwt",
        outcome=Outcome.RESOLVED,
    )
    agent = ReflectionAgent(echo_router, failure_store=store)

    state = ProjectState(user_request="add auth", project_id="r1")
    state.execution_logs.append("ModuleNotFoundError: No module named 'jwt'")
    out = await agent.run(state)

    assert "reused known fix" in out.execution_logs[-1]
    assert "pip install pyjwt" in out.review_feedback


async def test_reflection_records_new_failure(echo_router):
    from agents.reflection import ReflectionAgent

    store = FailureStore()
    agent = ReflectionAgent(echo_router, failure_store=store)
    state = ProjectState(user_request="add auth", project_id="r2")
    state.execution_logs.append("RuntimeError: kaboom")
    await agent.run(state)
    # The novel failure is now in the KB.
    assert any(e.signature == "runtimeerror" for e in store.all())


async def test_reflection_without_store_is_unchanged(echo_router):
    from agents.reflection import ReflectionAgent

    agent = ReflectionAgent(echo_router)  # no store
    state = ProjectState(user_request="add auth", project_id="r3")
    state.execution_logs.append("RuntimeError: kaboom")
    out = await agent.run(state)
    assert out.retry_count == 1
    assert out.review_feedback.startswith("reflection-fix:")


# --- durable KB -------------------------------------------------------------


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
async def test_durable_kb_record_and_recall(session):
    kb = FailureKB(session)
    err = "ModuleNotFoundError: No module named 'jwt'"
    await kb.record(err, fix="pip install pyjwt", outcome=Outcome.RESOLVED)
    hit = await kb.recall(err)
    assert hit is not None and hit.fix == "pip install pyjwt"


@pytest.mark.asyncio
async def test_durable_kb_self_corrects(session):
    kb = FailureKB(session)
    err = "ValueError: bad config"
    await kb.record(err, fix="try this", outcome=Outcome.RESOLVED)
    assert (await kb.recall(err)).fix == "try this"
    # The fix later fails → demote it; nothing good left to recall.
    await kb.record(err, fix="try this", outcome=Outcome.FAILED)
    assert await kb.recall(err) is None


@pytest.mark.asyncio
async def test_durable_kb_bumps_hits(session):
    kb = FailureKB(session)
    err = "KeyError: 'token'"
    await kb.record(err, fix="add token")
    ep = await kb.record(err, fix="add token", outcome=Outcome.RESOLVED)
    assert ep.hits == 2 and ep.outcome is Outcome.RESOLVED
