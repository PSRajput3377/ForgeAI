"""MemoryManager — the single entry point for all memory.

No agent touches the store (or PostgreSQL) directly; they go through the
MemoryManager, which owns store/retrieve/summarize/compress and the logical
clock used for scoring. (Mirrors the Tool Manager pattern from Phase 3.)
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from memory.scoring import rank_memories
from memory.store import MemoryStore
from memory.types import MemoryItem, MemoryScope

# A summarizer takes text and returns a shorter summary. Async so it can call an
# LLM in production; a trivial default keeps everything offline-testable.
Summarizer = Callable[[str], Awaitable[str]]


async def _default_summarizer(text: str) -> str:
    """Offline fallback: first + last line, truncated. Deterministic."""
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if not lines:
        return ""
    head, tail = lines[0], lines[-1]
    summary = head if head == tail else f"{head} … {tail}"
    return summary[:300]


class MemoryManager:
    """Store, retrieve, summarize, and compress memories across all scopes."""

    def __init__(self, store: MemoryStore, summarizer: Summarizer | None = None):
        self.store = store
        self.summarizer = summarizer or _default_summarizer
        self._tick = 0

    def _now(self) -> int:
        self._tick += 1
        return self._tick

    async def store_memory(
        self,
        scope: MemoryScope,
        key: str,
        value: str,
        *,
        importance: float = 1.0,
        **owner: str,
    ) -> MemoryItem:
        """Create or update a memory item."""
        tick = self._now()
        item = MemoryItem(
            scope=scope,
            key=key,
            value=value,
            importance=importance,
            created_tick=tick,
            last_used_tick=tick,
            **{
                k: v
                for k, v in owner.items()
                if k in {"session_id", "project_id", "user_id"}
            },
        )
        await self.store.put(item)
        return item

    async def retrieve(
        self,
        scope: MemoryScope,
        *,
        current_project_id: str | None = None,
        limit: int | None = None,
        **owner: str,
    ) -> list[MemoryItem]:
        """Return scored, ranked memories for a scope/owner. Marks them used."""
        items = await self.store.query(scope, **owner)
        now = self._now()
        for it in items:
            it.usage_count += 1
            it.last_used_tick = now
            await self.store.put(it)
        return rank_memories(
            items, now_tick=now, current_project_id=current_project_id, limit=limit
        )

    async def summarize(self, text: str) -> str:
        """Summarize text via the configured summarizer."""
        return await self.summarizer(text)

    async def compress_session(
        self, session_id: str, *, keep_last: int = 10, summary_key: str = "summary"
    ) -> MemoryItem | None:
        """Compress a long session: summarize old items, store the summary,
        delete the details. Keeps the most recent ``keep_last`` items intact.

        Returns the stored summary item, or None if nothing to compress.
        """
        items = await self.store.query(MemoryScope.SESSION, session_id=session_id)
        # Oldest first.
        items.sort(key=lambda it: it.created_tick)
        if len(items) <= keep_last:
            return None

        # Everything except the most recent `keep_last` items gets folded.
        old = [it for it in items[:-keep_last] if it.key != summary_key]
        combined = "\n".join(f"{it.key}: {it.value}" for it in old)
        summary_text = await self.summarize(combined)

        for it in old:
            await self.store.delete(MemoryScope.SESSION, it.key, session_id=session_id)

        return await self.store_memory(
            MemoryScope.SESSION,
            summary_key,
            summary_text,
            importance=2.0,
            session_id=session_id,
        )
