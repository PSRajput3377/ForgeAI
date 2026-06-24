"""GitHub runtime wiring: provider selection + the demo endpoints (offline)."""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from github.provider import FakeGitHubProvider, GitHubProvider
from github.rest_provider import RestGitHubProvider

from app import github_runtime
from app.main import app


def test_rest_provider_conforms_to_interface():
    # RestGitHubProvider must actually implement the ABC (no missing methods).
    assert issubclass(RestGitHubProvider, GitHubProvider)
    provider = RestGitHubProvider(token="x")
    assert isinstance(provider, GitHubProvider)


def test_factory_uses_fake_without_token():
    with patch.object(github_runtime.settings, "github_token", ""):
        assert isinstance(github_runtime.build_provider(), FakeGitHubProvider)
        assert github_runtime.github_configured() is False


def test_factory_uses_rest_with_token():
    with patch.object(github_runtime.settings, "github_token", "ghp_live"):
        provider = github_runtime.build_provider()
        assert isinstance(provider, RestGitHubProvider)
        assert provider.token == "ghp_live"
        assert github_runtime.github_configured() is True


def test_status_endpoint_reports_mode():
    client = TestClient(app)
    with patch.object(github_runtime.settings, "github_token", ""):
        assert client.get("/github/status").json() == {"mode": "fake"}
    with patch.object(github_runtime.settings, "github_token", "ghp_live"):
        assert client.get("/github/status").json() == {"mode": "live"}


def test_repo_endpoint_via_fake(monkeypatch):
    # With no token, the demo endpoints run against the fake provider.
    # Patch where the name is used (app.api.github), not where it's defined.
    fake = FakeGitHubProvider()
    monkeypatch.setattr("app.api.github.build_provider", lambda: fake)
    client = TestClient(app)
    resp = client.get("/github/repo/psr/forge")
    assert resp.status_code == 200
    body = resp.json()
    assert body["owner"] == "psr" and body["name"] == "forge"


@pytest.mark.asyncio
async def test_demo_branches_and_issues_via_fake(monkeypatch):
    fake = FakeGitHubProvider()
    repo = await fake.get_repository("psr", "forge")
    await fake.create_branch(repo, "feature/x", repo.default_branch)
    monkeypatch.setattr("app.api.github.build_provider", lambda: fake)

    client = TestClient(app)
    branches = client.get("/github/repo/psr/forge/branches").json()["branches"]
    names = {b["name"] for b in branches}
    assert "main" in names and "feature/x" in names

    issues = client.get("/github/repo/psr/forge/issues").json()["issues"]
    assert issues == []  # none seeded
