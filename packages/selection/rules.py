"""Rule-based task classifier — the deterministic default strategy (spec §7).

Scores a request against keyword signals per task type and picks the strongest,
defaulting to GENERAL when nothing stands out. Pure and offline: no model call,
fully reproducible. The rationale names the matched signals so every selection
is auditable. A learned strategy can replace this behind ``SelectionStrategy``
once outcome data exists, with no agent/graph change.
"""

from __future__ import annotations

import re

from core.state import ProjectState

from selection.types import Selection, SelectionStrategy, TaskType

# Keyword signals per task type. Ordered specific → general so e.g. a database
# request isn't swallowed by the broader "backend" bucket on a tie.
SIGNALS: dict[TaskType, tuple[str, ...]] = {
    TaskType.DATABASE: (
        "database",
        "schema",
        "migration",
        "sql",
        "postgres",
        "query",
        "table",
        "index",
        "orm",
    ),
    TaskType.FRONTEND: (
        "frontend",
        "ui",
        "component",
        "css",
        "react",
        "page",
        "button",
        "dark mode",
        "style",
        "layout",
    ),
    TaskType.BACKEND: (
        "api",
        "endpoint",
        "backend",
        "auth",
        "jwt",
        "server",
        "route",
        "service",
        "webhook",
        "middleware",
    ),
}


def _count_hits(text: str, keywords: tuple[str, ...]) -> list[str]:
    """Whole-word (or phrase) matches of any keyword in ``text``."""
    hits = []
    for kw in keywords:
        if re.search(rf"\b{re.escape(kw)}\b", text):
            hits.append(kw)
    return hits


class RuleBasedSelector(SelectionStrategy):
    """Keyword-scored classifier. Deterministic; the default selection strategy."""

    name = "rule-based"

    def select(self, state: ProjectState) -> Selection:
        text = state.user_request.lower()

        # (task_type, matched_keywords) for each type with at least one hit.
        scored = [(tt, _count_hits(text, kws)) for tt, kws in SIGNALS.items()]
        scored = [(tt, hits) for tt, hits in scored if hits]

        if not scored:
            return Selection(
                task_type=TaskType.GENERAL,
                rationale="No strong task-type signal; using the full general pipeline.",
            )

        # Most matches wins; ties resolve by SIGNALS order (specific first), which
        # dict iteration preserves — so the result is deterministic.
        best_type, best_hits = max(scored, key=lambda pair: len(pair[1]))
        return Selection(
            task_type=best_type,
            rationale=f"Matched {best_type.value} signals: {', '.join(best_hits)}.",
        )
