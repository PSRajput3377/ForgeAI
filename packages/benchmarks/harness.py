"""Benchmark harness — run the suite through the real workflow, score, compare.

Same harness offline (echo provider, deterministic — for CI) and against real
models (true benchmarking): only the injected ``ModelRouter`` differs (spec §5).
Each scenario runs through ``run_workflow`` with a fresh ``EvaluationStore``, is
scored by the ``EvaluationEngine`` we already ship, checked against its expected
outcome, and rolled up into a ``BenchmarkReport`` tagged with the ForgeAI
version so versions are comparable.
"""

from __future__ import annotations

from agents.workflow import run_workflow
from evaluation import Evaluation, EvaluationStore
from evaluation.stats import Stats, aggregate
from models.router import ModelRouter
from pydantic import BaseModel

from benchmarks.suite import SUITE, SUITE_VERSION, Scenario


class BenchmarkResult(BaseModel):
    """The outcome of one scenario: its evaluation plus whether it met expectations."""

    scenario_id: str
    category: str
    evaluation: Evaluation
    met_expectations: bool


class BenchmarkReport(BaseModel):
    """All results for one run of the suite, tagged with versions for comparison."""

    forge_version: str
    suite_version: str
    results: list[BenchmarkResult]
    stats: Stats
    pass_rate: float  # fraction of scenarios that met expectations


def _met_expectations(scenario: Scenario, ev: Evaluation) -> bool:
    """A scenario passes if the run matched its expected outcome and stayed
    within the retry budget."""
    return ev.success == scenario.expect_success and ev.retries <= scenario.max_retries


async def run_benchmarks(
    router: ModelRouter,
    *,
    forge_version: str,
    scenarios: list[Scenario] | None = None,
    **run_kwargs,
) -> BenchmarkReport:
    """Run the suite and return a versioned report.

    ``forge_version`` tags the report so successive versions are comparable.
    Extra ``run_kwargs`` (e.g. ``engine_factory``) pass through to the workflow.
    """
    cases = scenarios if scenarios is not None else SUITE
    results: list[BenchmarkResult] = []

    for scenario in cases:
        store = EvaluationStore()
        await run_workflow(
            router,
            scenario.request,
            project_id=scenario.id,
            evaluation_store=store,
            **run_kwargs,
        )
        ev = store.for_run(scenario.id)
        results.append(
            BenchmarkResult(
                scenario_id=scenario.id,
                category=scenario.category.value,
                evaluation=ev,
                met_expectations=_met_expectations(scenario, ev),
            )
        )

    passed = sum(1 for r in results if r.met_expectations)
    return BenchmarkReport(
        forge_version=forge_version,
        suite_version=SUITE_VERSION,
        results=results,
        stats=aggregate([r.evaluation for r in results]),
        pass_rate=(passed / len(results)) if results else 0.0,
    )
