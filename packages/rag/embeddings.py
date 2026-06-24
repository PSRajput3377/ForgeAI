"""Embedding engine — turn text into vectors.

Two backends behind one interface (mirrors the Model Router pattern, ADR-0003):

- ``OllamaEmbedder``  real embeddings via the Model Router (nomic-embed-text).
- ``HashingEmbedder`` deterministic, offline, dependency-free. Hashes tokens
  into a fixed-dim bag-of-words vector so texts sharing words are cosine-similar
  — good enough to test retrieval quality without a live model.
"""

from __future__ import annotations

import hashlib
import math
import re
from abc import ABC, abstractmethod

_TOKEN_RE = re.compile(r"[A-Za-z0-9_]+")


def tokenize(text: str) -> list[str]:
    """Lowercase word/identifier tokens."""
    return [t.lower() for t in _TOKEN_RE.findall(text)]


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Cosine similarity of two equal-length vectors (0 if either is zero)."""
    if len(a) != len(b):
        raise ValueError("vectors must have equal length")
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


class Embedder(ABC):
    """Interface for embedding text into vectors."""

    dim: int

    @abstractmethod
    async def embed(self, text: str) -> list[float]:
        """Embed a single string."""
        raise NotImplementedError

    async def embed_many(self, texts: list[str]) -> list[list[float]]:
        """Embed several strings (default: sequential)."""
        return [await self.embed(t) for t in texts]


class HashingEmbedder(Embedder):
    """Deterministic offline embedder (hashed bag-of-words, L2-normalized)."""

    def __init__(self, dim: int = 256):
        self.dim = dim

    def _bucket(self, token: str) -> int:
        digest = hashlib.md5(token.encode("utf-8")).digest()
        return int.from_bytes(digest[:4], "big") % self.dim

    async def embed(self, text: str) -> list[float]:
        vec = [0.0] * self.dim
        for token in tokenize(text):
            vec[self._bucket(token)] += 1.0
        norm = math.sqrt(sum(v * v for v in vec))
        if norm > 0:
            vec = [v / norm for v in vec]
        return vec


class OllamaEmbedder(Embedder):
    """Real embeddings via the Model Router (Ollama nomic-embed-text)."""

    # nomic-embed-text produces 768-dim vectors.
    def __init__(self, router, dim: int = 768):
        self.router = router
        self.dim = dim

    async def embed(self, text: str) -> list[float]:
        return await self.router.embed(text)
