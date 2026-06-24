"""ContextBuilder — assemble a compact, high-value context for the LLM.

Rather than dumping everything into the prompt, the ContextBuilder gathers the
highest-value pieces and renders a small, structured context:

    relevant files (RAG)  +  project summary  +  recent conversation
    +  architecture notes  +  user preferences

It draws from the MemoryManager (scored memories) and, optionally, a Retriever
(semantic RAG over the indexed project). The result is small prompts, better
responses.
"""

from __future__ import annotations

from memory.manager import MemoryManager
from memory.types import MemoryScope


class ContextBuilder:
    """Builds the context string injected into agent prompts."""

    def __init__(self, memory: MemoryManager, retriever=None, max_chars: int = 4000):
        self.memory = memory
        self.retriever = retriever
        self.max_chars = max_chars

    async def build(
        self,
        query: str,
        *,
        project_id: str | None = None,
        user_id: str | None = None,
        session_id: str | None = None,
        rag_limit: int = 5,
        per_scope_limit: int = 5,
    ) -> str:
        """Assemble context for a query. Sections are omitted if empty."""
        sections: list[str] = []

        # 1. Relevant files (semantic RAG).
        if self.retriever is not None:
            hits = await self.retriever.retrieve(query, limit=rag_limit)
            if hits:
                files = "\n".join(
                    f"- {h.metadata.get('file', h.id)} (score {h.score:.2f})\n  {h.text[:200]}"
                    for h in hits
                )
                sections.append(f"## Relevant files\n{files}")

        # 2. Project memory (architecture, stack, conventions).
        if project_id:
            proj = await self.memory.retrieve(
                MemoryScope.PROJECT,
                project_id=project_id,
                current_project_id=project_id,
                limit=per_scope_limit,
            )
            if proj:
                sections.append(
                    "## Project notes\n" + "\n".join(f"- {m.key}: {m.value}" for m in proj)
                )

        # 3. User preferences.
        if user_id:
            prefs = await self.memory.retrieve(
                MemoryScope.USER, user_id=user_id, limit=per_scope_limit
            )
            if prefs:
                sections.append(
                    "## User preferences\n" + "\n".join(f"- {m.key}: {m.value}" for m in prefs)
                )

        # 4. Recent conversation (session).
        if session_id:
            convo = await self.memory.retrieve(
                MemoryScope.SESSION, session_id=session_id, limit=per_scope_limit
            )
            if convo:
                sections.append(
                    "## Recent conversation\n" + "\n".join(f"- {m.key}: {m.value}" for m in convo)
                )

        context = "\n\n".join(sections)
        if len(context) > self.max_chars:
            context = context[: self.max_chars] + "\n…[context truncated]"
        return context
