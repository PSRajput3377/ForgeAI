"""Feature flags + agent network policy.

- ``FeatureFlags`` toggles experimental agents/models/tools without redeploying;
  supports global on/off and per-workspace overrides.
- ``NetworkPolicy`` allow-lists the domains agent containers may reach (deny by
  default), hardening the sandbox.
"""

from __future__ import annotations

from urllib.parse import urlparse


class FeatureFlags:
    """Global flags with optional per-workspace overrides."""

    def __init__(self, defaults: dict[str, bool] | None = None):
        self._defaults: dict[str, bool] = defaults or {}
        self._overrides: dict[tuple[str, str], bool] = {}

    def set_default(self, flag: str, enabled: bool) -> None:
        self._defaults[flag] = enabled

    def override(self, flag: str, workspace_id: str, enabled: bool) -> None:
        self._overrides[(flag, workspace_id)] = enabled

    def enabled(self, flag: str, workspace_id: str | None = None) -> bool:
        if workspace_id is not None and (flag, workspace_id) in self._overrides:
            return self._overrides[(flag, workspace_id)]
        return self._defaults.get(flag, False)


class NetworkPolicy:
    """Allow-list of domains agent sandboxes may reach. Deny by default."""

    def __init__(self, allowed_domains: set[str] | None = None):
        # Sensible defaults for code work; production overrides per workspace.
        self.allowed = allowed_domains or {
            "github.com",
            "docs.python.org",
            "react.dev",
            "pypi.org",
            "registry.npmjs.org",
        }

    def is_allowed(self, url: str) -> bool:
        host = urlparse(url).hostname or ""
        return any(host == d or host.endswith("." + d) for d in self.allowed)

    def allow(self, domain: str) -> None:
        self.allowed.add(domain)
