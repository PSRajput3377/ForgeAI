"""Workflow optimization — recommend skipping a node, never mutate the graph.

From run history, surface that a pipeline step rarely earns its keep for a task
type (e.g. "research is unnecessary for trivial backend tweaks"). Per spec §8
this is a *recommendation for approval*, never a silent graph mutation: this
module produces suggestions; nothing here changes the workflow.

The heuristic is deliberately simple and explicit — it only fires on a large
enough sample where outcomes are uniformly good without the step mattering. Real
attribution needs the deferred outcome data; until then this stays advisory.
"""

from __future__ import annotations

from evaluation.types import Evaluation
from pydantic import BaseModel

DEFAULT_MIN_SAMPLES = 30
DEFAULT_MIN_SUCCESS = 0.95  # only suggest trimming when outcomes are already great


class OptimizationSuggestion(BaseModel):
    """A suggestion to consider removing a step for a task type (advisory only)."""

    task_type: str
    node: str
    suggestion: str
    requires_approval: bool = True  # always — the graph is never auto-edited


def suggest_skips(
    task_type: str,
    evals: list[Evaluation],
    candidate_nodes: list[str],
    *,
    min_samples: int = DEFAULT_MIN_SAMPLES,
    min_success: float = DEFAULT_MIN_SUCCESS,
) -> list[OptimizationSuggestion]:
    """Suggest nodes that *might* be skippable for ``task_type``.

    Conservative: only fires with enough runs and a near-perfect success rate,
    on the premise that if everything already passes, an expensive step may be
    redundant — a hypothesis for a human to test, not a decision. Returns [] on
    thin data so it never over-claims.
    """
    if len(evals) < min_samples:
        return []
    success_rate = sum(1 for e in evals if e.success) / len(evals)
    if success_rate < min_success:
        return []

    return [
        OptimizationSuggestion(
            task_type=task_type,
            node=node,
            suggestion=(
                f"For '{task_type}', {len(evals)} runs succeeded at "
                f"{round(success_rate * 100)}%. Consider A/B testing the pipeline "
                f"without the '{node}' step to see if it still passes (needs approval)."
            ),
        )
        for node in candidate_nodes
    ]
