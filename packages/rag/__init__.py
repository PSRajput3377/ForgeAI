"""rag — Retrieval-Augmented Generation: index a project, retrieve by meaning.

Pipeline:  files → chunk → embed → vector store → semantic retrieve → context.

Every component has an offline backend (HashingEmbedder, InMemoryVectorStore,
InMemoryCache) so the full pipeline runs in tests without Ollama/Qdrant/Redis,
and a real backend (Ollama/Qdrant/Redis) for production — selected by a factory
in the API. (Mirrors ADR-0003/0011.)
"""

from rag.cache import Cache, InMemoryCache, NullCache, RedisCache
from rag.chunking import Chunk, chunk_text
from rag.embeddings import (
    Embedder,
    HashingEmbedder,
    OllamaEmbedder,
    cosine_similarity,
)
from rag.indexer import IndexStats, ProjectIndexer
from rag.retriever import Retriever
from rag.vector_store import (
    InMemoryVectorStore,
    QdrantVectorStore,
    SearchHit,
    VectorRecord,
    VectorStore,
)

__all__ = [
    "Cache",
    "Chunk",
    "Embedder",
    "HashingEmbedder",
    "InMemoryCache",
    "InMemoryVectorStore",
    "IndexStats",
    "NullCache",
    "OllamaEmbedder",
    "ProjectIndexer",
    "QdrantVectorStore",
    "RedisCache",
    "Retriever",
    "SearchHit",
    "VectorRecord",
    "VectorStore",
    "chunk_text",
    "cosine_similarity",
]
