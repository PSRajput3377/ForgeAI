"""failures — the Failure Knowledge Base (Phase 12.4).

Turns the Reflection agent's Error → Fix → *Forget* into Error → Fix → Store →
Reuse: failures are stored keyed by a normalized error signature, and a matching
past fix is surfaced on recurrence instead of being re-diagnosed. A surfaced fix
that fails is recorded as a new outcome, so the KB self-corrects.

In-memory store now (offline-testable, injected into Reflection); the
PostgreSQL-backed store lands behind the same interface (spec §4, §7).
"""

from failures.signature import error_signature
from failures.store import FailureStore
from failures.types import Failure, Outcome

__all__ = ["Failure", "FailureStore", "Outcome", "error_signature"]
