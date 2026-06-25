"""Tests for first-class projects (Phase 13.1): CRUD, workspace dir, isolation.

Uses the `client` fixture (in-memory SQLite). The workspaces root is pointed at
a tmp dir so no real directories are touched. Proves spec §1. All offline.
"""

import os
from pathlib import Path

import pytest


async def _user(client, email):
    await client.post("/auth/register", json={"email": email, "name": email, "password": "pw12345"})
    resp = await client.post("/auth/login", json={"email": email, "password": "pw12345"})
    return resp.json()["access_token"]


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


async def _workspace(client, token):
    body = (await client.post("/orgs", json={"name": "Labs"}, headers=_auth(token))).json()
    return body["workspace_id"]


@pytest.fixture(autouse=True)
def _tmp_workspaces(tmp_path, monkeypatch):
    """Point the workspaces root at a throwaway tmp dir for every test."""
    monkeypatch.setattr("app.config.settings.workspaces_root", str(tmp_path / "ws"))
    return tmp_path


@pytest.mark.asyncio
async def test_create_project_provisions_a_directory(client):
    token = await _user(client, "a@x.com")
    ws = await _workspace(client, token)

    resp = await client.post(
        "/projects", json={"workspace_id": ws, "name": "My API"}, headers=_auth(token)
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "My API"
    assert body["path"]  # a path was assigned
    assert Path(body["path"]).is_dir()  # and the directory exists
    assert body["id"] in body["path"]  # derived from the id (not client-supplied)


@pytest.mark.asyncio
async def test_list_only_shows_own_workspace_projects(client):
    token = await _user(client, "a@x.com")
    ws = await _workspace(client, token)
    await client.post("/projects", json={"workspace_id": ws, "name": "P1"}, headers=_auth(token))
    await client.post("/projects", json={"workspace_id": ws, "name": "P2"}, headers=_auth(token))

    listing = await client.get(f"/projects?workspace_id={ws}", headers=_auth(token))
    names = {p["name"] for p in listing.json()["projects"]}
    assert names == {"P1", "P2"}


@pytest.mark.asyncio
async def test_outsider_cannot_create_or_see_projects(client):
    owner = await _user(client, "owner@x.com")
    outsider = await _user(client, "out@x.com")
    ws = await _workspace(client, owner)

    # Outsider is not a member of the workspace → 403 on create and list.
    create = await client.post(
        "/projects", json={"workspace_id": ws, "name": "X"}, headers=_auth(outsider)
    )
    assert create.status_code == 403
    listing = await client.get(f"/projects?workspace_id={ws}", headers=_auth(outsider))
    assert listing.status_code == 403


@pytest.mark.asyncio
async def test_get_unknown_project_is_404(client):
    token = await _user(client, "a@x.com")
    resp = await client.get("/projects/nonexistent", headers=_auth(token))
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_removes_row_and_directory(client):
    token = await _user(client, "a@x.com")
    ws = await _workspace(client, token)
    created = (
        await client.post(
            "/projects", json={"workspace_id": ws, "name": "Temp"}, headers=_auth(token)
        )
    ).json()
    path = created["path"]
    assert Path(path).is_dir()

    deleted = await client.delete(f"/projects/{created['id']}", headers=_auth(token))
    assert deleted.status_code == 200
    assert not Path(path).exists()  # directory removed
    # Row is gone too.
    assert (await client.get(f"/projects/{created['id']}", headers=_auth(token))).status_code == 404


@pytest.mark.asyncio
async def test_project_path_stays_under_root(client, _tmp_workspaces):
    token = await _user(client, "a@x.com")
    ws = await _workspace(client, token)
    created = (
        await client.post(
            "/projects", json={"workspace_id": ws, "name": "Confined"}, headers=_auth(token)
        )
    ).json()
    root = (_tmp_workspaces / "ws").resolve()
    assert os.path.commonpath([root, Path(created["path"]).resolve()]) == str(root)
