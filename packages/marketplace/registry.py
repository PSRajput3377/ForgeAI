"""Agent marketplace registry — register, approve, discover (spec §9).

Registration records a descriptor in the PENDING state — it runs no code and
imports nothing. An operator then approves (or rejects) it; only APPROVED agents
are discoverable. This mirrors the platform's approval-gated philosophy: nothing
third-party becomes active without an explicit human decision.

In-memory store now (offline-testable); a durable counterpart can sit behind the
same shape later, like the rest of Phase 12.
"""

from __future__ import annotations

from marketplace.types import AgentDescriptor, RegistrationStatus


class MarketplaceRegistry:
    """Permissioned registry of third-party agent descriptors."""

    def __init__(self) -> None:
        self._agents: dict[str, AgentDescriptor] = {}

    def register(self, descriptor: AgentDescriptor) -> AgentDescriptor:
        """Record a descriptor as PENDING. Runs no code; imports nothing.

        Re-registering an existing name is rejected — names are unique so an
        approved agent can't be silently replaced by an unapproved one.
        """
        if descriptor.name in self._agents:
            raise ValueError(f"agent '{descriptor.name}' is already registered")
        descriptor.status = RegistrationStatus.PENDING
        self._agents[descriptor.name] = descriptor
        return descriptor

    def approve(self, name: str) -> AgentDescriptor:
        """Approve a pending registration (the human gate). Raises if unknown."""
        descriptor = self._require(name)
        descriptor.status = RegistrationStatus.APPROVED
        return descriptor

    def reject(self, name: str) -> AgentDescriptor:
        descriptor = self._require(name)
        descriptor.status = RegistrationStatus.REJECTED
        return descriptor

    def get(self, name: str) -> AgentDescriptor | None:
        return self._agents.get(name)

    def pending(self) -> list[AgentDescriptor]:
        return [a for a in self._agents.values() if a.status is RegistrationStatus.PENDING]

    def discover(self) -> list[AgentDescriptor]:
        """List discoverable agents — APPROVED only (spec §9)."""
        return [a for a in self._agents.values() if a.status is RegistrationStatus.APPROVED]

    def all(self) -> list[AgentDescriptor]:
        return list(self._agents.values())

    def _require(self, name: str) -> AgentDescriptor:
        descriptor = self._agents.get(name)
        if descriptor is None:
            raise KeyError(f"no agent '{name}'")
        return descriptor
