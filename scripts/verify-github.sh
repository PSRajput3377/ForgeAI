#!/usr/bin/env bash
# Live GitHub verification against a SANDBOX repository.
#
# Phase 8.1: offline tests cover all logic via the fake provider. This script
# validates the REAL integration (auth scopes, branch/PR creation, pagination,
# rate limits) against a throwaway repo. NEVER run against a production repo.
#
# Usage:
#   export GITHUB_TOKEN=ghp_xxx           # fine-grained PAT, repo scope
#   export FORGE_SANDBOX=youruser/forgeai-sandbox
#   bash scripts/verify-github.sh
set -euo pipefail

: "${GITHUB_TOKEN:?Set GITHUB_TOKEN (fine-grained PAT with repo scope)}"
: "${FORGE_SANDBOX:?Set FORGE_SANDBOX=owner/repo (a throwaway sandbox repo)}"

API="https://api.github.com"
auth=(-H "Authorization: Bearer ${GITHUB_TOKEN}" -H "Accept: application/vnd.github+json")

echo "==> 1. Token identity"
curl -fsS "${auth[@]}" "$API/user" | python3 -c 'import sys,json;print("   user:",json.load(sys.stdin)["login"])'

echo "==> 2. Repository access (read scope)"
curl -fsS "${auth[@]}" "$API/repos/$FORGE_SANDBOX" >/dev/null && echo "   repo readable: $FORGE_SANDBOX"

echo "==> 3. Default branch + branches (pagination smoke)"
curl -fsS "${auth[@]}" "$API/repos/$FORGE_SANDBOX/branches?per_page=1" -D - -o /dev/null \
  | grep -i '^link:' && echo "   (Link header present — pagination works)" || echo "   (single page)"

echo "==> 4. Rate-limit headers"
curl -fsS "${auth[@]}" "$API/rate_limit" \
  | python3 -c 'import sys,json;d=json.load(sys.stdin)["rate"];print(f"   remaining: {d[\"remaining\"]}/{d[\"limit\"]}")'

echo "==> 5. Local clone → branch → commit → push (write + PR scope)"
work="$(mktemp -d)"
git clone "https://x-access-token:${GITHUB_TOKEN}@github.com/${FORGE_SANDBOX}.git" "$work" >/dev/null 2>&1
cd "$work"
branch="forgeai/verify-$(git rev-parse --short HEAD)"
git checkout -b "$branch" >/dev/null
echo "verified at $(date)" > forgeai-verify.txt
git add -A && git -c user.email=verify@forge.ai -c user.name=forgeai commit -m "chore: forgeai verification" >/dev/null
git push -u origin "$branch" >/dev/null 2>&1 && echo "   pushed branch: $branch"

echo "==> 6. Open + close a PR (PR scope)"
pr=$(curl -fsS "${auth[@]}" -X POST "$API/repos/$FORGE_SANDBOX/pulls" \
  -d "{\"title\":\"ForgeAI verification\",\"head\":\"$branch\",\"base\":\"$(git remote show origin | sed -n 's/.*HEAD branch: //p')\",\"body\":\"automated check\"}" \
  | python3 -c 'import sys,json;print(json.load(sys.stdin)["number"])')
echo "   opened PR #$pr"
curl -fsS "${auth[@]}" -X PATCH "$API/repos/$FORGE_SANDBOX/pulls/$pr" -d '{"state":"closed"}' >/dev/null
curl -fsS "${auth[@]}" -X DELETE "$API/repos/$FORGE_SANDBOX/git/refs/heads/$branch" >/dev/null
echo "   closed PR #$pr and deleted branch"

cd - >/dev/null && rm -rf "$work"
echo "==> All live checks passed ✅"
