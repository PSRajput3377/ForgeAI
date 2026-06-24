"""In-memory connectors for every external system.

These are deterministic, offline implementations of the Connector interface —
they back the entire integration suite in tests and local dev. Production
connectors (httpx against each vendor API) implement the same interface and drop
in behind the Integration Hub without touching agents (ADR-0021).

Writable systems (Jira/Slack/Notion/Email/Confluence) expose WRITE; read-only
systems (Confluence search, Calendar, Figma) expose READ only by default.
"""

from __future__ import annotations

from integrations.base import Capability, Connector, ExternalObject, System


class _InMemoryConnector(Connector):
    """Shared in-memory store keyed by ref, with substring search."""

    def __init__(self) -> None:
        self._objects: dict[str, ExternalObject] = {}

    def seed(self, obj: ExternalObject) -> ExternalObject:
        self._objects[obj.ref] = obj
        return obj

    async def search(self, query: str, limit: int = 10) -> list[ExternalObject]:
        # Token-based: match if any query word appears in title/body (closer to
        # real search than a single-substring match).
        words = [w for w in query.lower().split() if w]
        hits = [
            o
            for o in self._objects.values()
            if any(w in o.title.lower() or w in o.body.lower() for w in words)
        ]
        return hits[:limit]

    async def get(self, ref: str) -> ExternalObject | None:
        return self._objects.get(ref)


class FakeGitHubConnector(_InMemoryConnector):
    system = System.GITHUB
    capabilities = {Capability.READ, Capability.WRITE}


class FakeJiraConnector(_InMemoryConnector):
    system = System.JIRA
    capabilities = {Capability.READ, Capability.WRITE}

    _counter = 0

    async def create(self, kind: str, *, title: str, body: str = "", **fields) -> ExternalObject:
        self._counter += 1
        key = f"JIRA-{100 + self._counter}"
        return self.seed(
            ExternalObject(
                system=System.JIRA,
                kind=kind,
                ref=f"jira:{key}",
                title=title,
                body=body,
                metadata={"key": key, "status": "open", **fields},
            )
        )

    async def update(self, ref: str, **fields) -> ExternalObject:
        obj = self._objects[ref]
        obj.metadata.update(fields)
        return obj


class FakeSlackConnector(_InMemoryConnector):
    system = System.SLACK
    capabilities = {Capability.READ, Capability.WRITE}

    async def create(
        self, kind: str, *, body: str, channel: str = "#general", **fields
    ) -> ExternalObject:
        ref = f"slack:{channel}:{len(self._objects) + 1}"
        return self.seed(
            ExternalObject(
                system=System.SLACK,
                kind="message",
                ref=ref,
                body=body,
                metadata={"channel": channel, **fields},
            )
        )


class FakeNotionConnector(_InMemoryConnector):
    system = System.NOTION
    capabilities = {Capability.READ, Capability.WRITE}

    async def create(self, kind: str, *, title: str, body: str = "", **fields) -> ExternalObject:
        ref = f"notion:{title.lower().replace(' ', '-')}"
        return self.seed(
            ExternalObject(
                system=System.NOTION,
                kind="page",
                ref=ref,
                title=title,
                body=body,
                metadata=fields,
            )
        )

    async def update(self, ref: str, *, body: str | None = None, **fields) -> ExternalObject:
        obj = self._objects[ref]
        if body is not None:
            obj.body = body
        obj.metadata.update(fields)
        return obj


class FakeConfluenceConnector(_InMemoryConnector):
    system = System.CONFLUENCE
    capabilities = {Capability.READ}


class FakeEmailConnector(_InMemoryConnector):
    system = System.EMAIL
    capabilities = {Capability.WRITE}

    sent: list[ExternalObject]

    def __init__(self) -> None:
        super().__init__()
        self.sent = []

    async def search(self, query: str, limit: int = 10):
        return []  # email is send-only here

    async def get(self, ref: str):
        return None

    async def create(
        self, kind: str, *, to: str, subject: str, body: str = "", **fields
    ) -> ExternalObject:
        obj = ExternalObject(
            system=System.EMAIL,
            kind="email",
            ref=f"email:{len(self.sent) + 1}",
            title=subject,
            body=body,
            metadata={"to": to, **fields},
        )
        self.sent.append(obj)
        return obj


class FakeCalendarConnector(_InMemoryConnector):
    system = System.CALENDAR
    capabilities = {Capability.READ}


class FakeFigmaConnector(_InMemoryConnector):
    system = System.FIGMA
    capabilities = {Capability.READ}  # read-only initially
