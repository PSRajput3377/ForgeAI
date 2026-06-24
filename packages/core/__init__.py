"""core — shared types and contracts for the ForgeAI agent system.

Everything the agents share lives here so no package depends on another's
internals:

- ``ProjectState``  the single state object every agent reads from / writes to.
- ``messages``      structured agent-to-agent message contracts.
- ``AgentRole``     the canonical roster of agent roles.
"""

from core.messages import AgentMessage, MessageStatus, TaskSpec
from core.roles import AgentRole
from core.state import ProjectState, ReviewVerdict

__all__ = [
    "AgentMessage",
    "AgentRole",
    "MessageStatus",
    "ProjectState",
    "ReviewVerdict",
    "TaskSpec",
]
