"""Tests for the /agents/run endpoint (offline, via EchoProvider)."""

from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app


def test_agents_run_endpoint(echo_router):
    """The endpoint runs the full workflow and returns a structured result."""
    with patch("app.agents_runtime.build_router", return_value=echo_router):
        client = TestClient(app)
        resp = client.post(
            "/agents/run", json={"user_request": "Add JWT authentication"}
        )

    assert resp.status_code == 200
    body = resp.json()
    assert body["review_verdict"] == "approved"
    assert body["tasks"] == 6
    assert body["files_changed"] == ["generated/output.txt"]
    assert body["final_response"].startswith("Request 'Add JWT authentication'")
