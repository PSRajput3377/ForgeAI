"""Connector contracts — the uniform interface every external system implements.

Every integration (GitHub, Jira, Slack, Notion, …) is a ``Connector`` exposing
``read``/``write`` over ``ExternalObject``s. One interface means the Integration
Hub, knowledge layer, and agents treat all systems alike, and any connector is
replaceable. Offline ``Fake*`` connectors back the whole suite (ADR-0021).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import StrEnum

from pydantic import BaseModel, Field


class System(StrEnum):
    """The external systems ForgeAI integrates with."""

    GITHUB = "github"
    JIRA = "jira"
    SLACK = "slack"
    NOTION = "notion"
    CONFLUENCE = "confluence"
    EMAIL = "email"
    CALENDAR = "calendar"
    FIGMA = "figma"


class Capability(StrEnum):
    """What a connector can do (used for permissioning)."""

    READ = "read"
    WRITE = "write"


class ExternalObject(BaseModel):
    """A normalized item from any external system.

    ``ref`` is a stable cross-system id (e.g. ``jira:JIRA-142``,
    ``github:pr/91``) used by the knowledge graph and search.
    """

    system: System
    kind: str  # issue | message | page | pr | event | email | design ...
    ref: str
    title: str = ""
    body: str = ""
    url: str = ""
    metadata: dict = Field(default_factory=dict)


class Connector(ABC):
    """Interface every external-system connector implements."""

    system: System
    capabilities: set[Capability] = {Capability.READ}
    # Honesty (Phase 13.6): "simulated" = interface-complete, validated against an
    # in-memory fake; "live" = talks to the real external system. The default is
    # deliberately "simulated" so a connector never *overstates* its readiness.
    mode: str = "simulated"

    @abstractmethod
    async def search(self, query: str, limit: int = 10) -> list[ExternalObject]:
        """Return objects matching a query (read)."""

    @abstractmethod
    async def get(self, ref: str) -> ExternalObject | None:
        """Fetch a single object by its ref (read)."""

    async def create(self, kind: str, **fields) -> ExternalObject:
        """Create an object (write). Override in writable connectors."""
        raise NotImplementedError(f"{self.system} connector is read-only")

    async def update(self, ref: str, **fields) -> ExternalObject:
        """Update an object (write). Override in writable connectors."""
        raise NotImplementedError(f"{self.system} connector is read-only")

    def can(self, capability: Capability) -> bool:
        return capability in self.capabilities
