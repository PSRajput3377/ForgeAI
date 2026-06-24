"""Auth + multi-tenancy + RBAC tests against an in-memory SQLite DB.

Overrides the app's DB session dependency with a shared in-memory SQLite engine
so the entire auth/org/workspace flow runs offline (ADR-0018).
"""

import pytest

# The `client` fixture (in-memory SQLite + clean denylist) lives in conftest.py.


async def _register_and_login(client, email="a@a.com", name="A", password="pw12345"):
    await client.post("/auth/register", json={"email": email, "name": name, "password": password})
    resp = await client.post("/auth/login", json={"email": email, "password": password})
    return resp.json()


@pytest.mark.asyncio
async def test_register_login_me(client):
    tokens = await _register_and_login(client)
    assert "access_token" in tokens and "refresh_token" in tokens
    me = await client.get("/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert me.status_code == 200 and me.json()["email"] == "a@a.com"


@pytest.mark.asyncio
async def test_duplicate_email_rejected(client):
    await _register_and_login(client)
    dup = await client.post(
        "/auth/register", json={"email": "a@a.com", "name": "B", "password": "x12345"}
    )
    assert dup.status_code == 409


@pytest.mark.asyncio
async def test_wrong_password_rejected(client):
    await _register_and_login(client)
    resp = await client.post("/auth/login", json={"email": "a@a.com", "password": "wrong"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_protected_route_requires_auth(client):
    resp = await client.get("/auth/me")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_refresh_issues_new_tokens(client):
    tokens = await _register_and_login(client)
    resp = await client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert resp.status_code == 200 and "access_token" in resp.json()


@pytest.mark.asyncio
async def test_logout_revokes_refresh_token(client):
    tokens = await _register_and_login(client)
    await client.post(
        "/auth/logout",
        json={"refresh_token": tokens["refresh_token"]},
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    # The revoked refresh token can no longer mint access tokens.
    resp = await client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert resp.status_code == 401
