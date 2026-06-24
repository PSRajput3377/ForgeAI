"""evaluation — measure ForgeAI so it can improve (Phase 12).

After every run the ``EvaluationEngine`` derives one scored ``Evaluation``
record (outcome + cost) via a versioned rubric. Records land in an
``EvaluationStore`` (in-memory now; PostgreSQL behind the same interface in
12.2) and become the substrate everything downstream reads: per-agent stats,
benchmark results, prompt comparison, and the deferred learning loops.

Fully deterministic and offline-testable (``EchoModel``, in-memory store) — no
real models or services required. See ``specs/self-improvement-spec.md``.
"""

from evaluation.engine import EvaluationEngine, extract_review_score
from evaluation.rubric import ACTIVE_RUBRIC, score_v1
from evaluation.stats import Stats, aggregate, by_prompt_version
from evaluation.store import EvaluationStore
from evaluation.types import Evaluation

__all__ = [
    "ACTIVE_RUBRIC",
    "Evaluation",
    "EvaluationEngine",
    "EvaluationStore",
    "Stats",
    "aggregate",
    "by_prompt_version",
    "extract_review_score",
    "score_v1",
]
