"""Tests for the memory subsystem: persistence, scoring, compression, detection."""

import pytest
from memory.context_builder import ContextBuilder
from memory.detection import detect_project
from memory.manager import MemoryManager
from memory.scoring import score_memory
from memory.store import InMemoryStore
from memory.types import MemoryItem, MemoryScope


def mgr() -> MemoryManager:
    return MemoryManager(InMemoryStore())


@pytest.mark.asyncio
async def test_store_and_retrieve_project_memory():
    m = mgr()
    await m.store_memory(MemoryScope.PROJECT, "framework", "FastAPI", project_id="p1")
    await m.store_memory(MemoryScope.PROJECT, "style", "Black", project_id="p1")
    items = await m.retrieve(MemoryScope.PROJECT, project_id="p1", current_project_id="p1")
    assert {i.key for i in items} == {"framework", "style"}


@pytest.mark.asyncio
async def test_memory_is_owner_scoped():
    m = mgr()
    await m.store_memory(MemoryScope.USER, "pm", "pnpm", user_id="u1")
    await m.store_memory(MemoryScope.USER, "pm", "npm", user_id="u2")
    u1 = await m.retrieve(MemoryScope.USER, user_id="u1")
    assert len(u1) == 1 and u1[0].value == "pnpm"


def test_scoring_prefers_recent_important_relevant():
    recent = MemoryItem(
        scope=MemoryScope.PROJECT,
        key="a",
        value="x",
        project_id="p1",
        importance=1.0,
        usage_count=3,
        last_used_tick=100,
    )
    old = MemoryItem(
        scope=MemoryScope.PROJECT,
        key="b",
        value="y",
        project_id="p1",
        importance=1.0,
        usage_count=0,
        last_used_tick=10,
    )
    s_recent = score_memory(recent, now_tick=100, current_project_id="p1")
    s_old = score_memory(old, now_tick=100, current_project_id="p1")
    assert s_recent > s_old


def test_scoring_project_relevance_bonus():
    base = {
        "scope": MemoryScope.PROJECT,
        "key": "a",
        "value": "x",
        "last_used_tick": 100,
    }
    relevant = MemoryItem(project_id="p1", **base)
    other = MemoryItem(project_id="p2", **base)
    assert score_memory(relevant, now_tick=100, current_project_id="p1") > score_memory(
        other, now_tick=100, current_project_id="p1"
    )


@pytest.mark.asyncio
async def test_conversation_compression():
    m = mgr()
    for i in range(25):
        await m.store_memory(MemoryScope.SESSION, f"msg{i}", f"message {i}", session_id="s1")
    summary = await m.compress_session("s1", keep_last=10)
    assert summary is not None and summary.key == "summary"
    remaining = await m.store.query(MemoryScope.SESSION, session_id="s1")
    # 10 kept + 1 summary.
    assert len(remaining) == 11


@pytest.mark.asyncio
async def test_compression_noop_when_short():
    m = mgr()
    for i in range(3):
        await m.store_memory(MemoryScope.SESSION, f"m{i}", "x", session_id="s1")
    assert await m.compress_session("s1", keep_last=10) is None


@pytest.mark.asyncio
async def test_context_builder_assembles_sections():
    m = mgr()
    await m.store_memory(MemoryScope.PROJECT, "stack", "FastAPI + Next.js", project_id="p1")
    await m.store_memory(MemoryScope.USER, "formatter", "Prettier", user_id="u1")
    builder = ContextBuilder(m)
    ctx = await builder.build("add dark mode", project_id="p1", user_id="u1")
    assert "Project notes" in ctx and "FastAPI + Next.js" in ctx
    assert "User preferences" in ctx and "Prettier" in ctx


def test_detect_project_python_and_node(tmp_path):
    (tmp_path / "pyproject.toml").write_text("[project]\ndependencies=['fastapi','sqlalchemy']")
    (tmp_path / "uv.lock").write_text("")
    (tmp_path / "package.json").write_text('{"dependencies":{"next":"15","tailwindcss":"3"}}')
    (tmp_path / "pnpm-lock.yaml").write_text("")
    profile = detect_project(tmp_path)
    assert "python" in profile.languages
    assert "fastapi" in profile.frameworks and "next" in profile.frameworks
    assert "uv" in profile.package_managers and "pnpm" in profile.package_managers
