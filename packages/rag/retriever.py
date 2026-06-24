"""Semantic retriever — embed a query, search the vector store, optionally cache.

Searches by *meaning*, not filename: "Where do we validate JWT?" embeds to a
vector close to the chunk containing ``verify_token()``. Repeated queries can be
served from a cache (Redis in prod, in-memory in tests) to avoid re-hitting the
vector store.
"""

from __future__ import annotations

from rag.cache import Cache, NullCache
from rag.embeddings import Embedder
from rag.vector_store import SearchHit, VectorStore


class Retriever:
    """Embed → (cache?) → vector search → ranked hits."""

    def __init__(
        self,
        embedder: Embedder,
        store: VectorStore,
        cache: Cache | None = None,
        cache_ttl: int = 300,
    ):
        self.embedder = embedder
        self.store = store
        self.cache = cache or NullCache()
        self.cache_ttl = cache_ttl

    async def retrieve(self, query: str, limit: int = 5) -> list[SearchHit]:
        """Return the most relevant chunks for a query."""
        cache_key = f"retr:{limit}:{query}"
        cached = await self.cache.get(cache_key)
        if cached is not None:
            return [SearchHit.model_validate(h) for h in cached]

        vector = await self.embedder.embed(query)
        hits = await self.store.search(vector, limit=limit)
        await self.cache.set(
            cache_key, [h.model_dump() for h in hits], ttl=self.cache_ttl
        )
        return hits
