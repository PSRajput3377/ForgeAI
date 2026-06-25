"""PR-outcome learning — turn a PR merge/close into a labeled signal (spec §10).

When a proposed PR is accepted (merged) or rejected (closed unmerged), that is
the strongest signal we have about whether humans valued the work. This module
maps a raw PR outcome to the boolean the Evaluation record carries
(``pr_accepted``); the actual backfill is done by the PerformanceStore writer
(12.2), and *acting* on the signal is the deferred learned strategy.

Kept tiny and pure on purpose: the seam (classify + a writer protocol) exists
now so the GitHub webhook/poll path can feed it; the learning that consumes it
comes later.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Protocol


class PROutcome(StrEnum):
    """The terminal state of a proposed PR."""

    MERGED = "merged"  # accepted → positive signal
    CLOSED = "closed"  # closed unmerged → negative signal


def outcome_to_signal(outcome: PROutcome) -> bool:
    """Map a PR outcome to the ``pr_accepted`` label (merged → True)."""
    return outcome is PROutcome.MERGED


class AcceptanceWriter(Protocol):
    """What a backfill target must provide (the PerformanceStore satisfies this)."""

    async def set_pr_accepted(self, run_id: str, accepted: bool) -> bool: ...


async def record_pr_outcome(writer: AcceptanceWriter, run_id: str, outcome: PROutcome) -> bool:
    """Backfill the PR outcome for a run as a labeled signal.

    Returns True if a matching evaluation was updated. The signal is *stored*,
    not acted on — consumption is the deferred learned strategy (spec §8/§10).
    """
    return await writer.set_pr_accepted(run_id, outcome_to_signal(outcome))
