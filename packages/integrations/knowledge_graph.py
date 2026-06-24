"""Knowledge graph — relationships across systems.

Edges connect cross-system refs (JIRA-142 → PR #91 → commit → Notion doc →
Slack thread), so ForgeAI can answer "why was X decided?" by walking the graph
and "what's related to this ticket?" across every tool.
"""

from __future__ import annotations

from pydantic import BaseModel


class Edge(BaseModel):
    source: str  # cross-system ref, e.g. "jira:JIRA-142"
    target: str  # e.g. "github:pr/91"
    relationship: str  # implements | references | discusses | documents ...


class KnowledgeGraph:
    """A small directed multigraph over external-object refs."""

    def __init__(self) -> None:
        self._edges: list[Edge] = []

    def link(self, source: str, target: str, relationship: str) -> Edge:
        edge = Edge(source=source, target=target, relationship=relationship)
        self._edges.append(edge)
        return edge

    def neighbors(self, ref: str) -> list[Edge]:
        """Edges touching ``ref`` in either direction."""
        return [e for e in self._edges if e.source == ref or e.target == ref]

    def related(self, ref: str, *, max_depth: int = 2) -> set[str]:
        """All refs reachable from ``ref`` within ``max_depth`` hops."""
        seen: set[str] = {ref}
        frontier = {ref}
        for _ in range(max_depth):
            nxt: set[str] = set()
            for node in frontier:
                for e in self.neighbors(node):
                    for other in (e.source, e.target):
                        if other not in seen:
                            seen.add(other)
                            nxt.add(other)
            frontier = nxt
            if not frontier:
                break
        return seen - {ref}
