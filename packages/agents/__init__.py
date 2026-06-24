"""agents — the specialist AI agents that make up the organization.

Each agent has a single responsibility (ADR-0001), depends only on the shared
``core`` contracts and the ``ModelRouter`` (never on another agent), and is
unit-testable in isolation.

Phase 2 ships every agent as a runnable skeleton: real role, prompt, router
wiring, and structured I/O, with deterministic placeholder logic where full
LLM intelligence lands in later phases.
"""

from agents.base import BaseAgent
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

__all__ = [
    "BaseAgent",
    "CoderAgent",
    "ExecutionAgent",
    "GitAgent",
    "ManagerAgent",
    "MemoryAgent",
    "PlannerAgent",
    "ReflectionAgent",
    "ResearcherAgent",
    "ReviewAgent",
    "TestingAgent",
]
