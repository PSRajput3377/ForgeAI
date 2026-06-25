"""End-to-end Phase 12 walkthrough — runs the whole self-improving loop offline.

Deterministic (EchoModel + in-memory stores): no Docker, no models, no network.
Run from apps/api:  uv run python ../../scripts/demo_phase12.py
"""

import asyncio

from agents.workflow import run_workflow
from core.roles import AgentRole
from core.state import ProjectState, ReviewVerdict
from evaluation import EvaluationStore
from evaluation.stats import aggregate
from failures import FailureStore, Outcome
from learning import PROutcome, evaluate_promotion, outcome_to_signal, suggest_skips
from marketplace import AgentDescriptor, MarketplaceRegistry, check_agent_contract
from models.echo import EchoProvider
from models.router import ModelRouter
from prompts import REGISTRY, active_versions, system_prompt
from selection import RuleBasedSelector


def line(title):
    print(f"\n{'=' * 70}\n{title}\n{'=' * 70}")


def echo_router():
    role_models = {role: f"echo-{role.value}" for role in AgentRole}
    return ModelRouter(
        provider=EchoProvider(),
        role_models=role_models,
        embed_model="echo-embed",
        default_model="echo-default",
    )


async def main():
    router = echo_router()
    evals = EvaluationStore()
    failures = FailureStore()
    selector = RuleBasedSelector()

    # ---- STEP 1: classify the task (12.7) ----------------------------------
    line("STEP 1 — Dynamic agent selection (12.7): classify the request")
    request = "Add JWT authentication to the API"
    sel = selector.select(ProjectState(user_request=request))
    print(f"Request:   {request!r}")
    print(f"Task type: {sel.task_type.value}")
    print(f"Rationale: {sel.rationale}")

    # ---- STEP 2: run the full pipeline with everything wired (12.1/6/7) -----
    line("STEP 2 — Run the multi-agent workflow (debate ON, scored, classified)")
    final = await run_workflow(
        router,
        request,
        project_id="demo-run-1",
        evaluation_store=evals,       # 12.1 — score the run
        failure_store=failures,       # 12.4 — remember failures
        selection_strategy=selector,  # 12.7 — classify at intake
        debate_planner=3,             # 12.6 — 3 planners debate the plan
    )
    print(f"Verdict:    {final.review_verdict.value}")
    print(f"Tasks:      {len(final.tasks)}   Retries: {final.retry_count}")
    print(f"Task type recorded on state: {final.task_type}")
    print("\nAgent timeline (who did what):")
    for m in final.messages:
        print(f"  - {m.sender.value:11} {m.status.value:11} {m.summary}")

    # ---- STEP 3: the debate decision (12.6) --------------------------------
    line("STEP 3 — Multi-agent debate (12.6): the recorded decision")
    planner_msg = next(m for m in final.messages if m.sender == AgentRole.PLANNER)
    print(f"Summary:  {planner_msg.summary}")
    print(f"Winner:   attempt {planner_msg.payload.get('debate_winner')}")
    print(f"Judge:    {planner_msg.payload.get('debate_rationale', '')[:90]}…")

    # ---- STEP 4: the evaluation record (12.1) ------------------------------
    line("STEP 4 — Evaluation Engine (12.1): the scored record")
    ev = evals.for_run("demo-run-1")
    print(f"run_id={ev.run_id}  success={ev.success}  score={ev.score}  "
          f"rubric={ev.rubric_version}")
    print(f"prompt_versions used: {ev.prompt_versions}")

    # ---- STEP 5: failure memory (12.4) -------------------------------------
    line("STEP 5 — Failure Knowledge Base (12.4): store → reuse")
    err = "ModuleNotFoundError: No module named 'jwt'"
    failures.record(err, fix="pip install pyjwt", outcome=Outcome.RESOLVED)
    print(f"Stored fix for: {err}")
    hit = failures.recall("Traceback...\nModuleNotFoundError: No module named 'jwt'")
    print(f"Recall on recurrence → signature={hit.signature!r}  fix={hit.fix!r}")
    print("  (note: same root cause collides on one signature despite traceback noise)")

    # ---- STEP 6: prompt versioning + A/B promotion (12.3 + 12.9) -----------
    line("STEP 6 — Prompt versioning (12.3) + A/B promotion gate (12.9)")
    print(f"Active planner prompt version: {active_versions()['planner']}")
    REGISTRY.register(AgentRole.PLANNER, "v2", "Plan with explicit acceptance criteria.")
    print("Registered planner v2 (now active). v1 preserved (append-only):")
    print(f"  v1 still retrievable: {REGISTRY.get(AgentRole.PLANNER, 'v1')[:40]!r}…")

    # Promotion is gated: thin data → no promotion, even if v2 looks better.
    from evaluation.stats import Stats
    thin = {"v1": Stats(runs=1, mean_score=0.7), "v2": Stats(runs=1, mean_score=0.9)}
    rec = evaluate_promotion("planner", "v1", thin)
    print(f"\nPromotion on thin data: should_promote={rec.should_promote}")
    print(f"  reason: {rec.reason}")
    strong = {"v1": Stats(runs=50, mean_score=0.70), "v2": Stats(runs=50, mean_score=0.82)}
    rec2 = evaluate_promotion("planner", "v1", strong)
    print(f"Promotion on strong data: should_promote={rec2.should_promote}  "
          f"requires_approval={rec2.requires_approval}")
    print(f"  reason: {rec2.reason}")

    # ---- STEP 7: derived analytics (12.2/12.8) -----------------------------
    line("STEP 7 — Performance stats (12.2) — what the dashboard shows")
    # add a couple more runs so stats are interesting
    for i in range(2, 5):
        await run_workflow(router, request, project_id=f"demo-run-{i}",
                           evaluation_store=evals, selection_strategy=selector)
    stats = aggregate(evals.all())
    print(f"runs={stats.runs}  success_rate={stats.success_rate}  "
          f"mean_score={stats.mean_score}  avg_time={stats.avg_time_s}s")

    # ---- STEP 8: workflow optimization hint (12.9) -------------------------
    line("STEP 8 — Workflow optimization (12.9): advisory only")
    suggestions = suggest_skips("backend", evals.all() * 10, ["research"])  # inflate sample
    if suggestions:
        print(f"Suggestion: {suggestions[0].suggestion}")
        print(f"  requires_approval={suggestions[0].requires_approval} (graph never auto-edited)")

    # ---- STEP 9: PR-outcome learning seam (12.9/§10) -----------------------
    line("STEP 9 — PR-outcome learning (12.9): merge/close → labeled signal")
    print(f"PR merged  → pr_accepted signal = {outcome_to_signal(PROutcome.MERGED)}")
    print(f"PR closed  → pr_accepted signal = {outcome_to_signal(PROutcome.CLOSED)}")
    print("  (the signal is stored on the Evaluation; acting on it is deferred)")

    # ---- STEP 10: marketplace (12.10) --------------------------------------
    line("STEP 10 — Agent marketplace (12.10): register → approve → discover")
    market = MarketplaceRegistry()
    market.register(AgentDescriptor(
        name="security-scanner", role="review",
        description="Scans diffs for vulns", entrypoint="acme.sec:SecAgent"))
    print(f"Registered (PENDING, no code run). Discoverable now? {market.discover()}")
    market.approve("security-scanner")
    print(f"After approval, discoverable: {[d.name for d in market.discover()]}")
    from agents.planner import PlannerAgent
    check_agent_contract(PlannerAgent)
    print("Contract check on a real agent (PlannerAgent): PASSED")

    line("DONE — static pipeline → self-improving system, end to end")


if __name__ == "__main__":
    asyncio.run(main())
