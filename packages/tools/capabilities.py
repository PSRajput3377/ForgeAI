"""Capability System — agents declare WHAT they want, not WHICH tool to use.

Instead of an agent picking a tool directly, it requests a capability (e.g.
"modify a file", "find documentation"). The CapabilityResolver maps the
capability to the tool(s) that fulfill it. This lets implementations change
(local search → web search) without touching agent logic, and lets multiple
tools satisfy one capability. (Phase 3 ⭐)
"""

from __future__ import annotations

from enum import StrEnum

from tools.registry import ToolRegistry


class Capability(StrEnum):
    """What an agent wants to achieve, independent of the tool that does it."""

    READ_FILE = "read_file"
    MODIFY_FILE = "modify_file"
    RUN_COMMAND = "run_command"
    RUN_SANDBOXED = "run_sandboxed"
    VERSION_CONTROL = "version_control"
    FIND_DOCUMENTATION = "find_documentation"
    BROWSE_WEB = "browse_web"
    RECALL_MEMORY = "recall_memory"
    UNDERSTAND_PROJECT = "understand_project"


# A capability maps to an ORDERED list of tool names that can fulfill it.
# The resolver returns the first one currently registered, so you can prefer a
# richer tool and fall back (e.g. browser → search for documentation).
_CAPABILITY_TOOLS: dict[Capability, list[str]] = {
    Capability.READ_FILE: ["filesystem"],
    Capability.MODIFY_FILE: ["filesystem"],
    Capability.RUN_COMMAND: ["terminal"],
    Capability.RUN_SANDBOXED: ["docker", "terminal"],
    Capability.VERSION_CONTROL: ["git"],
    Capability.FIND_DOCUMENTATION: ["search", "browser"],
    Capability.BROWSE_WEB: ["browser"],
    Capability.RECALL_MEMORY: ["memory"],
    Capability.UNDERSTAND_PROJECT: ["project"],
}


class CapabilityResolver:
    """Resolves a Capability to a concrete registered tool name."""

    def __init__(self, registry: ToolRegistry) -> None:
        self.registry = registry

    def candidates(self, capability: Capability) -> list[str]:
        """All tool names that could fulfill the capability (in preference order)."""
        return _CAPABILITY_TOOLS.get(capability, [])

    def resolve(self, capability: Capability) -> str | None:
        """Return the preferred *registered* tool name for the capability."""
        for name in self.candidates(capability):
            if self.registry.has(name):
                return name
        return None
