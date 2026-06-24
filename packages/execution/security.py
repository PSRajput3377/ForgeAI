"""Security layer for code execution: blocked commands and resource limits.

Every sandbox calls ``check_command`` before running anything. AI-generated
commands are untrusted, so destructive operations are hard-blocked regardless of
sandbox isolation (defense in depth).
"""

from __future__ import annotations

import re

from pydantic import BaseModel

# Patterns that are never allowed, even inside a container.
_BLOCKED_PATTERNS = [
    r"\brm\s+-rf\s+/",  # rm -rf / (and variants)
    r"\brm\s+-rf\s+~",
    r"\bsudo\b",
    r"\bchmod\s+777\b",
    r"\bchown\b",
    r"\bshutdown\b",
    r"\breboot\b",
    r"\bmkfs\b",
    r"\bdd\s+if=",
    r":\(\)\s*\{.*\};:",  # fork bomb
    r">\s*/dev/sd",  # writing to raw disks
    r"\bcurl\b.*\|\s*(sh|bash)",  # curl | sh
    r"\bwget\b.*\|\s*(sh|bash)",
]

_BLOCKED_RE = [re.compile(p) for p in _BLOCKED_PATTERNS]


class ResourceLimits(BaseModel):
    """Per-sandbox resource quotas. Prevents runaway execution."""

    cpus: float = 2.0
    memory_mb: int = 2048
    timeout: float = 300.0


def check_command(command: str) -> str | None:
    """Return a reason string if the command is blocked, else None."""
    lowered = command.lower()
    for pattern in _BLOCKED_RE:
        if pattern.search(lowered):
            return f"Blocked command (matched safety rule): {command!r}"
    return None
