"""selection — dynamic agent selection (Phase 12.7).

Classifies a request by task type (backend / frontend / database / general)
behind a ``SelectionStrategy`` interface, recording the rationale on the run.
Phase 12.7 ships a deterministic rule-based classifier; a learned strategy can
replace it by config once outcome data exists, with no agent/graph change
(spec §7).
"""

from selection.rules import SIGNALS, RuleBasedSelector
from selection.types import Selection, SelectionStrategy, TaskType

__all__ = [
    "SIGNALS",
    "RuleBasedSelector",
    "Selection",
    "SelectionStrategy",
    "TaskType",
]
