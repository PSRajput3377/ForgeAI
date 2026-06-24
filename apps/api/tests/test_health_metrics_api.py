"""API tests for the production health/readiness/metrics endpoints."""

from fastapi.testclient import TestClient

from app.main import app


def test_liveness():
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_readiness_reports_components():
    client = TestClient(app)
    resp = client.get("/health/ready")
    assert resp.status_code == 200
    body = resp.json()
    assert "status" in body and "components" in body
    # No DB is running in the test → database component is down, status degraded/unhealthy.
    assert "database" in body["components"]


def test_prometheus_metrics_endpoint():
    client = TestClient(app)
    resp = client.get("/metrics")
    assert resp.status_code == 200
    assert "text/plain" in resp.headers["content-type"]
