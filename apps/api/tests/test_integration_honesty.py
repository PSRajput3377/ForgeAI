"""Tests for integration honesty (Phase 13.6) — modes are never overstated."""

from app.main import app
from fastapi.testclient import TestClient
from integrations import build_default_hub


def test_default_hub_connectors_are_simulated():
    hub = build_default_hub()
    status = hub.status()
    assert len(status) >= 8  # github, jira, slack, notion, confluence, email, calendar, figma
    # Fakes must report 'simulated' — never claim to be live.
    assert all(c["mode"] == "simulated" for c in status)
    assert all("capabilities" in c for c in status)


def test_connector_default_mode_is_simulated():
    from integrations import FakeSlackConnector

    # The base default is the conservative one, so a connector can't accidentally
    # look live.
    assert FakeSlackConnector().mode == "simulated"


def test_status_endpoint_reports_modes():
    client = TestClient(app)
    body = client.get("/integrations/status").json()
    assert body["github_mode"] in ("fake", "live")
    systems = {c["system"] for c in body["connectors"]}
    assert "jira" in systems and "slack" in systems
    assert all(c["mode"] == "simulated" for c in body["connectors"])
