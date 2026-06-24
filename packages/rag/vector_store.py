"""Vector store — persist and search embeddings.

One interface, two backends:
- ``InMemoryVectorStore`` brute-force cosine search; offline, used in tests.
- ``QdrantVectorStore``    real Qdrant (optional import); used in production.

Points are addressable by id so incremental indexing can upsert/delete the
chunks of a single file without touching the rest.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from pydantic import BaseModel, Field

from rag.embeddings import cosine_similarity


class VectorRecord(BaseModel):
    """A stored vector with its payload (text + metadata)."""

    id: str
    vector: list[float]
    text: str = ""
    metadata: dict = Field(default_factory=dict)


class SearchHit(BaseModel):
    """A retrieval result."""

    id: str
    score: float
    text: str
    metadata: dict = Field(default_factory=dict)


class VectorStore(ABC):
    """Interface for a vector database collection."""

    @abstractmethod
    async def upsert(self, records: list[VectorRecord]) -> None: ...

    @abstractmethod
    async def search(self, vector: list[float], limit: int = 5) -> list[SearchHit]: ...

    @abstractmethod
    async def delete_by_filter(self, **equals: str) -> int:
        """Delete all records whose metadata matches the given equalities."""

    @abstractmethod
    async def count(self) -> int: ...


class InMemoryVectorStore(VectorStore):
    """Brute-force cosine-similarity store. Deterministic; no dependencies."""

    def __init__(self) -> None:
        self._records: dict[str, VectorRecord] = {}

    async def upsert(self, records: list[VectorRecord]) -> None:
        for r in records:
            self._records[r.id] = r

    async def search(self, vector: list[float], limit: int = 5) -> list[SearchHit]:
        scored = [
            SearchHit(
                id=r.id,
                score=cosine_similarity(vector, r.vector),
                text=r.text,
                metadata=r.metadata,
            )
            for r in self._records.values()
        ]
        scored.sort(key=lambda h: h.score, reverse=True)
        return scored[:limit]

    async def delete_by_filter(self, **equals: str) -> int:
        to_delete = [
            rid
            for rid, r in self._records.items()
            if all(r.metadata.get(k) == v for k, v in equals.items())
        ]
        for rid in to_delete:
            del self._records[rid]
        return len(to_delete)

    async def count(self) -> int:
        return len(self._records)


class QdrantVectorStore(VectorStore):
    """Qdrant-backed store. Imports the client lazily so the package works
    without qdrant installed (tests use the in-memory store)."""

    def __init__(self, url: str, collection: str, dim: int):
        self.url = url
        self.collection = collection
        self.dim = dim
        self._client = None

    def _ensure_client(self):
        if self._client is None:
            from qdrant_client import QdrantClient  # lazy import
            from qdrant_client.models import Distance, VectorParams

            self._client = QdrantClient(url=self.url)
            existing = {c.name for c in self._client.get_collections().collections}
            if self.collection not in existing:
                self._client.create_collection(
                    self.collection,
                    vectors_config=VectorParams(size=self.dim, distance=Distance.COSINE),
                )
        return self._client

    async def upsert(self, records: list[VectorRecord]) -> None:
        from qdrant_client.models import PointStruct

        client = self._ensure_client()
        points = [
            PointStruct(id=r.id, vector=r.vector, payload={"text": r.text, **r.metadata})
            for r in records
        ]
        client.upsert(self.collection, points=points)

    async def search(self, vector: list[float], limit: int = 5) -> list[SearchHit]:
        client = self._ensure_client()
        results = client.search(self.collection, query_vector=vector, limit=limit)
        hits = []
        for p in results:
            payload = dict(p.payload or {})
            text = payload.pop("text", "")
            hits.append(SearchHit(id=str(p.id), score=p.score, text=text, metadata=payload))
        return hits

    async def delete_by_filter(self, **equals: str) -> int:
        from qdrant_client.models import FieldCondition, Filter, MatchValue

        client = self._ensure_client()
        conditions = [FieldCondition(key=k, match=MatchValue(value=v)) for k, v in equals.items()]
        client.delete(self.collection, points_selector=Filter(must=conditions))
        return 0  # Qdrant delete is fire-and-forget; count not returned

    async def count(self) -> int:
        client = self._ensure_client()
        return client.count(self.collection).count
