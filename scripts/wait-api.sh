#!/usr/bin/env bash
# Wait until the ForgeAI API health endpoint responds (e.g. after `make up`).
set -euo pipefail

API="${FORGE_API:-http://localhost:8000}"
MAX_WAIT="${MAX_WAIT:-90}"

echo "Waiting for $API/health (up to ${MAX_WAIT}s)…"
for ((i = 1; i <= MAX_WAIT; i++)); do
  if curl -fsS "$API/health" >/dev/null 2>&1; then
    echo "API ready."
    exit 0
  fi
  sleep 1
done

echo "ERROR: API not ready after ${MAX_WAIT}s." >&2
echo "  Run: make up && docker compose logs forge-api" >&2
exit 1
