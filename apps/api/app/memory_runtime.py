"""Wiring between the FastAPI app and the Memory + RAG subsystem.

Builds production backends (Ollama embeddings, Qdrant vector store, Redis cache)
from settings. The packages themselves remain backend-agnostic and fully
testable offline (InMemory* / Hashing*); this module just selects the real
implementations. (ADR-0015)
"""

from __future__ import annotations

from memory.context_builder import ContextBuilder
from memory.manager import MemoryManager
from memory.store import InMemoryStore
from rag.cache import RedisCache
from rag.embeddings import OllamaEmbedder
from rag.retriever import Retriever
from rag.vector_store import QdrantVectorStore

from app.agents_runtime import build_router
from app.config import settings

# nomic-embed-text dimensionality.
EMBED_DIM = 768


def build_embedder() -> OllamaEmbedder:
    """Real embeddings via the Model Router (Ollama nomic-embed-text)."""
    return OllamaEmbedder(build_router(), dim=EMBED_DIM)


def build_vector_store(collection: str = "forge_project") -> QdrantVectorStore:
    return QdrantVectorStore(url=settings.qdrant_url, collection=collection, dim=EMBED_DIM)


def build_cache() -> RedisCache:
    return RedisCache(url=settings.redis_url)


def build_retriever(collection: str = "forge_project") -> Retriever:
    """Assemble the production retriever (Ollama + Qdrant + Redis cache)."""
    return Retriever(build_embedder(), build_vector_store(collection), cache=build_cache())


def build_context_builder(collection: str = "forge_project") -> ContextBuilder:
    """A ContextBuilder backed by in-process memory + the production retriever.

    NOTE: MemoryManager uses InMemoryStore here; the durable PostgreSQL store
    lands in the Database phase and drops in behind the same interface.
    """
    memory = MemoryManager(InMemoryStore())
    return ContextBuilder(memory, retriever=build_retriever(collection))
