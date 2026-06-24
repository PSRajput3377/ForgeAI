"""Error-signature normalization — the key that makes recurring errors collide.

A failure's *signature* is a stable, normalized key derived from its error text,
so the same underlying problem (e.g. a missing ``jwt`` module) maps to one KB
entry across runs regardless of surrounding noise (spec §4). Volatile detail —
file paths, line numbers, hex addresses, quotes — is stripped; the exception
type and the salient identifier are kept.
"""

from __future__ import annotations

import re

# "ModuleNotFoundError", "ImportError", "RuntimeException", "DeprecationWarning"
_EXC_RE = re.compile(r"\b(\w*(?:Error|Exception|Warning))\b")
# A quoted identifier, e.g. No module named 'jwt'  →  jwt
_QUOTED_RE = re.compile(r"['\"`]([\w.\-]+)['\"`]")
_HEX_RE = re.compile(r"0x[0-9a-fA-F]+")
_NUM_RE = re.compile(r"\d+")


def error_signature(text: str) -> str:
    """Normalize raw error text into a stable signature key.

    ``ModuleNotFoundError: No module named 'jwt'``  → ``modulenotfounderror:jwt``
    ``ImportError: cannot import name 'Foo' ...``    → ``importerror:foo``
    Unrecognized text falls back to a normalized slug of its first line, so even
    untyped failures collide when they recur.
    """
    if not text or not text.strip():
        return "unknown"

    # Prefer the last exception type mentioned (tracebacks end with the real one).
    exc_match = list(_EXC_RE.finditer(text))
    exc = exc_match[-1].group(1).lower() if exc_match else None

    quoted = _QUOTED_RE.search(text)
    if exc and quoted:
        return f"{exc}:{quoted.group(1).lower()}"
    if exc:
        return exc

    # No exception type — slugify the first non-empty line, stripped of volatile
    # tokens, so recurring untyped messages still share a key.
    first_line = next((ln for ln in text.splitlines() if ln.strip()), "")
    cleaned = _HEX_RE.sub("", first_line)
    cleaned = _NUM_RE.sub("", cleaned)
    slug = re.sub(r"[^a-z0-9]+", "-", cleaned.lower()).strip("-")
    return slug[:64] or "unknown"
