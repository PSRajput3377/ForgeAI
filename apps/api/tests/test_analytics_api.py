"""Tests for the Agent Analytics endpoints (Phase 12.8).

Uses the `client` fixture (in-memory SQLite). Proves the dashboard's data
sources: an agent run persists an evaluation, the overview/prompt-comparison
reflect it, and the benchmark-trend endpoint responds. All offline (the run
goes through the echo router via patched build_router).
"""

from unittest.mock import patch

import pytest


@pytest.mark.asyncio
async def test_overview_empty_before_any_run(client):
    resp = await client.get("/analytics/overview")
    assert resp.status_code == 200
    assert resp.json()["runs"] == 0


@pytest.mark.asyncio
async def test_run_persists_evaluation_and_overview_reflects_it(client, echo_router):
    with patch("app.agents_runtime.build_router", return_value=echo_router):
        run = await client.post("/agents/run", json={"user_request": "Add JWT auth"})
    assert run.status_code == 200

    overview = (await client.get("/analytics/overview")).json()
    assert overview["runs"] == 1
    assert 0.0 <= overview["mean_score"] <= 1.0


@pytest.mark.asyncio
async def test_prompt_comparison_reflects_recorded_versions(client, echo_router):
    with patch("app.agents_runtime.build_router", return_value=echo_router):
        await client.post("/agents/run", json={"user_request": "Add JWT auth"})

    body = (await client.get("/analytics/prompts")).json()
    roles = body["roles"]
    assert "planner" in roles
    assert roles["planner"]["active_version"] == "v1"
    assert "v1" in roles["planner"]["versions"]


@pytest.mark.asyncio
async def test_prompt_comparison_single_role(client, echo_router):
    with patch("app.agents_runtime.build_router", return_value=echo_router):
        await client.post("/agents/run", json={"user_request": "Add JWT auth"})

    body = (await client.get("/analytics/prompts/planner")).json()
    assert body["role"] == "planner"
    assert body["active_version"] == "v1"


@pytest.mark.asyncio
async def test_benchmark_trend_endpoint(client):
    resp = await client.get("/analytics/benchmarks/trend")
    assert resp.status_code == 200
    assert resp.json()["trend"] == []
