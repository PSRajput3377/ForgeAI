"""Tests for the Integration Hub: permissions, approval rules, cross-system search."""

import pytest
from integrations.base import Capability, System
from integrations.connectors import (
    FakeConfluenceConnector,
    FakeEmailConnector,
    FakeGitHubConnector,
    FakeJiraConnector,
    FakeNotionConnector,
    FakeSlackConnector,
)
from integrations.hub import ApprovalDenied, IntegrationHub, PermissionError_
from integrations.security import ApprovalRules, ConnectorPermissions


def build_hub(approver=None, approval_rules=None):
    hub = IntegrationHub(approval_rules=approval_rules, approver=approver)
    hub.register(FakeGitHubConnector())
    hub.register(FakeJiraConnector())
    hub.register(FakeSlackConnector())
    hub.register(FakeNotionConnector())
    hub.register(FakeConfluenceConnector())
    hub.register(FakeEmailConnector())
    return hub


@pytest.mark.asyncio
async def test_register_and_list_systems():
    hub = build_hub()
    assert System.JIRA in hub.systems()
    assert len(hub.systems()) == 6


@pytest.mark.asyncio
async def test_permission_blocks_unauthorized_agent():
    perms = ConnectorPermissions()
    perms.grant("notification", System.SLACK, Capability.WRITE)
    hub = IntegrationHub(
        permissions=perms, approval_rules=ApprovalRules(required=set())
    )
    hub.register(FakeSlackConnector())

    # Authorized agent can post.
    msg = await hub.write(System.SLACK, "message", agent="notification", body="hi")
    assert msg.body == "hi"

    # Unauthorized agent is blocked.
    with pytest.raises(PermissionError_):
        await hub.write(System.SLACK, "message", agent="research", body="nope")


@pytest.mark.asyncio
async def test_read_only_system_rejects_write():
    hub = IntegrationHub(approval_rules=ApprovalRules(required=set()))
    hub.register(FakeConfluenceConnector())
    with pytest.raises(PermissionError_):
        await hub.write(System.CONFLUENCE, "page", title="x")


@pytest.mark.asyncio
async def test_approval_required_blocks_without_approval():
    # Default rules require approval for Jira issue creation.
    hub = build_hub(approver=None)  # default approver denies
    with pytest.raises(ApprovalDenied):
        await hub.write(System.JIRA, "issue", title="Missing validation bug")


@pytest.mark.asyncio
async def test_approval_granted_allows_write():
    async def approve_all(system, kind, fields):
        return True

    hub = build_hub(approver=approve_all)
    issue = await hub.write(System.JIRA, "issue", title="Missing validation bug")
    assert issue.ref.startswith("jira:JIRA-")


@pytest.mark.asyncio
async def test_non_gated_write_skips_approval():
    # Slack messages are not in the approval set → no approver needed.
    hub = build_hub(approver=None)
    msg = await hub.write(System.SLACK, "message", body="build failed")
    assert "build failed" in msg.body


@pytest.mark.asyncio
async def test_cross_system_search():
    hub = build_hub()
    await hub.connector(System.JIRA).create(
        "issue", title="Add JWT auth", body="use jwt"
    )
    await hub.connector(System.NOTION).create(
        "page", title="Auth RFC", body="JWT chosen for statelessness"
    )
    await hub.connector(System.SLACK).create(
        "message", body="why jwt? because stateless"
    )

    results = await hub.search("jwt")
    systems = {r.system for r in results}
    assert {System.JIRA, System.NOTION, System.SLACK} <= systems
