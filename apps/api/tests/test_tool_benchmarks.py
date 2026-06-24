"""Lightweight performance benchmarks for common tool operations.

Not micro-benchmarks — these assert that common operations complete well under a
generous budget, catching accidental O(n^2) or blocking regressions. They also
record timing in the result's execution_time via the Tool Manager.
"""

import time

import pytest
from tools import build_default_registry
from tools.base import ToolInput
from tools.manager import ToolManager


@pytest.mark.asyncio
async def test_filesystem_write_read_under_budget(tmp_path):
    mgr = ToolManager(build_default_registry(tmp_path))
    start = time.perf_counter()
    for i in range(100):
        await mgr.run(
            "filesystem",
            ToolInput(action="write", args={"path": f"f{i}.txt", "content": "x" * 100}),
        )
    for i in range(100):
        await mgr.run(
            "filesystem", ToolInput(action="read", args={"path": f"f{i}.txt"})
        )
    elapsed = time.perf_counter() - start
    # 200 confined fs ops should be fast; 5s is a very generous ceiling.
    assert elapsed < 5.0, f"200 fs ops took {elapsed:.2f}s"


@pytest.mark.asyncio
async def test_manager_records_execution_time(tmp_path):
    mgr = ToolManager(build_default_registry(tmp_path))
    res = await mgr.run(
        "filesystem", ToolInput(action="write", args={"path": "a.txt", "content": "x"})
    )
    assert res.success
    assert res.execution_time > 0.0


@pytest.mark.asyncio
async def test_search_scales_to_many_files(tmp_path):
    mgr = ToolManager(build_default_registry(tmp_path))
    for i in range(200):
        await mgr.run(
            "filesystem",
            ToolInput(
                action="write",
                args={"path": f"f{i}.txt", "content": f"line{i}\nneedle{i % 2}"},
            ),
        )
    start = time.perf_counter()
    res = await mgr.run(
        "search", ToolInput(action="search", args={"query": "needle0", "limit": 1000})
    )
    elapsed = time.perf_counter() - start
    assert res.success
    assert elapsed < 5.0, f"search over 200 files took {elapsed:.2f}s"
