"""learning — the self-improvement loops, scaffolded behind safe defaults.

Phase 12.9 lands these as interfaces with conservative defaults and explicit
approval gates; none auto-acts on production until documented data thresholds
are met (spec §8, §10). They consume the measurement substrate (12.1–12.8) and
switch from "recommend" to "act" via a learned strategy once real usage data
exists — without changing the agents or the workflow graph.

  - promotion:    A/B prompt promotion — recommend a winner, never auto-promote.
  - workflow_opt: suggest skippable pipeline steps — never mutate the graph.
  - pr_outcome:   map a PR merge/close to a labeled signal — stored, not acted on.
"""

from learning.pr_outcome import PROutcome, outcome_to_signal, record_pr_outcome
from learning.promotion import (
    DEFAULT_MIN_MARGIN,
    DEFAULT_MIN_SAMPLES,
    PromotionRecommendation,
    evaluate_promotion,
)
from learning.workflow_opt import OptimizationSuggestion, suggest_skips

__all__ = [
    "DEFAULT_MIN_MARGIN",
    "DEFAULT_MIN_SAMPLES",
    "OptimizationSuggestion",
    "PROutcome",
    "PromotionRecommendation",
    "evaluate_promotion",
    "outcome_to_signal",
    "record_pr_outcome",
    "suggest_skips",
]
