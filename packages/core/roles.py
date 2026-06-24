"""The canonical roster of agent roles.

One enum so the Manager, the workflow graph, and the prompt registry all refer
to agents by the same names. Adding a role here (e.g. SECURITY) is the first
step to adding a new specialist — see ADR-0001/0002.
"""

from enum import StrEnum


class AgentRole(StrEnum):
    """Every specialist in the AI organization."""

    MANAGER = "manager"
    PLANNER = "planner"
    RESEARCHER = "researcher"
    MEMORY = "memory"
    CODER = "coder"
    EXECUTION = "execution"
    TESTING = "testing"
    REVIEW = "review"
    REFLECTION = "reflection"
    GIT = "git"
