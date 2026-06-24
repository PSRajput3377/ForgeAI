"""Chunking engine — split files into overlapping windows before embedding.

Never embed a whole large file. We split into ~500–1000 "token" windows with
overlap, which gives much better retrieval quality. Tokens here are approximated
by whitespace-split words (cheap and good enough; the real tokenizer lives in
the model). Each chunk carries metadata (file, language, index) so retrieval
results are traceable to their source.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class Chunk(BaseModel):
    """A single chunk of text plus provenance metadata."""

    text: str
    index: int
    metadata: dict = Field(default_factory=dict)


def chunk_text(
    text: str,
    *,
    chunk_size: int = 800,
    overlap: int = 100,
    metadata: dict | None = None,
) -> list[Chunk]:
    """Split text into overlapping word-windows.

    Args:
        chunk_size: target words per chunk (≈500–1000 tokens).
        overlap: words shared between consecutive chunks (preserves context).
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be in [0, chunk_size)")

    words = text.split()
    if not words:
        return []

    base_meta = metadata or {}
    chunks: list[Chunk] = []
    step = chunk_size - overlap
    idx = 0
    for start in range(0, len(words), step):
        window = words[start : start + chunk_size]
        if not window:
            break
        chunks.append(Chunk(text=" ".join(window), index=idx, metadata={**base_meta, "chunk": idx}))
        idx += 1
        if start + chunk_size >= len(words):
            break
    return chunks
