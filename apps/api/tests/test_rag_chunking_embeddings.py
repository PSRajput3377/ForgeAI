"""Tests for chunking and the embedding engine."""

import pytest
from rag.chunking import chunk_text
from rag.embeddings import HashingEmbedder, cosine_similarity


def test_chunking_overlap_and_metadata():
    text = " ".join(f"w{i}" for i in range(2000))
    chunks = chunk_text(text, chunk_size=800, overlap=100, metadata={"file": "a.py"})
    assert len(chunks) >= 2
    # Metadata propagates and chunk index is recorded.
    assert chunks[0].metadata["file"] == "a.py"
    assert chunks[0].metadata["chunk"] == 0
    # Overlap: last 100 words of chunk 0 == first 100 words of chunk 1.
    w0 = chunks[0].text.split()
    w1 = chunks[1].text.split()
    assert w0[-100:] == w1[:100]


def test_chunking_empty_text():
    assert chunk_text("") == []


def test_chunking_rejects_bad_overlap():
    with pytest.raises(ValueError):
        chunk_text("a b c", chunk_size=10, overlap=10)


@pytest.mark.asyncio
async def test_hashing_embedder_is_deterministic_and_normalized():
    emb = HashingEmbedder(dim=64)
    v1 = await emb.embed("validate jwt token")
    v2 = await emb.embed("validate jwt token")
    assert v1 == v2
    # L2-normalized.
    assert abs(sum(x * x for x in v1) - 1.0) < 1e-9


@pytest.mark.asyncio
async def test_embeddings_capture_word_overlap_similarity():
    emb = HashingEmbedder(dim=512)
    base = await emb.embed("function to verify and validate a jwt auth token")
    similar = await emb.embed("verify jwt token authentication")
    unrelated = await emb.embed("css styling for the dashboard navbar colors")
    assert cosine_similarity(base, similar) > cosine_similarity(base, unrelated)
