"""Organizations, workspaces, invitations, RBAC, and workspace isolation."""

import pytest

# The `client` fixture (in-memory SQLite + clean denylist) lives in conftest.py.


async def _user(client, email):
    await client.post("/auth/register", json={"email": email, "name": email, "password": "pw12345"})
    resp = await client.post("/auth/login", json={"email": email, "password": "pw12345"})
    return resp.json()["access_token"]


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_create_org_makes_owner(client):
    token = await _user(client, "owner@x.com")
    resp = await client.post("/orgs", json={"name": "ForgeAI Labs"}, headers=_auth(token))
    assert resp.status_code == 201
    body = resp.json()
    assert "organization_id" in body and "workspace_id" in body

    # Owner can see members and is OWNER.
    ws = body["workspace_id"]
    members = await client.get(f"/orgs/workspaces/{ws}/members", headers=_auth(token))
    assert members.json()["members"][0]["role"] == "owner"


@pytest.mark.asyncio
async def test_workspace_isolation_blocks_outsider(client):
    owner = await _user(client, "owner@x.com")
    outsider = await _user(client, "outsider@x.com")
    ws = (await client.post("/orgs", json={"name": "Labs"}, headers=_auth(owner))).json()[
        "workspace_id"
    ]

    # Outsider is not a member → 403, not data leak.
    resp = await client.get(f"/orgs/workspaces/{ws}/members", headers=_auth(outsider))
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_invite_requires_admin(client):
    owner = await _user(client, "owner@x.com")
    member_token = await _user(client, "member@x.com")
    ws = (await client.post("/orgs", json={"name": "Labs"}, headers=_auth(owner))).json()[
        "workspace_id"
    ]

    # Owner invites the member as a plain MEMBER.
    inv = await client.post(
        f"/orgs/workspaces/{ws}/invite",
        json={"email": "member@x.com", "role": "member"},
        headers=_auth(owner),
    )
    token = inv.json()["invite_token"]
    await client.post("/orgs/invite/accept", json={"token": token}, headers=_auth(member_token))

    # The MEMBER cannot invite others (requires ADMIN+).
    resp = await client.post(
        f"/orgs/workspaces/{ws}/invite",
        json={"email": "new@x.com", "role": "member"},
        headers=_auth(member_token),
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_invite_accept_grants_membership_and_activity(client):
    owner = await _user(client, "owner@x.com")
    invitee = await _user(client, "invitee@x.com")
    ws = (await client.post("/orgs", json={"name": "Labs"}, headers=_auth(owner))).json()[
        "workspace_id"
    ]

    inv = await client.post(
        f"/orgs/workspaces/{ws}/invite",
        json={"email": "invitee@x.com", "role": "viewer"},
        headers=_auth(owner),
    )
    accept = await client.post(
        "/orgs/invite/accept",
        json={"token": inv.json()["invite_token"]},
        headers=_auth(invitee),
    )
    assert accept.status_code == 201 and accept.json()["role"] == "viewer"

    # Activity feed records the collaboration events.
    feed = await client.get(f"/orgs/workspaces/{ws}/activity", headers=_auth(owner))
    actions = {a["action"] for a in feed.json()["activity"]}
    assert "org.created" in actions and "member.invited" in actions and "member.joined" in actions


@pytest.mark.asyncio
async def test_viewer_cannot_invite_but_can_read(client):
    owner = await _user(client, "owner@x.com")
    viewer = await _user(client, "viewer@x.com")
    ws = (await client.post("/orgs", json={"name": "Labs"}, headers=_auth(owner))).json()[
        "workspace_id"
    ]
    inv = await client.post(
        f"/orgs/workspaces/{ws}/invite",
        json={"email": "viewer@x.com", "role": "viewer"},
        headers=_auth(owner),
    )
    await client.post(
        "/orgs/invite/accept",
        json={"token": inv.json()["invite_token"]},
        headers=_auth(viewer),
    )

    # Viewer can read members...
    assert (
        await client.get(f"/orgs/workspaces/{ws}/members", headers=_auth(viewer))
    ).status_code == 200
    # ...but cannot invite.
    resp = await client.post(
        f"/orgs/workspaces/{ws}/invite",
        json={"email": "z@x.com", "role": "member"},
        headers=_auth(viewer),
    )
    assert resp.status_code == 403
