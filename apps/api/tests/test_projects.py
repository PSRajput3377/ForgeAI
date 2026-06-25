"""Tests for first-class projects (Phase 13.1): CRUD, workspace dir, isolation.

Uses the `client` fixture (in-memory SQLite). The workspaces root is pointed at
a tmp dir so no real directories are touched. Proves spec §1. All offline.
"""

import os
from pathlib import Path
from unittest.mock import patch

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


# --- 13.2: /agents/run binds to a real project ------------------------------


@pytest.mark.asyncio
async def test_run_writes_files_into_project_dir(client, echo_router):
    token = await _user(client, "a@x.com")
    ws = await _workspace(client, token)
    created = (
        await client.post(
            "/projects", json={"workspace_id": ws, "name": "Bound"}, headers=_auth(token)
        )
    ).json()

    with patch("app.agents_runtime.build_router", return_value=echo_router):
        resp = await client.post(
            "/agents/run",
            json={"user_request": "Add a health endpoint", "project_id": created["id"]},
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["project_id"] == created["id"]
    assert body["written_files"]  # files were written
    # The generated files now physically exist under the project's dir.
    for rel in body["written_files"]:
        assert (Path(created["path"]) / rel).is_file()


@pytest.mark.asyncio
async def test_run_with_unknown_project_is_404(client, echo_router):
    with patch("app.agents_runtime.build_router", return_value=echo_router):
        resp = await client.post(
            "/agents/run",
            json={"user_request": "do something", "project_id": "ghost"},
        )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_run_without_project_still_works(client, echo_router):
    # Backward compatible: no project_id → runs, writes nothing to a project dir.
    with patch("app.agents_runtime.build_router", return_value=echo_router):
        resp = await client.post("/agents/run", json={"user_request": "just run"})
    assert resp.status_code == 200
    assert resp.json()["written_files"] == []


# --- 13.3: project bootstrap from starters ----------------------------------


@pytest.mark.asyncio
async def test_list_starters(client):
    token = await _user(client, "a@x.com")
    resp = await client.get("/projects/starters", headers=_auth(token))
    assert resp.status_code == 200
    ids = {s["id"] for s in resp.json()["starters"]}
    assert {"empty", "fastapi-saas"} <= ids


@pytest.mark.asyncio
async def test_bootstrap_scaffolds_fastapi_starter(client):
    token = await _user(client, "a@x.com")
    ws = await _workspace(client, token)
    resp = await client.post(
        "/projects/bootstrap",
        json={"workspace_id": ws, "name": "SaaS", "starter": "fastapi-saas"},
        headers=_auth(token),
    )
    assert resp.status_code == 201
    body = resp.json()
    assert "app/main.py" in body["scaffolded_files"]
    assert "Dockerfile" in body["scaffolded_files"]
    # The files physically exist under the project dir.
    root = Path(body["path"])
    assert (root / "app" / "main.py").is_file()
    assert (root / "tests" / "test_app.py").is_file()
    assert "JWT" in (root / "README.md").read_text()


@pytest.mark.asyncio
async def test_bootstrap_empty_starter(client):
    token = await _user(client, "a@x.com")
    ws = await _workspace(client, token)
    resp = await client.post(
        "/projects/bootstrap",
        json={"workspace_id": ws, "name": "Blank", "starter": "empty"},
        headers=_auth(token),
    )
    assert resp.status_code == 201
    assert resp.json()["scaffolded_files"] == ["README.md"]


@pytest.mark.asyncio
async def test_bootstrap_unknown_starter_is_400_and_rolls_back(client):
    token = await _user(client, "a@x.com")
    ws = await _workspace(client, token)
    resp = await client.post(
        "/projects/bootstrap",
        json={"workspace_id": ws, "name": "Nope", "starter": "does-not-exist"},
        headers=_auth(token),
    )
    assert resp.status_code == 400
    # The rolled-back project is not listed.
    listing = await client.get(f"/projects?workspace_id={ws}", headers=_auth(token))
    assert listing.json()["projects"] == []


@pytest.mark.asyncio
async def test_scaffold_refuses_non_empty_project(tmp_path):
    """Bootstrapping into a project that already has files is refused (no overwrite)."""
    from app.db.base import Base
    from app.db.models import Organization, User, Workspace
    from app.projects import ProjectService
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    engine = create_async_engine("sqlite+aiosqlite://", future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with async_sessionmaker(engine, expire_on_commit=False)() as session:
        user = User(email="s@x.com", name="s", password_hash="x")
        session.add(user)
        await session.flush()
        org = Organization(name="O", slug="o", owner_id=user.id)
        session.add(org)
        await session.flush()
        ws = Workspace(organization_id=org.id, name="W")
        session.add(ws)
        await session.flush()

        svc = ProjectService(session, workspaces_root=str(tmp_path / "ws"))
        project = await svc.create(workspace_id=ws.id, name="Used")
        (Path(project.path) / "existing.txt").write_text("keep me")

        with pytest.raises(ValueError, match="not empty"):
            svc.scaffold(project, "empty")
    await engine.dispose()
