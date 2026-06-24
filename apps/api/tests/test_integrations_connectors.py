"""Tests for the connector interface and the in-memory connectors."""

import pytest
from integrations.base import Capability, ExternalObject, System
from integrations.connectors import (
    FakeConfluenceConnector,
    FakeEmailConnector,
    FakeJiraConnector,
    FakeNotionConnector,
    FakeSlackConnector,
)


@pytest.mark.asyncio
async def test_jira_create_read_update():
    jira = FakeJiraConnector()
    issue = await jira.create("issue", title="Add Authentication", body="JWT please")
    assert issue.ref.startswith("jira:JIRA-")
    assert issue.metadata["status"] == "open"

    fetched = await jira.get(issue.ref)
    assert fetched.title == "Add Authentication"

    await jira.update(issue.ref, status="in_progress")
    assert (await jira.get(issue.ref)).metadata["status"] == "in_progress"


@pytest.mark.asyncio
async def test_slack_post_message():
    slack = FakeSlackConnector()
    msg = await slack.create("message", body="Build failed on PR #42", channel="#ci")
    assert msg.metadata["channel"] == "#ci"
    assert "Build failed" in msg.body


@pytest.mark.asyncio
async def test_notion_write_then_search():
    notion = FakeNotionConnector()
    await notion.create("page", title="Auth Design", body="We use JWT because it is stateless")
    hits = await notion.search("jwt")
    assert len(hits) == 1 and hits[0].title == "Auth Design"


@pytest.mark.asyncio
async def test_email_is_send_only():
    email = FakeEmailConnector()
    sent = await email.create("email", to="dev@x.com", subject="Task done", body="JWT shipped")
    assert email.sent == [sent]
    assert await email.search("anything") == []


@pytest.mark.asyncio
async def test_confluence_is_read_only():
    conf = FakeConfluenceConnector()
    assert conf.can(Capability.READ)
    assert not conf.can(Capability.WRITE)
    with pytest.raises(NotImplementedError):
        await conf.create("page", title="x")


@pytest.mark.asyncio
async def test_search_matches_title_and_body():
    notion = FakeNotionConnector()
    notion.seed(
        ExternalObject(
            system=System.NOTION,
            kind="page",
            ref="notion:a",
            title="RFC",
            body="choose postgres",
        )
    )
    assert len(await notion.search("postgres")) == 1
    assert len(await notion.search("RFC")) == 1
    assert len(await notion.search("kubernetes")) == 0
