"""LangGraph workflow — the explicit orchestration of the AI organization.

The graph makes the execution order, branching, and retries explicit:

    START → manager(intake) → planner → research → memory → coder
          → execute → tests → review → [reflection needed?]
                                          │yes → reflection → coder (retry)
                                          │no  → git → manager(final) → END

Every node reads from and writes to one shared ``ProjectState``. No agent calls
another directly — the graph is the only thing that sequences them, which keeps
agents loosely coupled (ADR-0001).
"""

from __future__ import annotations

import asyncio

from core.state import ProjectState, ReviewVerdict
from langgraph.graph import END, START, StateGraph
from models.router import ModelRouter

from agents.coder import CoderAgent
from agents.execution import ExecutionAgent
from agents.git import GitAgent
from agents.manager import ManagerAgent
from agents.memory import MemoryAgent
from agents.planner import PlannerAgent
from agents.reflection import ReflectionAgent
from agents.researcher import ResearcherAgent
from agents.review import ReviewAgent
from agents.testing import TestingAgent


def _after_review(state: ProjectState) -> str:
    """Conditional edge: decide whether to reflect-and-retry or finish."""
    if state.review_verdict == ReviewVerdict.APPROVED:
        return "git"
    if state.retry_count < state.max_retries:
        return "reflection"
    return "git"  # give up gracefully; Manager reports the non-approval


def _instrument(node_name: str, fn, bus):
    """Wrap an agent node so it emits agent.started/completed/failed events.

    No-op wrapper when ``bus`` is None, so the offline default workflow is
    unchanged. Timing is measured per node for the metrics dashboard.
    """
    if bus is None:
        return fn

    from observability.events import EventType

    async def wrapped(state):
        loop = asyncio.get_event_loop()
        start = loop.time()
        await bus.emit(EventType.AGENT_STARTED, agent=node_name, run_id=state.project_id)
        try:
            result = await fn(state)
        except Exception:
            await bus.emit(EventType.AGENT_FAILED, agent=node_name, run_id=state.project_id)
            raise
        await bus.emit(
            EventType.AGENT_COMPLETED,
            agent=node_name,
            run_id=state.project_id,
            payload={"duration": loop.time() - start},
        )
        return result

    return wrapped


def build_workflow(
    router: ModelRouter,
    context_builder=None,
    engine_factory=None,
    bus=None,
    github_workflow=None,
    github_repo=None,
):
    """Compile and return the agent workflow graph for a given ModelRouter.

    If ``context_builder`` is provided (Phase 4 Memory + RAG), the Memory agent
    uses it to assemble scored memories + RAG hits; otherwise it falls back to
    lightweight behavior so the graph still runs offline.

    If ``engine_factory`` is provided (Phase 5), the Execution agent runs the
    real build/test loop in a sandbox; otherwise it simulates execution.

    If ``bus`` is provided (Phase 6), each node emits lifecycle events for the
    timeline, metrics, and live WebSocket updates.

    If ``github_workflow`` + ``github_repo`` are provided (Phase 8.2), the Git
    agent proposes a gated PR (opens an approval request, writes nothing);
    otherwise it only drafts a commit message.
    """
    manager = ManagerAgent(router)
    planner = PlannerAgent(router)
    researcher = ResearcherAgent(router)
    memory = MemoryAgent(router, context_builder=context_builder)
    coder = CoderAgent(router)
    execution = ExecutionAgent(router, engine_factory=engine_factory)
    testing = TestingAgent(router)
    review = ReviewAgent(router)
    reflection = ReflectionAgent(router)
    git = GitAgent(router, workflow=github_workflow, repo=github_repo)

    graph = StateGraph(ProjectState)

    # One node per step. ``intake`` and ``final`` are the Manager's two touch
    # points (it delegates everything in between).
    graph.add_node("intake", _instrument("intake", manager.intake, bus))
    graph.add_node("planner", _instrument("planner", planner.run, bus))
    graph.add_node("research", _instrument("research", researcher.run, bus))
    graph.add_node("memory", _instrument("memory", memory.run, bus))
    graph.add_node("coder", _instrument("coder", coder.run, bus))
    graph.add_node("execute", _instrument("execute", execution.run, bus))
    graph.add_node("tests", _instrument("tests", testing.run, bus))
    graph.add_node("review", _instrument("review", review.run, bus))
    graph.add_node("reflection", _instrument("reflection", reflection.run, bus))
    graph.add_node("git", _instrument("git", git.run, bus))
    graph.add_node("final", _instrument("final", manager.run, bus))

    graph.add_edge(START, "intake")
    graph.add_edge("intake", "planner")
    graph.add_edge("planner", "research")
    graph.add_edge("research", "memory")
    graph.add_edge("memory", "coder")
    graph.add_edge("coder", "execute")
    graph.add_edge("execute", "tests")
    graph.add_edge("tests", "review")
    graph.add_conditional_edges(
        "review",
        _after_review,
        {"git": "git", "reflection": "reflection"},
    )
    graph.add_edge("reflection", "coder")  # retry loop
    graph.add_edge("git", "final")
    graph.add_edge("final", END)

    return graph.compile()


async def run_workflow(
    router: ModelRouter,
    user_request: str,
    *,
    context_builder=None,
    engine_factory=None,
    bus=None,
    github_workflow=None,
    github_repo=None,
    **state_kwargs,
) -> ProjectState:
    """Run the full workflow for a request and return the final ProjectState."""
    app = build_workflow(
        router,
        context_builder=context_builder,
        engine_factory=engine_factory,
        bus=bus,
        github_workflow=github_workflow,
        github_repo=github_repo,
    )
    initial = ProjectState(user_request=user_request, **state_kwargs)
    if bus is not None:
        from observability.events import EventType

        await bus.emit(
            EventType.RUN_STARTED,
            run_id=initial.project_id,
            payload={"request": user_request},
        )
    result = await app.ainvoke(initial)
    final = ProjectState.model_validate(result)
    if bus is not None:
        from observability.events import EventType

        await bus.emit(
            EventType.RUN_COMPLETED,
            run_id=final.project_id,
            payload={"success": final.review_verdict.value == "approved"},
        )
    return final
