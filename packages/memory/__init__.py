"""memory — long-term memory & project understanding for ForgeAI.

Four memory scopes (session, project, user, knowledge) behind a single
``MemoryManager`` that every agent uses (no direct store access). A
``ContextBuilder`` assembles scored memories + RAG hits into a compact context.

Offline by default (InMemoryStore); the PostgreSQL backend (same interface)
arrives in the Database phase. See ADR-0015.
"""

from memory.context_builder import ContextBuilder
from memory.detection import ProjectProfile, detect_project
from memory.manager import MemoryManager
from memory.scoring import rank_memories, score_memory
from memory.store import InMemoryStore, MemoryStore
from memory.types import MemoryItem, MemoryScope

__all__ = [
    "ContextBuilder",
    "InMemoryStore",
    "MemoryItem",
    "MemoryManager",
    "MemoryScope",
    "MemoryStore",
    "ProjectProfile",
    "detect_project",
    "rank_memories",
    "score_memory",
]
