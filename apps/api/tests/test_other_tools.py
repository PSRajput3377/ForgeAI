"""Unit tests for Search, Project, and Memory tools."""

import json

import pytest
from tools.base import ToolErrorCode, ToolInput
from tools.memory import MemoryTool
from tools.project import ProjectTool
from tools.search import SearchTool


@pytest.mark.asyncio
async def test_search_finds_lines(tmp_path):
    (tmp_path / "a.py").write_text("def foo():\n    return 42\n")
    tool = SearchTool(tmp_path)
    res = await tool.execute(ToolInput(action="search", args={"query": "return"}))
    assert res.success
    assert res.metadata["matches"][0]["file"] == "a.py"
    assert res.metadata["matches"][0]["line"] == 2


@pytest.mark.asyncio
async def test_project_detects_python_and_node(tmp_path):
    (tmp_path / "pyproject.toml").write_text("[project]\ndependencies=['fastapi']\n")
    (tmp_path / "package.json").write_text(json.dumps({"dependencies": {"next": "15"}}))
    tool = ProjectTool(tmp_path)
    res = await tool.execute(ToolInput(action="analyze", args={}))
    assert res.success
    assert set(res.metadata["languages"]) == {"python", "node"}
    assert "fastapi" in res.metadata["frameworks"]
    assert "next" in res.metadata["frameworks"]


@pytest.mark.asyncio
async def test_memory_store_retrieve_search_delete():
    mem = MemoryTool()
    await mem.execute(
        ToolInput(
            action="store",
            args={"type": "decisions", "key": "db", "value": "use postgres"},
        )
    )
    got = await mem.execute(ToolInput(action="retrieve", args={"type": "decisions", "key": "db"}))
    assert got.output == "use postgres"

    found = await mem.execute(ToolInput(action="search", args={"query": "postgres"}))
    assert found.metadata["matches"][0]["key"] == "db"

    await mem.execute(ToolInput(action="delete", args={"type": "decisions", "key": "db"}))
    missing = await mem.execute(
        ToolInput(action="retrieve", args={"type": "decisions", "key": "db"})
    )
    assert not missing.success
    assert missing.error.code == ToolErrorCode.NOT_FOUND
