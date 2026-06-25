"""Tests for the /agents/run endpoint (offline, via EchoProvider)."""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import app


def test_agents_run_endpoint(echo_router):
    """The endpoint runs the full workflow and returns a structured result."""
    with patch("app.agents_runtime.build_router", return_value=echo_router):
        client = TestClient(app)
        resp = client.post("/agents/run", json={"user_request": "Add JWT authentication"})

    assert resp.status_code == 200
    body = resp.json()
    assert body["review_verdict"] == "approved"
    assert body["tasks"] == 6
    assert body["files_changed"] == ["generated/output.txt"]
    assert "generated/output.txt" in body["generated_files"]
    assert body["generated_files"]["generated/output.txt"]
    assert body["final_response"].startswith("Request 'Add JWT authentication'")


@pytest.mark.asyncio
async def test_agents_run_auto_proposes_pr(client, echo_router, monkeypatch):
    """When GitHub owner/repo are set, a completed run persists a pending PR proposal."""
    from github.provider import FakeGitHubProvider

    from app.config import settings

    monkeypatch.setattr(settings, "github_token", "fake-token")
    monkeypatch.setattr(settings, "github_owner", "psr")
    monkeypatch.setattr(settings, "github_repo", "forge")
    monkeypatch.setattr("app.agents_runtime.build_provider", lambda: FakeGitHubProvider())

    with patch("app.agents_runtime.build_router", return_value=echo_router):
        resp = await client.post("/agents/run", json={"user_request": "Add JWT authentication"})

    assert resp.status_code == 200
    body = resp.json()
    assert body.get("pr_approval_id")

    pending = (await client.get("/github/pr/pending")).json()["pending"]
    assert any(p["approval_id"] == body["pr_approval_id"] for p in pending)
