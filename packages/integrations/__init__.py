"""integrations — enterprise integrations & external tool ecosystem.

ForgeAI operates across the whole engineering org (GitHub, Jira, Slack, Notion,
Confluence, Email, Calendar, Figma), not just code. Every system is a
``Connector`` behind one ``IntegrationHub`` that enforces permissions + approval
rules, runs cross-system search, and feeds a ``KnowledgeGraph``.

Offline by default: in-memory Fake* connectors back the whole suite; production
connectors (httpx per vendor) implement the same interface (ADR-0021).
"""

from integrations.base import Capability, Connector, ExternalObject, System
from integrations.connectors import (
    FakeCalendarConnector,
    FakeConfluenceConnector,
    FakeEmailConnector,
    FakeFigmaConnector,
    FakeGitHubConnector,
    FakeJiraConnector,
    FakeNotionConnector,
    FakeSlackConnector,
)
from integrations.hub import (
    ApprovalDenied,
    IntegrationHub,
    PermissionError_,
)
from integrations.knowledge_graph import Edge, KnowledgeGraph
from integrations.security import ApprovalRules, ConnectorPermissions, SecretStore


def build_default_hub() -> IntegrationHub:
    """An IntegrationHub with every connector registered.

    Ships the in-memory Fake* connectors (mode='simulated'). Live connectors
    register the same way once implemented (ADR-0021) — the hub's status()
    then reports them as 'live'.
    """
    hub = IntegrationHub()
    for connector_cls in (
        FakeGitHubConnector,
        FakeJiraConnector,
        FakeSlackConnector,
        FakeNotionConnector,
        FakeConfluenceConnector,
        FakeEmailConnector,
        FakeCalendarConnector,
        FakeFigmaConnector,
    ):
        hub.register(connector_cls())
    return hub


__all__ = [
    "build_default_hub",
    "ApprovalDenied",
    "ApprovalRules",
    "Capability",
    "Connector",
    "ConnectorPermissions",
    "Edge",
    "ExternalObject",
    "FakeCalendarConnector",
    "FakeConfluenceConnector",
    "FakeEmailConnector",
    "FakeFigmaConnector",
    "FakeGitHubConnector",
    "FakeJiraConnector",
    "FakeNotionConnector",
    "FakeSlackConnector",
    "IntegrationHub",
    "KnowledgeGraph",
    "PermissionError_",
    "SecretStore",
    "System",
]
