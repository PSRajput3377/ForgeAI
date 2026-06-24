"""Task classification + the selection-strategy interface (spec §7).

Dynamic agent selection routes a request to the right specialist emphasis based
on what *kind* of task it is. Phase 12.7 ships a deterministic rule-based
classifier; the ``SelectionStrategy`` interface lets a *learned* strategy (from
the 12.2/12.9 outcome data) replace it later by config — without changing the
agents or the graph.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import StrEnum

from core.state import ProjectState
from pydantic import BaseModel


class TaskType(StrEnum):
    """The kind of work a request represents."""

    BACKEND = "backend"
    FRONTEND = "frontend"
    DATABASE = "database"
    GENERAL = "general"  # no strong signal — the default, full pipeline


class Selection(BaseModel):
    """The outcome of classifying a request: type + auditable rationale."""

    task_type: TaskType
    rationale: str


class SelectionStrategy(ABC):
    """Decides the task type for a request. Swappable: rule-based now, learned
    later (spec §7). A strategy MUST be deterministic given the same input so
    runs are reproducible and the rationale is meaningful."""

    name: str = "base"

    @abstractmethod
    def select(self, state: ProjectState) -> Selection:
        """Classify the request in ``state`` and explain the choice."""
        raise NotImplementedError
