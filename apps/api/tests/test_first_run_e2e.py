"""End-to-end first-run path (Phase 13.5) — fresh account to working project.

Proves spec §5 offline: a brand-new user can register, bootstrap a project from
a starter, run the agent team against it, and end with real files on disk — no
config, no models (echo provider), all through the HTTP API.
"""

from pathlib import Path
from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True)
def _tmp_workspaces(tmp_path, monkeypatch):
    monkeypatch.setattr("app.config.settings.workspaces_root", str(tmp_path / "ws"))


async def _auth_token(client, email="new@x.com"):
    await client.post("/auth/register", json={"email": email, "name": "New", "password": "pw12345"})
    resp = await client.post("/auth/login", json={"email": email, "password": "pw12345"})
    return resp.json()["access_token"]


@pytest.mark.asyncio
async def test_fresh_account_to_working_project(client, echo_router):
    """The whole first-minute journey, offline, in one test."""
    # 1. Fresh account.
    token = await _auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    # 2. A workspace (the chooser does this via ensureWorkspace()).
    ws = (await client.post("/orgs", json={"name": "My Workspace"}, headers=headers)).json()[
        "workspace_id"
    ]

    # 3. See the starters the chooser would offer.
    starters = (await client.get("/projects/starters")).json()["starters"]
    assert any(s["id"] == "fastapi-saas" for s in starters)

    # 4. Bootstrap a real project from the FastAPI starter.
    project = (
        await client.post(
            "/projects/bootstrap",
            json={"workspace_id": ws, "name": "My SaaS", "starter": "fastapi-saas"},
            headers=headers,
        )
    ).json()
    assert "app/main.py" in project["scaffolded_files"]
    assert (Path(project["path"]) / "app" / "main.py").is_file()

    # 5. Run the agent team against the project (echo provider — instant).
    with patch("app.agents_runtime.build_router", return_value=echo_router):
        run = await client.post(
            "/agents/run",
            json={"user_request": "Add a /status endpoint", "project_id": project["id"]},
            headers=headers,
        )
    assert run.status_code == 200
    body = run.json()
    assert body["project_id"] == project["id"]
    assert body["review_verdict"]  # the team produced a verdict
    assert body["written_files"]  # and wrote files into the project

    # 6. The result is a real, inspectable project on disk.
    for rel in body["written_files"]:
        assert (Path(project["path"]) / rel).is_file()

    # 7. The run was scored and is visible in analytics (the loop closes).
    overview = (await client.get("/analytics/overview")).json()
    assert overview["runs"] >= 1
