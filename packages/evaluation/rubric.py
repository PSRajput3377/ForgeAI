"""Versioned scoring rubric — turns a run's signals into one comparable number.

The rubric is the *documented, versioned* function from outcome+cost to a
``score`` in [0, 1] (spec §1). Versioning matters: changing the weights changes
every score, so a new rubric is a new named version, never an edit to ``v1``.
Two evaluations are only directly comparable when their ``rubric_version``
matches.

``v1`` is intentionally simple and deterministic: it rewards success, a clean
review, and few retries. Efficiency (time/tokens) is recorded on the record but
not yet folded into the score — adding it would be ``v2``.
"""

from __future__ import annotations

ACTIVE_RUBRIC = "v1"


def score_v1(
    *,
    success: bool,
    review_score: int | None,
    retries: int,
    max_retries: int = 2,
) -> float:
    """Weighted score in [0, 1]. Deterministic — no model calls.

    Weights (sum to 1.0):
      - success      0.6  — did the run achieve the outcome at all?
      - review_score 0.3  — quality, as the Review agent's 0-10 judgement.
      - retries      0.1  — efficiency: full credit at 0 retries, 0 at the cap.
    """
    success_pts = 0.6 if success else 0.0

    # Review contributes only when a review happened; absent → no credit (its
    # weight is simply not earned, which keeps unreviewed runs from looking good).
    review_pts = 0.3 * (review_score / 10) if review_score is not None else 0.0

    # Retry credit decays linearly to zero at the retry cap.
    cap = max_retries if max_retries > 0 else 1
    retry_pts = 0.1 * max(0.0, 1.0 - retries / cap)

    return round(success_pts + review_pts + retry_pts, 4)
