"""prompts — system prompts that give each agent its identity.

Kept separate from agent logic so prompts can be iterated, versioned, and
eventually loaded from files without touching code. Prompts are versioned and
append-only (Phase 12.3): ``system_prompt(role)`` returns the active version's
text (unchanged for callers), while ``active_version(role)`` /
``active_versions()`` report which versions a run used, for the Evaluation.
"""

from prompts.registry import (
    PROMPTS,
    REGISTRY,
    PromptRegistry,
    active_version,
    active_versions,
    system_prompt,
)

__all__ = [
    "PROMPTS",
    "REGISTRY",
    "PromptRegistry",
    "active_version",
    "active_versions",
    "system_prompt",
]
