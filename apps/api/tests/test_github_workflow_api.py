"""API tests for the persisted, approval-gated PR endpoints (offline)."""

import pytest

# Uses the async `client` fixture (in-memory SQLite) from conftest.py so the
# PRApproval rows persist across requests within a test.

PR_BODY = {
    "owner": "psr",
    "name": "forge",
    "kind": "feature",
    "task": "Add JWT authentication",
    "commit_message": "feat(auth): add JWT",
    "files": {"auth.py": "import jwt", "requirements.txt": "pyjwt"},
    "pr_title": "feat(auth): JWT authentication",
    "pr_summary": "Adds JWT auth",
    "changes": ["routes", "middleware"],
    "testing": "pytest passed",
}


@pytest.mark.asyncio
async def test_full_gated_flow_propose_approve_execute(client):
    # 1. Propose — persists a pending approval, writes nothing to GitHub.
    proposed = (await client.post("/github/pr/propose", json=PR_BODY)).json()
    approval_id = proposed["approval_id"]
    assert proposed["status"] == "pending"
    assert proposed["branch"] == "feature/add-jwt-authentication"
    assert set(proposed["files_changed"]) == {"auth.py", "requirements.txt"}

    # Appears in the pending list (Approval Center source).
    pending = (await client.get("/github/pr/pending")).json()["pending"]
    assert any(p["approval_id"] == approval_id for p in pending)

    # Diff viewer can fetch proposed file contents.
    diff = (await client.get(f"/github/pr/{approval_id}/diff")).json()
    assert {f["path"] for f in diff["files"]} == {"auth.py", "requirements.txt"}

    # 2. Executing before approval is forbidden (id-only, one-click).
    early = await client.post(f"/github/pr/{approval_id}/execute")
    assert early.status_code == 403

    # 3. Approve, then execute → PR created with a URL.
    approved = (await client.post(f"/github/pr/{approval_id}/approve")).json()
    assert approved["status"] == "approved"
    done = (await client.post(f"/github/pr/{approval_id}/execute")).json()
    assert done["approved"] is True
    assert done["pr_url"].endswith("/pull/1")

    # No longer pending after approval.
    pending_after = (await client.get("/github/pr/pending")).json()["pending"]
    assert all(p["approval_id"] != approval_id for p in pending_after)


@pytest.mark.asyncio
async def test_rejected_proposal_cannot_execute(client):
    proposed = (await client.post("/github/pr/propose", json=PR_BODY)).json()
    approval_id = proposed["approval_id"]
    rejected = (await client.post(f"/github/pr/{approval_id}/reject")).json()
    assert rejected["status"] == "rejected"
    blocked = await client.post(f"/github/pr/{approval_id}/execute")
    assert blocked.status_code == 403


@pytest.mark.asyncio
async def test_proposal_persists_across_requests(client):
    """A proposal persisted by one request is visible to a later request —
    proving durability (DB-backed, not in-memory)."""
    proposed = (await client.post("/github/pr/propose", json=PR_BODY)).json()
    approval_id = proposed["approval_id"]
    fetched = await client.get(f"/github/pr/{approval_id}")
    assert fetched.status_code == 200
    assert fetched.json()["pr_title"] == PR_BODY["pr_title"]


@pytest.mark.asyncio
async def test_unknown_proposal_404(client):
    assert (await client.get("/github/pr/nope")).status_code == 404
    assert (await client.get("/github/pr/nope/diff")).status_code == 404
