"""Integration Hub — the single layer every external system connects through.

Agents never touch a vendor SDK directly; they go through the hub, which:
- registers connectors by ``System``,
- enforces per-agent connector permissions,
- gates write actions behind approval rules,
- runs cross-system search and powers the knowledge graph.

Mirrors the Tool Manager (Phase 3) and Model Router (Phase 2) patterns.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from integrations.base import Capability, Connector, ExternalObject, System
from integrations.knowledge_graph import KnowledgeGraph
from integrations.security import ApprovalRules, ConnectorPermissions

# An approver decides whether a gated write proceeds.
Approver = Callable[[System, str, dict], Awaitable[bool]]


async def _deny(system, kind, details) -> bool:
    return False


class PermissionError_(PermissionError):
    """Raised when an agent lacks a connector capability."""


class ApprovalDenied(RuntimeError):
    """Raised when a write requiring approval is not approved."""


class IntegrationHub:
    """Registry + policy enforcement for all external systems."""

    def __init__(
        self,
        permissions: ConnectorPermissions | None = None,
        approval_rules: ApprovalRules | None = None,
        approver: Approver | None = None,
    ):
        self._connectors: dict[System, Connector] = {}
        self.permissions = permissions or ConnectorPermissions()
        self.approval_rules = approval_rules or ApprovalRules()
        self.approver = approver or _deny
        self.graph = KnowledgeGraph()

    def register(self, connector: Connector) -> None:
        self._connectors[connector.system] = connector

    def connector(self, system: System) -> Connector | None:
        return self._connectors.get(system)

    def systems(self) -> list[System]:
        return sorted(self._connectors)

    def status(self) -> list[dict]:
        """Honest per-connector status (Phase 13.6): system, mode (simulated /
        live), and capabilities — so the UI never overstates readiness."""
        return [
            {
                "system": c.system.value if hasattr(c.system, "value") else str(c.system),
                "mode": getattr(c, "mode", "simulated"),
                "capabilities": sorted(
                    cap.value if hasattr(cap, "value") else str(cap) for cap in c.capabilities
                ),
            }
            for c in (self._connectors[s] for s in self.systems())
        ]

    def _check_permission(self, agent: str, system: System, cap: Capability) -> None:
        if agent is None:
            return  # system-level/internal calls bypass per-agent checks
        if not self.permissions.allows(agent, system, cap):
            raise PermissionError_(f"{agent} lacks {cap} on {system}")

    async def read(
        self, system: System, ref: str, *, agent: str | None = None
    ) -> ExternalObject | None:
        self._check_permission(agent, system, Capability.READ)
        connector = self._connectors[system]
        return await connector.get(ref)

    async def write(
        self, system: System, kind: str, *, agent: str | None = None, **fields
    ) -> ExternalObject:
        """Create an object, enforcing permission + approval rules."""
        self._check_permission(agent, system, Capability.WRITE)
        connector = self._connectors[system]
        if not connector.can(Capability.WRITE):
            raise PermissionError_(f"{system} connector is read-only")
        if self.approval_rules.requires_approval(system, kind):
            if not await self.approver(system, kind, fields):
                raise ApprovalDenied(f"Write to {system}:{kind} was not approved")
        return await connector.create(kind, **fields)

    async def search(
        self, query: str, *, systems: list[System] | None = None, limit_per: int = 5
    ) -> list[ExternalObject]:
        """Cross-system search — query every (or selected) connected system."""
        targets = systems or self.systems()
        results: list[ExternalObject] = []
        for system in targets:
            connector = self._connectors.get(system)
            if connector is None or not connector.can(Capability.READ):
                continue
            results.extend(await connector.search(query, limit=limit_per))
        return results

    async def answer(self, question: str) -> dict:
        """Cross-system retrieval: gather evidence for a question (e.g. 'Why JWT?')
        from every connected system, plus graph-related refs."""
        hits = await self.search(question)
        related: set[str] = set()
        for h in hits:
            related |= self.graph.related(h.ref)
        return {
            "question": question,
            "evidence": [{"system": h.system, "ref": h.ref, "title": h.title} for h in hits],
            "related_refs": sorted(related),
        }
