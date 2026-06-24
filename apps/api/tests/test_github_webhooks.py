"""Webhook signature verification + event mapping."""

import hashlib
import hmac
import json

from github.webhooks import map_webhook, verify_signature
from observability.events import EventType


def _sign(secret: str, body: bytes) -> str:
    return "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def test_verify_valid_signature():
    secret = "s3cret"
    body = b'{"action":"opened"}'
    assert verify_signature(secret, body, _sign(secret, body)) is True


def test_verify_rejects_tampered_body():
    secret = "s3cret"
    sig = _sign(secret, b'{"action":"opened"}')
    assert verify_signature(secret, b'{"action":"closed"}', sig) is False


def test_verify_rejects_missing_or_malformed():
    assert verify_signature("s", b"x", None) is False
    assert verify_signature("s", b"x", "md5=abc") is False


def test_map_pull_request_opened():
    payload = {"action": "opened", "pull_request": {"number": 42}}
    event = map_webhook("pull_request", payload)
    assert event.type == EventType.NOTIFICATION
    assert event.payload["pr_number"] == 42


def test_map_issue_opened():
    event = map_webhook("issues", {"action": "opened", "issue": {"number": 7}})
    assert event.payload["issue_number"] == 7


def test_map_failed_check_run_triggers_build_failed():
    payload = {"action": "completed", "check_run": {"conclusion": "failure"}}
    event = map_webhook("check_run", payload)
    assert event.type == EventType.BUILD_FAILED
    assert event.payload["conclusion"] == "failure"


def test_map_passed_check_suite():
    payload = {"action": "completed", "check_suite": {"conclusion": "success"}}
    event = map_webhook("check_suite", payload)
    assert event.type == EventType.BUILD_PASSED


def test_signed_payload_roundtrip():
    secret = "whsecret"
    payload = {"action": "opened", "pull_request": {"number": 1}}
    body = json.dumps(payload).encode()
    assert verify_signature(secret, body, _sign(secret, body))
    assert map_webhook("pull_request", payload).payload["pr_number"] == 1
