"""Smoke test for the health endpoint."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_ok():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_root_banner():
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json()["service"] == "forge-api"
