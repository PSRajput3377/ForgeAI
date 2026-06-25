#!/usr/bin/env bash
# End-to-end Todo API demo — register → bootstrap FastAPI starter → 4 agent runs
# → approve & execute each PR on your GitHub sandbox.
#
# Prereqs:
#   make up
#   GITHUB_TOKEN, GITHUB_OWNER, GITHUB_REPO in .env (live PR execute)
#
# Usage:
#   bash scripts/demo-todo-e2e.sh
#   DRY_RUN=1 bash scripts/demo-todo-e2e.sh    # propose only, no GitHub execute
#   FORGE_API=http://localhost:8000 bash scripts/demo-todo-e2e.sh
#
# Tip: set MODEL_PROVIDER=echo for an instant flow test; use ollama for real code.
set -euo pipefail

API="${FORGE_API:-http://localhost:8000}"
EMAIL="${DEMO_EMAIL:-todo-demo-$(date +%s)@example.com}"
PASS="${DEMO_PASS:-changeme123}"
DRY_RUN="${DRY_RUN:-0}"

jq_get() { python3 -c "import sys,json; print(json.load(sys.stdin)$1)"; }

# POST and exit with the API error body on failure (not just "curl: 22").
api_post() {
  local url="$1"
  shift
  local resp code body
  resp=$(curl -s -w "\n%{http_code}" -X POST "$url" "$@")
  code=$(echo "$resp" | tail -1)
  body=$(echo "$resp" | sed '$d')
  if [[ "$code" -lt 200 || "$code" -ge 300 ]]; then
    echo "ERROR HTTP $code from $url" >&2
    echo "$body" | python3 -m json.tool 2>/dev/null || echo "$body" >&2
    exit 1
  fi
  echo "$body"
}

step() { echo ""; echo "==> $*"; }

# After `make up` recreates forge-api, uvicorn needs a few seconds to bind.
bash "$(dirname "$0")/wait-api.sh"

step "Health check"
curl -fsS "$API/health" | python3 -m json.tool
step "GitHub mode"
curl -fsS "$API/github/status" | python3 -m json.tool

step "1. Register & login ($EMAIL)"
curl -fsS -X POST "$API/auth/register" \
  -H 'Content-Type: application/json' \
  -d "{\"email\":\"$EMAIL\",\"name\":\"Todo Demo\",\"password\":\"$PASS\"}" > /dev/null

TOKEN=$(curl -fsS -X POST "$API/auth/login" \
  -H 'Content-Type: application/json' \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASS\"}" \
  | jq_get '["access_token"]')
AUTH="Authorization: Bearer $TOKEN"
echo "   token acquired"

step "2. Create workspace"
WS=$(curl -fsS -X POST "$API/orgs" \
  -H 'Content-Type: application/json' -H "$AUTH" \
  -d '{"name":"Todo Demo Workspace"}' | jq_get '["workspace_id"]')
echo "   workspace_id=$WS"

step "3. Bootstrap FastAPI SaaS project"
PROJECT_JSON=$(curl -fsS -X POST "$API/projects/bootstrap" \
  -H 'Content-Type: application/json' -H "$AUTH" \
  -d "{\"workspace_id\":\"$WS\",\"name\":\"Todo API\",\"starter\":\"fastapi-saas\"}")
PID=$(echo "$PROJECT_JSON" | jq_get '["id"]')
SCAFFOLD_COUNT=$(echo "$PROJECT_JSON" | python3 -c 'import sys,json; print(len(json.load(sys.stdin)["scaffolded_files"]))')
echo "   project_id=$PID"
echo "   scaffolded $SCAFFOLD_COUNT files (app/main.py, tests, Docker, …)"

TASKS=(
  "Add a Todo SQLAlchemy model with fields id, title, done, and owner_id"
  "Add CRUD REST endpoints for todos at /todos — list, create, update, delete"
  "Scope todos to the authenticated user from JWT — users only see their own todos"
  "Add pytest tests for all todo endpoints including auth checks"
)

PR_URLS=()

run_task() {
  local n="$1"
  local task="$2"
  step "4.$n Agent run: ${task:0:60}…"
  RUN=$(curl -fsS -X POST "$API/agents/run" \
    -H 'Content-Type: application/json' -H "$AUTH" \
    -d "{\"user_request\":\"$task\",\"project_id\":\"$PID\"}")
  VERDICT=$(echo "$RUN" | jq_get '["review_verdict"]')
  APPROVAL=$(echo "$RUN" | jq_get '.get("pr_approval_id") or ""')
  WRITTEN=$(echo "$RUN" | python3 -c 'import sys,json; print(len(json.load(sys.stdin).get("written_files") or []))')
  echo "   verdict=$VERDICT  files_written=$WRITTEN  pr_approval_id=${APPROVAL:-none}"

  if [[ -z "$APPROVAL" ]]; then
    echo "   (no PR proposed — check GITHUB_OWNER/GITHUB_REPO in .env)"
    return
  fi

  if [[ "$DRY_RUN" == "1" ]]; then
    echo "   DRY_RUN=1 — skipping approve/execute"
    return
  fi

  step "4.$n Approve PR $APPROVAL"
  api_post "$API/github/pr/$APPROVAL/approve" -H "$AUTH" | python3 -m json.tool

  step "4.$n Execute → GitHub"
  RESULT=$(api_post "$API/github/pr/$APPROVAL/execute" -H "$AUTH")
  URL=$(echo "$RESULT" | jq_get '.get("pr_url") or ""')
  echo "$RESULT" | python3 -m json.tool
  if [[ -n "$URL" ]]; then
    PR_URLS+=("$URL")
    echo "   PR: $URL"
  fi
}

for i in "${!TASKS[@]}"; do
  run_task "$((i + 1))" "${TASKS[$i]}"
done

step "5. Pending approvals (should be empty if all executed)"
curl -fsS "$API/github/pr/pending" | python3 -m json.tool

step "6. Analytics overview"
curl -fsS "$API/analytics/overview" | python3 -m json.tool

echo ""
echo "=============================================="
echo "Todo API demo complete"
echo "  Account:  $EMAIL / $PASS"
echo "  Project:  $PID"
if [[ ${#PR_URLS[@]} -gt 0 ]]; then
  echo "  PRs:"
  for u in "${PR_URLS[@]}"; do echo "    $u"; done
else
  echo "  PRs: none (DRY_RUN or missing GitHub config)"
fi
echo "=============================================="
