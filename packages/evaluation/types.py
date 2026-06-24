"""The Evaluation record — one row per run, capturing outcome *and* cost.

This is the unit everything in Phase 12 reads from: per-agent stats (12.2),
benchmark results (12.5), prompt comparison (12.3/12.8), and the deferred
learning loops (12.9). See ``specs/self-improvement-spec.md`` §1.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class Evaluation(BaseModel):
    """A scored record of a single workflow run.

    Outcome fields answer "did it work?"; cost fields answer "at what price?".
    ``score`` is derived by a versioned rubric so two runs are comparable, and
    ``rubric_version`` records which rubric produced it (a v2 rubric must not be
    compared against v1 scores without noting the difference).
    """

    run_id: str
    task: str

    # --- outcome ---
    success: bool
    tests_passed: bool | None = None
    review_score: int | None = None  # 0-10; None when not reviewed
    retries: int = 0

    # --- cost ---
    execution_time_s: float = 0.0
    tokens: int = 0

    # --- provenance (filled in by later sub-phases) ---
    prompt_versions: dict[str, str] = Field(default_factory=dict)  # role -> version
    model_routing: dict[str, str] = Field(default_factory=dict)  # role -> model id

    # --- deferred signal (backfilled by the GitHub workflow; spec §10) ---
    pr_accepted: bool | None = None

    # --- scoring ---
    score: float  # 0.0-1.0, from the rubric
    rubric_version: str
