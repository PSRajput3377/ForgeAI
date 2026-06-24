"""EvaluationEngine — derive a scored ``Evaluation`` from a finished run.

Reads the final ``ProjectState`` (plus optional cost signals the workflow
gathers) and produces one ``Evaluation`` via the active rubric. Pure and
deterministic: with ``EchoModel`` it runs end-to-end and yields a stable record,
so the whole engine is offline-testable (spec §1, guiding constraint).

Parsing a numeric review score out of free-text review feedback is best-effort;
when nothing usable is present the score is left ``None`` and the rubric simply
doesn't award the review portion.
"""

from __future__ import annotations

import re

from core.state import ProjectState, ReviewVerdict

from evaluation.rubric import ACTIVE_RUBRIC, score_v1
from evaluation.types import Evaluation

# Matches "review_score: 9", "score 9/10", "8 out of 10", etc.
_SCORE_RE = re.compile(r"(?:score\D{0,4})(\d{1,2})\s*(?:/\s*10|out of 10)?", re.IGNORECASE)


def extract_review_score(feedback: str) -> int | None:
    """Best-effort 0-10 review score from free-text feedback, else None."""
    if not feedback:
        return None
    match = _SCORE_RE.search(feedback)
    if not match:
        return None
    value = int(match.group(1))
    return value if 0 <= value <= 10 else None


class EvaluationEngine:
    """Builds ``Evaluation`` records from finished runs using a versioned rubric."""

    def __init__(self, rubric_version: str = ACTIVE_RUBRIC) -> None:
        self.rubric_version = rubric_version

    def evaluate(
        self,
        state: ProjectState,
        *,
        execution_time_s: float = 0.0,
        tokens: int = 0,
        prompt_versions: dict[str, str] | None = None,
        model_routing: dict[str, str] | None = None,
    ) -> Evaluation:
        """Score a finished run. ``success`` == the Review agent approved it."""
        success = state.review_verdict == ReviewVerdict.APPROVED
        review_score = extract_review_score(state.review_feedback)

        score = score_v1(
            success=success,
            review_score=review_score,
            retries=state.retry_count,
            max_retries=state.max_retries,
        )

        return Evaluation(
            run_id=state.project_id or "unknown",
            task=state.user_request,
            success=success,
            tests_passed=state.test_passed,
            review_score=review_score,
            retries=state.retry_count,
            execution_time_s=execution_time_s,
            tokens=tokens,
            prompt_versions=prompt_versions or {},
            model_routing=model_routing or {},
            score=score,
            rubric_version=self.rubric_version,
        )
