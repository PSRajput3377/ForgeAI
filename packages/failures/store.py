"""Failure Knowledge Base — store + reuse of error→fix episodes (spec §4, §7).

Like Stack Overflow for ForgeAI itself: when an error recurs, surface the fix
that worked last time instead of re-diagnosing from scratch.

Phase 12.4 ships the in-memory store (offline-testable, injected into the
Reflection agent); the PostgreSQL-backed store lands behind the same interface
(``apps/api/app/failure_kb.py``), mirroring how the evaluation store evolved
(ADR-0025).

Reuse policy: ``recall`` returns the best known fix for a signature — a
``RESOLVED`` one if any exists, else the most-seen ``UNKNOWN`` candidate. A
surfaced fix that fails is recorded as a new ``FAILED`` outcome, so the KB
self-corrects and no fix is trusted permanently.
"""

from __future__ import annotations

from failures.signature import error_signature
from failures.types import Failure, Outcome


class FailureStore:
    """In-memory append/merge store of failures, keyed by error signature."""

    def __init__(self) -> None:
        # signature -> list of episodes (newest last)
        self._by_sig: dict[str, list[Failure]] = {}

    def record(
        self,
        error: str,
        *,
        cause: str = "",
        fix: str = "",
        outcome: Outcome = Outcome.UNKNOWN,
    ) -> Failure:
        """Store an error→fix episode. The signature is derived from ``error``.

        Re-recording a known signature bumps its hit count; a new distinct fix
        is appended as its own episode so competing fixes coexist until outcomes
        decide between them.
        """
        sig = error_signature(error)
        episodes = self._by_sig.setdefault(sig, [])

        for ep in episodes:
            if ep.fix == fix:
                ep.hits += 1
                # An observed outcome always supersedes UNKNOWN.
                if outcome is not Outcome.UNKNOWN:
                    ep.outcome = outcome
                if cause and not ep.cause:
                    ep.cause = cause
                return ep

        episode = Failure(signature=sig, error=error, cause=cause, fix=fix, outcome=outcome)
        episodes.append(episode)
        return episode

    def recall(self, error: str) -> Failure | None:
        """Best known fix for an error's signature, or None if unseen/unfixed.

        Prefers a ``RESOLVED`` episode; otherwise the most-seen non-failed
        candidate. Episodes with no fix, or only ``FAILED`` ones, return None.
        """
        sig = error_signature(error)
        episodes = self._by_sig.get(sig, [])
        candidates = [e for e in episodes if e.fix and e.outcome is not Outcome.FAILED]
        if not candidates:
            return None
        resolved = [e for e in candidates if e.outcome is Outcome.RESOLVED]
        pool = resolved or candidates
        return max(pool, key=lambda e: e.hits)

    def all(self) -> list[Failure]:
        return [ep for episodes in self._by_sig.values() for ep in episodes]

    def for_signature(self, signature: str) -> list[Failure]:
        return list(self._by_sig.get(signature, []))
