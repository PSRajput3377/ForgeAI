"""API tests for the approval-gated PR endpoints (offline, fake provider)."""

from fastapi.testclient import TestClient

from app.main import app

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


def test_full_gated_flow_propose_approve_execute():
    client = TestClient(app)

    # 1. Propose — returns an approval id + proposal view, writes nothing.
    proposed = client.post("/github/pr/propose", json=PR_BODY).json()
    approval_id = proposed["approval_id"]
    assert proposed["status"] == "pending"
    assert proposed["branch"] == "feature/add-jwt-authentication"
    assert set(proposed["files_changed"]) == {"auth.py", "requirements.txt"}

    # It shows up in the pending list (Approval Center data source).
    pending = client.get("/github/pr/pending").json()["pending"]
    assert any(p["approval_id"] == approval_id for p in pending)

    # The diff viewer can fetch proposed file contents.
    diff = client.get(f"/github/pr/{approval_id}/diff").json()
    paths = {f["path"] for f in diff["files"]}
    assert paths == {"auth.py", "requirements.txt"}

    # 2. Executing before approval is forbidden (one-click, id-only).
    early = client.post(f"/github/pr/{approval_id}/execute")
    assert early.status_code == 403

    # 3. Approve, then execute → PR created with a URL.
    assert client.post(f"/github/pr/{approval_id}/approve").json()["status"] == "approved"
    done = client.post(f"/github/pr/{approval_id}/execute").json()
    assert done["approved"] is True
    assert done["pr_url"].endswith("/pull/1")

    # No longer pending after approval.
    pending_after = client.get("/github/pr/pending").json()["pending"]
    assert all(p["approval_id"] != approval_id for p in pending_after)


def test_rejected_proposal_cannot_execute():
    client = TestClient(app)
    proposed = client.post("/github/pr/propose", json=PR_BODY).json()
    approval_id = proposed["approval_id"]
    assert client.post(f"/github/pr/{approval_id}/reject").json()["status"] == "rejected"
    blocked = client.post(f"/github/pr/{approval_id}/execute")
    assert blocked.status_code == 403


def test_unknown_proposal_404():
    client = TestClient(app)
    assert client.get("/github/pr/nope").status_code == 404
    assert client.get("/github/pr/nope/diff").status_code == 404
