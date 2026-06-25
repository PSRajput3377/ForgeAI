"""marketplace — register & discover third-party agents (Phase 12.10).

Users can publish specialist agents (Security, Documentation, DevOps, …) as
descriptors; ForgeAI discovers the *approved* ones dynamically. Registration is
metadata-only (no code runs on register) and approval-gated; a discoverable
agent must satisfy the agent contract (``specs/agent-spec.md``). Independent of
the learning loops — ships on its own timeline (spec §9).
"""

from marketplace.registry import MarketplaceRegistry
from marketplace.types import (
    AgentDescriptor,
    ContractError,
    RegistrationStatus,
    check_agent_contract,
)

__all__ = [
    "AgentDescriptor",
    "ContractError",
    "MarketplaceRegistry",
    "RegistrationStatus",
    "check_agent_contract",
]
