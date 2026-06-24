"""benchmarks — the versioned benchmark suite + harness (Phase 12.5).

A fixed set of representative scenarios (add feature, fix bug, refactor, write
tests, create API), each with an expected outcome. The harness runs them through
the real workflow, scores each with the EvaluationEngine, checks expectations,
and rolls up a version-tagged report so every version of ForgeAI is comparable.

Same harness offline (echo provider, deterministic — for CI) and against real
models (true benchmarking); only the injected ModelRouter differs (spec §5).
"""

from benchmarks.harness import (
    BenchmarkReport,
    BenchmarkResult,
    run_benchmarks,
)
from benchmarks.suite import SUITE, SUITE_VERSION, Category, Scenario

__all__ = [
    "SUITE",
    "SUITE_VERSION",
    "BenchmarkReport",
    "BenchmarkResult",
    "Category",
    "Scenario",
    "run_benchmarks",
]
