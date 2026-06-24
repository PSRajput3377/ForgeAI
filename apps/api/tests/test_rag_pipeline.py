"""End-to-end RAG tests: index a project, retrieve by meaning, incremental re-index."""

import pytest
from rag.cache import InMemoryCache
from rag.embeddings import HashingEmbedder
from rag.indexer import ProjectIndexer
from rag.retriever import Retriever
from rag.vector_store import InMemoryVectorStore


def _make_project(root):
    (root / "auth").mkdir()
    (root / "auth" / "middleware.py").write_text(
        "def verify_token(token):\n"
        "    # validate the jwt authentication token and decode claims\n"
        "    return decode_jwt(token)\n"
    )
    (root / "ui").mkdir()
    (root / "ui" / "navbar.css").write_text(
        ".navbar { color: blue; background: white; }\n" "/* dashboard styling and colors */\n"
    )
    (root / "README.md").write_text("# Demo project\nUses FastAPI and JWT auth.\n")
    # Noise that must be ignored.
    (root / "node_modules").mkdir()
    (root / "node_modules" / "junk.js").write_text("module.exports = {}")


async def _index(root):
    embedder = HashingEmbedder(dim=512)
    store = InMemoryVectorStore()
    indexer = ProjectIndexer("demo", root, embedder, store)
    stats = await indexer.index()
    return embedder, store, indexer, stats


@pytest.mark.asyncio
async def test_index_skips_noise_dirs(tmp_path):
    _make_project(tmp_path)
    _, store, _, stats = await _index(tmp_path)
    assert stats.indexed_files == 3  # middleware.py, navbar.css, README.md
    assert await store.count() >= 3


@pytest.mark.asyncio
async def test_semantic_retrieval_finds_by_meaning(tmp_path):
    _make_project(tmp_path)
    embedder, store, _, _ = await _index(tmp_path)
    retriever = Retriever(embedder, store)
    # Query by *meaning*, not filename.
    hits = await retriever.retrieve("where do we validate the JWT authentication?", limit=1)
    assert hits[0].metadata["file"] == "auth/middleware.py"


@pytest.mark.asyncio
async def test_incremental_indexing_skips_unchanged(tmp_path):
    _make_project(tmp_path)
    _, _, indexer, first = await _index_with(indexer_root=tmp_path)
    # Re-index without changes: everything skipped.
    second = await indexer.index()
    assert second.indexed_files == 0
    assert second.skipped_files == first.indexed_files


async def _index_with(indexer_root):
    embedder = HashingEmbedder(dim=512)
    store = InMemoryVectorStore()
    indexer = ProjectIndexer("demo", indexer_root, embedder, store)
    stats = await indexer.index()
    return embedder, store, indexer, stats


@pytest.mark.asyncio
async def test_incremental_reindex_on_change(tmp_path):
    _make_project(tmp_path)
    embedder = HashingEmbedder(dim=512)
    store = InMemoryVectorStore()
    indexer = ProjectIndexer("demo", tmp_path, embedder, store)
    await indexer.index()
    # Change one file → only it is re-indexed.
    (tmp_path / "README.md").write_text("# Demo\nNow mentions Redis caching too.\n")
    stats = await indexer.index()
    assert stats.indexed_files == 1
    assert stats.skipped_files == 2


@pytest.mark.asyncio
async def test_retrieval_cache_hit(tmp_path):
    _make_project(tmp_path)
    embedder, store, _, _ = await _index(tmp_path)
    cache = InMemoryCache()
    retriever = Retriever(embedder, store, cache=cache)
    q = "jwt validation"
    first = await retriever.retrieve(q, limit=2)
    # Second call served from cache (same results).
    second = await retriever.retrieve(q, limit=2)
    assert [h.id for h in first] == [h.id for h in second]
    assert await cache.get(f"retr:2:{q}") is not None
