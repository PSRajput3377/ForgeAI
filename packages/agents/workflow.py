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


def build_workflow(router: ModelRouter):
    """Compile and return the agent workflow graph for a given ModelRouter."""
    manager = ManagerAgent(router)
    planner = PlannerAgent(router)
    researcher = ResearcherAgent(router)
    memory = MemoryAgent(router)
    coder = CoderAgent(router)
    execution = ExecutionAgent(router)
    testing = TestingAgent(router)
    review = ReviewAgent(router)
    reflection = ReflectionAgent(router)
    git = GitAgent(router)

    graph = StateGraph(ProjectState)

    # One node per step. ``intake`` and ``final`` are the Manager's two touch
    # points (it delegates everything in between).
    graph.add_node("intake", manager.intake)
    graph.add_node("planner", planner.run)
    graph.add_node("research", researcher.run)
    graph.add_node("memory", memory.run)
    graph.add_node("coder", coder.run)
    graph.add_node("execute", execution.run)
    graph.add_node("tests", testing.run)
    graph.add_node("review", review.run)
    graph.add_node("reflection", reflection.run)
    graph.add_node("git", git.run)
    graph.add_node("final", manager.run)

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
    router: ModelRouter, user_request: str, **state_kwargs
) -> ProjectState:
    """Run the full workflow for a request and return the final ProjectState."""
    app = build_workflow(router)
    initial = ProjectState(user_request=user_request, **state_kwargs)
    result = await app.ainvoke(initial)
    # LangGraph returns the state as a dict-like; normalize back to ProjectState.
    return ProjectState.model_validate(result)
