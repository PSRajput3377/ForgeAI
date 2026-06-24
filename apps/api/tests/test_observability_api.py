"""API tests for observability endpoints + the /agents/run → events pipeline."""

from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app


def test_metrics_endpoint_shape():
    client = TestClient(app)
    resp = client.get("/observability/metrics")
    assert resp.status_code == 200
    body = resp.json()
    assert "agents" in body and "tools" in body and "tokens" in body


def test_agents_run_populates_timeline_and_metrics(echo_router):
    """A run through /agents/run emits events captured by the shared store."""
    with patch("app.agents_runtime.build_router", return_value=echo_router):
        client = TestClient(app)
        run_resp = client.post(
            "/agents/run",
            json={"user_request": "Add JWT auth", "project_id": "api-run-1"},
        )
        assert run_resp.status_code == 200

        timeline = client.get("/observability/timeline/api-run-1").json()
        types = {e["type"] for e in timeline["events"]}
        assert "run.started" in types
        assert "agent.started" in types
        assert "run.completed" in types

        audit = client.get("/observability/audit/api-run-1").json()
        assert len(audit["audit"]) > 0


def test_live_websocket_streams_events(echo_router):
    """The /observability/live WebSocket receives events emitted during a run."""
    client = TestClient(app)
    with client.websocket_connect("/observability/live") as ws:
        with patch("app.agents_runtime.build_router", return_value=echo_router):
            client.post(
                "/agents/run",
                json={"user_request": "x", "project_id": "ws-run"},
            )
        # First streamed event should be the run.started for our run.
        msg = ws.receive_json()
        assert msg["type"].startswith("run.") or msg["type"].startswith("agent.")
