"""Agent marketplace types — descriptors + the contract check (spec §9).

Third-party agents (Security, Documentation, DevOps, …) are registered as
*descriptors* and discovered dynamically. A descriptor is metadata only —
registering one runs **no code** (spec §9: no implicit execution on
registration). Before an agent can be discovered it must (a) be approved and
(b) satisfy the agent contract (``specs/agent-spec.md``): a unique role, an
async ``run(state) -> state``, and no import of another agent.
"""

from __future__ import annotations

import inspect
from enum import StrEnum

from pydantic import BaseModel, Field


class RegistrationStatus(StrEnum):
    """Lifecycle of a marketplace registration. Approval-gated (spec §9)."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class AgentDescriptor(BaseModel):
    """Metadata describing a registerable agent. No code, no import — just facts.

    ``entrypoint`` names where the implementation lives (e.g. ``pkg.mod:Class``)
    for a later, sandboxed loader; the marketplace never imports it on register.
    """

    name: str
    role: str  # the AgentRole value the agent claims
    description: str = ""
    author: str = ""
    entrypoint: str = ""  # "module.path:ClassName" — not imported at registration
    capabilities: list[str] = Field(default_factory=list)
    status: RegistrationStatus = RegistrationStatus.PENDING


class ContractError(ValueError):
    """Raised when a candidate agent class violates the agent contract."""


def check_agent_contract(agent_cls: type) -> None:
    """Validate a candidate agent *class* against the agent contract (spec §9).

    Used when an operator chooses to load an approved descriptor's class — a
    deliberate, separate step from registration. Raises ``ContractError`` on any
    violation; returns None when the class conforms.
    """
    from agents.base import BaseAgent

    if not isinstance(agent_cls, type) or not issubclass(agent_cls, BaseAgent):
        raise ContractError("agent must subclass BaseAgent")

    role = getattr(agent_cls, "role", None)
    if role is None:
        raise ContractError("agent must define a `role`")

    run = getattr(agent_cls, "run", None)
    if run is None or not inspect.iscoroutinefunction(run):
        raise ContractError("agent must implement `async def run(self, state)`")

    sig = inspect.signature(run)
    # self + state
    if len(sig.parameters) < 2:
        raise ContractError("run() must accept (self, state)")
