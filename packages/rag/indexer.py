"""Project indexer — read → split → embed → store, incrementally.

Walks a project, skips noise (node_modules, .git, build, …), chunks each
indexable file, embeds the chunks, and upserts them into the vector store with
provenance metadata (project, file, language, chunk, hash).

Incremental: a per-file content hash is tracked. On re-index, unchanged files
are skipped; changed files have their old chunks deleted and re-embedded.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from pydantic import BaseModel

from rag.chunking import chunk_text
from rag.embeddings import Embedder
from rag.vector_store import VectorRecord, VectorStore

# Directories never indexed.
IGNORE_DIRS = {
    "node_modules",
    ".git",
    "dist",
    "build",
    ".cache",
    ".next",
    "venv",
    ".venv",
    "__pycache__",
    ".ruff_cache",
    ".pytest_cache",
    ".turbo",
}

# Extensions we index. README/Dockerfile handled by name below.
INDEX_EXTENSIONS = {
    ".py",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".md",
    ".txt",
    ".json",
    ".toml",
    ".yaml",
    ".yml",
    ".sql",
    ".sh",
    ".css",
}
INDEX_FILENAMES = {"Dockerfile", "Makefile", "requirements.txt", "package.json"}

# Map extension → language for metadata.
_LANG = {
    ".py": "python",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".js": "javascript",
    ".jsx": "javascript",
    ".md": "markdown",
    ".json": "json",
    ".toml": "toml",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".sql": "sql",
    ".sh": "shell",
    ".css": "css",
}


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


class IndexStats(BaseModel):
    """Summary of an indexing run."""

    indexed_files: int = 0
    skipped_files: int = 0
    chunks: int = 0


class ProjectIndexer:
    """Indexes a project into a vector store, with incremental re-indexing."""

    def __init__(
        self,
        project: str,
        root: str | Path,
        embedder: Embedder,
        store: VectorStore,
        chunk_size: int = 800,
        overlap: int = 100,
    ):
        self.project = project
        self.root = Path(root).resolve()
        self.embedder = embedder
        self.store = store
        self.chunk_size = chunk_size
        self.overlap = overlap
        # file path (relative) -> content hash of last index
        self._hashes: dict[str, str] = {}

    def _is_indexable(self, path: Path) -> bool:
        if any(part in IGNORE_DIRS for part in path.parts):
            return False
        if not path.is_file():
            return False
        return path.suffix in INDEX_EXTENSIONS or path.name in INDEX_FILENAMES

    def iter_files(self):
        """Yield indexable files under the project root."""
        for path in sorted(self.root.rglob("*")):
            if self._is_indexable(path):
                yield path

    async def index(self) -> IndexStats:
        """Index (or incrementally re-index) the whole project."""
        stats = IndexStats()
        for path in self.iter_files():
            rel = path.relative_to(self.root).as_posix()
            try:
                content = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue

            h = _hash(content)
            if self._hashes.get(rel) == h:
                stats.skipped_files += 1
                continue  # unchanged → skip (incremental)

            # Changed (or new): drop old chunks for this file, then re-embed.
            if rel in self._hashes:
                await self.store.delete_by_filter(project=self.project, file=rel)

            chunks = chunk_text(
                content,
                chunk_size=self.chunk_size,
                overlap=self.overlap,
                metadata={
                    "project": self.project,
                    "file": rel,
                    "language": _LANG.get(path.suffix, "text"),
                    "hash": h,
                },
            )
            records = []
            for chunk in chunks:
                vector = await self.embedder.embed(chunk.text)
                records.append(
                    VectorRecord(
                        id=f"{self.project}:{rel}:{chunk.index}",
                        vector=vector,
                        text=chunk.text,
                        metadata=chunk.metadata,
                    )
                )
            if records:
                await self.store.upsert(records)
            self._hashes[rel] = h
            stats.indexed_files += 1
            stats.chunks += len(records)
        return stats
