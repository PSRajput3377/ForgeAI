# RAG Specification

Contracts for retrieval-augmented generation. Narrative in
[`../docs/memory.md`](../docs/memory.md). Source: `packages/rag/`.

## Chunking

- MUST split text into overlapping windows; overlap MUST be in `[0, chunk_size)`.
- Each chunk MUST carry provenance metadata (at least `file` and `chunk` index).
- Consecutive chunks MUST share exactly `overlap` units of context.

## Embedding

- An `Embedder` MUST be deterministic for the same input.
- The offline `HashingEmbedder` MUST yield higher cosine similarity for texts
  that share vocabulary than for unrelated texts (so retrieval tests are
  meaningful without a model).
- `HashingEmbedder` and `OllamaEmbedder` MUST be interchangeable behind the
  interface.

## Indexing

- The indexer MUST skip ignored directories (`node_modules`, `.git`, `dist`,
  `build`, `.venv`, `__pycache__`, …).
- Indexing MUST be incremental: unchanged files (same content hash) MUST be
  skipped; changed files MUST have their old chunks removed before re-embedding.
- Every stored vector MUST be addressable by a stable id derived from
  (project, file, chunk).

## Retrieval

- Retrieval MUST be semantic (by meaning), returning the highest-similarity
  chunks with their provenance.
- A configured cache MUST serve repeated identical queries without re-searching.

## Vector store backends

- A `VectorStore` MUST implement `upsert / search / delete_by_filter / count`.
- `InMemoryVectorStore` and `QdrantVectorStore` MUST be interchangeable.

## Acceptance criteria

- [ ] Chunking overlap + metadata verified.
- [ ] Embedding determinism + similarity ordering verified.
- [ ] Noise dirs skipped; incremental skip + re-index verified.
- [ ] Semantic retrieval returns the right file by meaning.
- [ ] Cache hit verified.
