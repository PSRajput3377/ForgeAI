"""API tests for the approval-gated PR endpoints (offline, fake provider)."""

from fastapi.testclient import TestClient

from app.main import app

PR_BODY = {
    "owner": "psr",
    "name": "forge",
    "kind": "feature",
    "task": "Add JWT authentication",
    "commit_message": "feat(auth): add JWT",
    "files": {"auth.py": "import jwt"},
    "pr_title": "feat(auth): JWT authentication",
    "pr_summary": "Adds JWT auth",
    "changes": ["routes", "middleware"],
    "testing": "pytest passed",
}


def test_full_gated_flow_propose_approve_execute():
    client = TestClient(app)

    # 1. Propose — returns an approval id, writes nothing.
    proposed = client.post("/github/pr/propose", json=PR_BODY).json()
    approval_id = proposed["approval_id"]
    assert proposed["status"] == "pending"
    assert proposed["branch"] == "feature/add-jwt-authentication"

    # 2. Executing before approval is forbidden.
    early = client.post(f"/github/pr/{approval_id}/execute", json=PR_BODY)
    assert early.status_code == 403

    # 3. Approve, then execute → PR created with a URL.
    assert (
        client.post(f"/github/pr/{approval_id}/approve").json()["status"] == "approved"
    )
    done = client.post(f"/github/pr/{approval_id}/execute", json=PR_BODY).json()
    assert done["approved"] is True
    assert done["pr_url"].endswith("/pull/1")


def test_rejected_proposal_cannot_execute():
    client = TestClient(app)
    proposed = client.post("/github/pr/propose", json=PR_BODY).json()
    approval_id = proposed["approval_id"]
    assert (
        client.post(f"/github/pr/{approval_id}/reject").json()["status"] == "rejected"
    )
    blocked = client.post(f"/github/pr/{approval_id}/execute", json=PR_BODY)
    assert blocked.status_code == 403
