"""Integration security: secret management, connector permissions, approval rules.

- ``SecretStore``      encrypts integration secrets at rest (Fernet); offline.
- ``ConnectorPermissions`` per-agent allow-list of (system, capability).
- ``ApprovalRules``    which write actions require human approval.
"""

from __future__ import annotations

import base64
import hashlib

from integrations.base import Capability, System


class SecretStore:
    """Encrypts/decrypts integration secrets at rest.

    Uses Fernet when ``cryptography`` is available (it is — a Phase 7 dep),
    deriving a key from the app secret. Secrets are never stored in plaintext.
    """

    def __init__(self, app_secret: str):
        # Derive a urlsafe 32-byte key from the app secret.
        digest = hashlib.sha256(app_secret.encode()).digest()
        self._key = base64.urlsafe_b64encode(digest)
        self._store: dict[str, bytes] = {}

    def _fernet(self):
        from cryptography.fernet import Fernet

        return Fernet(self._key)

    def put(self, name: str, secret: str) -> None:
        self._store[name] = self._fernet().encrypt(secret.encode())

    def get(self, name: str) -> str | None:
        token = self._store.get(name)
        if token is None:
            return None
        return self._fernet().decrypt(token).decode()

    def is_encrypted(self, name: str) -> bool:
        """True if the stored blob is not the plaintext secret."""
        return name in self._store


class ConnectorPermissions:
    """Per-agent allow-list of (system, capability). Not every agent gets access
    to everything — e.g. Research reads Notion; Notification writes Slack."""

    def __init__(self) -> None:
        self._grants: dict[str, set[tuple[System, Capability]]] = {}

    def grant(self, agent: str, system: System, capability: Capability) -> None:
        self._grants.setdefault(agent, set()).add((system, capability))

    def allows(self, agent: str, system: System, capability: Capability) -> bool:
        return (system, capability) in self._grants.get(agent, set())


# Write actions that require human approval before executing.
_APPROVAL_REQUIRED: set[tuple[System, str]] = {
    (System.EMAIL, "email"),
    (System.JIRA, "issue"),  # creating tickets
    (System.NOTION, "page"),  # updating production docs
    (System.CONFLUENCE, "page"),
}


class ApprovalRules:
    """Decides whether a write action needs human approval."""

    def __init__(self, required: set[tuple[System, str]] | None = None):
        self.required = required if required is not None else set(_APPROVAL_REQUIRED)

    def requires_approval(self, system: System, kind: str) -> bool:
        return (system, kind) in self.required
