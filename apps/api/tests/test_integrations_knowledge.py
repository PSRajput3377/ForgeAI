"""Knowledge graph, cross-system 'why' answers, and secret encryption."""

import pytest
from integrations.base import System
from integrations.connectors import (
    FakeNotionConnector,
    FakeSlackConnector,
)
from integrations.hub import IntegrationHub
from integrations.knowledge_graph import KnowledgeGraph
from integrations.security import ApprovalRules, SecretStore


def test_knowledge_graph_links_and_neighbors():
    g = KnowledgeGraph()
    g.link("jira:JIRA-142", "github:pr/91", "implements")
    g.link("github:pr/91", "notion:auth-rfc", "documents")
    g.link("github:pr/91", "slack:t1", "discusses")

    neighbors = g.neighbors("github:pr/91")
    assert len(neighbors) == 3


def test_knowledge_graph_multi_hop_related():
    g = KnowledgeGraph()
    g.link("jira:JIRA-142", "github:pr/91", "implements")
    g.link("github:pr/91", "notion:auth-rfc", "documents")
    # From the Jira ticket, the RFC is reachable in 2 hops.
    related = g.related("jira:JIRA-142", max_depth=2)
    assert "github:pr/91" in related
    assert "notion:auth-rfc" in related


@pytest.mark.asyncio
async def test_cross_system_answer_gathers_evidence_and_related():
    hub = IntegrationHub(approval_rules=ApprovalRules(required=set()))
    hub.register(FakeNotionConnector())
    hub.register(FakeSlackConnector())
    await hub.connector(System.NOTION).create(
        "page", title="Auth RFC", body="JWT chosen because stateless"
    )
    await hub.connector(System.SLACK).create(
        "message", body="we picked jwt for statelessness"
    )
    hub.graph.link("notion:auth-rfc", "jira:JIRA-142", "references")

    answer = await hub.answer("why jwt")
    assert answer["question"] == "why jwt"
    assert len(answer["evidence"]) >= 2  # found in Notion + Slack
    systems = {e["system"] for e in answer["evidence"]}
    assert System.NOTION in systems and System.SLACK in systems


def test_secret_store_encrypts_at_rest():
    store = SecretStore("app-secret-key")
    store.put("jira_token", "super-secret-token")
    # Round-trips correctly...
    assert store.get("jira_token") == "super-secret-token"
    # ...but the stored blob is encrypted, not plaintext.
    assert store._store["jira_token"] != b"super-secret-token"
    assert store.is_encrypted("jira_token")


def test_secret_store_missing_returns_none():
    store = SecretStore("k")
    assert store.get("nope") is None
