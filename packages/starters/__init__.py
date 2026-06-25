"""starters — versioned project scaffolds (Phase 13.3).

A starter is a deterministic, named set of files (a relative-path -> content
map). Scaffolding one needs no model and no network, so bootstrap is instant and
reproducible offline (spec §3). The agent pipeline then extends the scaffolded
project.

New starters slot in behind the same interface: add a builder to STARTERS.
"""

from starters.registry import STARTERS, StarterInfo, get_starter, list_starters

__all__ = ["STARTERS", "StarterInfo", "get_starter", "list_starters"]
