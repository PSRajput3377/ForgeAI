"""prompts — system prompts that give each agent its identity.

Kept separate from agent logic so prompts can be iterated, versioned, and
eventually loaded from files without touching code. ``system_prompt(role)``
returns the system message for an agent.
"""

from prompts.registry import PROMPTS, system_prompt

__all__ = ["PROMPTS", "system_prompt"]
