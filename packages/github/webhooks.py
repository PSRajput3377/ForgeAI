"""GitHub webhook handling — event-driven instead of polling.

Verifies the HMAC signature GitHub sends (`X-Hub-Signature-256`), parses the
event, and maps it to a ForgeAI ``Event`` so the rest of the platform reacts
without polling. The mapping is pure/offline-testable; signature verification
uses the configured webhook secret.
"""

from __future__ import annotations

import hashlib
import hmac

from observability.events import Event, EventType

# GitHub event (X-GitHub-Event) + action → a ForgeAI EventType.
_EVENT_MAP: dict[tuple[str, str | None], EventType] = {
    ("pull_request", "opened"): EventType.NOTIFICATION,
    ("pull_request", "closed"): EventType.NOTIFICATION,
    ("issues", "opened"): EventType.NOTIFICATION,
    ("check_run", "completed"): EventType.BUILD_PASSED,
    ("check_suite", "completed"): EventType.BUILD_PASSED,
}


def verify_signature(secret: str, body: bytes, signature_header: str | None) -> bool:
    """Verify the `X-Hub-Signature-256` HMAC. Constant-time comparison."""
    if not signature_header or not signature_header.startswith("sha256="):
        return False
    expected = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature_header)


def map_webhook(github_event: str, payload: dict) -> Event:
    """Map a GitHub webhook to a ForgeAI Event.

    For check events, a failed conclusion maps to BUILD_FAILED so the CI
    self-correction loop can be triggered by a push instead of a poll.
    """
    action = payload.get("action")

    if github_event in ("check_run", "check_suite"):
        block = payload.get(github_event, {})
        conclusion = block.get("conclusion")
        etype = EventType.BUILD_FAILED if conclusion == "failure" else EventType.BUILD_PASSED
        return Event(
            type=etype,
            payload={
                "source": "github",
                "event": github_event,
                "conclusion": conclusion,
            },
        )

    etype = _EVENT_MAP.get((github_event, action), EventType.NOTIFICATION)
    detail: dict = {"source": "github", "event": github_event, "action": action}
    if "pull_request" in payload:
        detail["pr_number"] = payload["pull_request"].get("number")
    if github_event == "issues" and "issue" in payload:
        detail["issue_number"] = payload["issue"].get("number")
    return Event(type=etype, payload=detail)
