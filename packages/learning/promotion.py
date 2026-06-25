"""A/B prompt promotion — recommend a winner, never auto-promote (spec §8).

Given per-version stats for a role (from the PerformanceStore), decide whether a
challenger version has earned promotion over the active one. The gate is
deliberately strict and explicit:

  - both versions need at least ``min_samples`` runs (no calls on thin data),
  - the challenger must beat the active version's mean score by ``min_margin``.

Even when the gate passes, this returns a *recommendation* — promotion is an
approval-gated action elsewhere (the dashboard / an operator), never performed
here. This module decides "is it worth proposing?", not "do it."
"""

from __future__ import annotations

from evaluation.stats import Stats
from pydantic import BaseModel

# Conservative defaults: don't even consider a promotion on thin data.
DEFAULT_MIN_SAMPLES = 20
DEFAULT_MIN_MARGIN = 0.05  # challenger must lead by ≥ 5 score points


class PromotionRecommendation(BaseModel):
    """The outcome of evaluating a challenger against the active version."""

    role: str
    active_version: str | None
    candidate_version: str | None
    should_promote: bool
    reason: str
    requires_approval: bool = True  # always — promotion is never automatic


def evaluate_promotion(
    role: str,
    active_version: str | None,
    version_stats: dict[str, Stats],
    *,
    min_samples: int = DEFAULT_MIN_SAMPLES,
    min_margin: float = DEFAULT_MIN_MARGIN,
) -> PromotionRecommendation:
    """Recommend whether to promote a challenger over the active version.

    Pure and deterministic. Never mutates the active prompt — the caller (with
    human approval) does that via the PromptRegistry.
    """

    def no(reason: str, candidate: str | None = None) -> PromotionRecommendation:
        return PromotionRecommendation(
            role=role,
            active_version=active_version,
            candidate_version=candidate,
            should_promote=False,
            reason=reason,
        )

    if active_version is None or active_version not in version_stats:
        return no("No active version with recorded runs to compare against.")

    active = version_stats[active_version]
    if active.runs < min_samples:
        return no(f"Active version has {active.runs} runs (< {min_samples} needed).")

    # Best challenger by mean score, among versions with enough samples.
    challengers = {
        v: s for v, s in version_stats.items() if v != active_version and s.runs >= min_samples
    }
    if not challengers:
        return no(f"No challenger has ≥ {min_samples} runs yet.")

    best_version = max(challengers, key=lambda v: challengers[v].mean_score)
    best = challengers[best_version]
    margin = round(best.mean_score - active.mean_score, 4)

    if margin < min_margin:
        return no(
            f"Best challenger {best_version} leads by {margin} (< {min_margin} needed).",
            candidate=best_version,
        )

    return PromotionRecommendation(
        role=role,
        active_version=active_version,
        candidate_version=best_version,
        should_promote=True,
        reason=(
            f"{best_version} scores {best.mean_score} vs active {active_version} "
            f"{active.mean_score} (+{margin}) over {best.runs}/{active.runs} runs — "
            "propose for approval."
        ),
    )
