#!/usr/bin/env bash
# Hero demo: drive ForgeAI's gated PR workflow end-to-end through the API.
#
#   "Add JWT Authentication" → proposal → approval → branch → commit → PR → URL
#
# Prereqs:
#   - ForgeAI API running:  make up   (and GITHUB_TOKEN set in .env for a REAL PR)
#   - A sandbox repo, e.g.  forgeai-sandbox-demo  (NEVER a production repo)
#
# Usage:
#   FORGE_API=http://localhost:8000 OWNER=youruser REPO=forgeai-sandbox-demo \
#     bash scripts/demo-pr.sh
set -euo pipefail

API="${FORGE_API:-http://localhost:8000}"
OWNER="${OWNER:?Set OWNER=your-github-username}"
REPO="${REPO:?Set REPO=forgeai-sandbox-demo (a throwaway sandbox repo)}"

jq_get() { python3 -c "import sys,json;print(json.load(sys.stdin)$1)"; }

echo "==> Mode (live requires GITHUB_TOKEN in .env)"
curl -fsS "$API/github/status"; echo

echo "==> 1. Propose a PR for 'Add JWT Authentication' (writes nothing)"
proposal=$(curl -fsS -X POST "$API/github/pr/propose" -H 'Content-Type: application/json' -d "{
  \"owner\":\"$OWNER\", \"name\":\"$REPO\",
  \"task\":\"Add JWT Authentication\",
  \"commit_message\":\"feat(auth): add JWT authentication\",
  \"files\":{\"auth.py\":\"import jwt\\n\\ndef verify(token):\\n    return jwt.decode(token, 'secret', algorithms=['HS256'])\\n\",
             \"requirements.txt\":\"pyjwt\\n\"},
  \"pr_title\":\"feat(auth): JWT authentication\",
  \"pr_summary\":\"Adds JWT verification middleware.\",
  \"changes\":[\"auth.py\",\"requirements.txt\"],
  \"testing\":\"pytest passed\"
}")
echo "$proposal" | python3 -m json.tool
approval_id=$(echo "$proposal" | jq_get "['approval_id']")

echo "==> 2. Pending approvals (the Approval Center's data)"
curl -fsS "$API/github/pr/pending" | python3 -m json.tool

echo "==> 3. Try to execute WITHOUT approval — must be refused (403)"
code=$(curl -s -o /dev/null -w '%{http_code}' -X POST "$API/github/pr/$approval_id/execute")
echo "   HTTP $code (expected 403)"

echo "==> 4. Approve"
curl -fsS -X POST "$API/github/pr/$approval_id/approve" | python3 -m json.tool

echo "==> 5. Execute → creates the real PR (if GITHUB_TOKEN is set)"
result=$(curl -fsS -X POST "$API/github/pr/$approval_id/execute")
echo "$result" | python3 -m json.tool
echo
echo "==> PR URL: $(echo "$result" | jq_get "['pr_url']")"
echo "Hero demo complete ✅  (record from step 1)."
