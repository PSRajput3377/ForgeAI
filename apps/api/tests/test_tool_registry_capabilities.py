"""Tests for the Tool Registry and the Capability System."""

import pytest
from tools import build_default_registry
from tools.capabilities import Capability, CapabilityResolver
from tools.filesystem import FilesystemTool
from tools.registry import ToolRegistry


def test_registry_register_and_lookup(tmp_path):
    reg = ToolRegistry()
    reg.register(FilesystemTool(tmp_path))
    assert reg.has("filesystem")
    assert reg.get("filesystem") is not None
    assert reg.get("missing") is None


def test_registry_rejects_duplicates(tmp_path):
    reg = ToolRegistry()
    reg.register(FilesystemTool(tmp_path))
    with pytest.raises(ValueError):
        reg.register(FilesystemTool(tmp_path))


def test_default_registry_has_all_tools(tmp_path):
    reg = build_default_registry(tmp_path)
    assert set(reg.names()) == {
        "filesystem",
        "terminal",
        "docker",
        "git",
        "search",
        "project",
        "browser",
        "memory",
    }


def test_capability_resolves_to_tool(tmp_path):
    reg = build_default_registry(tmp_path)
    resolver = CapabilityResolver(reg)
    assert resolver.resolve(Capability.MODIFY_FILE) == "filesystem"
    assert resolver.resolve(Capability.VERSION_CONTROL) == "git"
    # Documentation prefers search, falls back to browser — both registered.
    assert resolver.resolve(Capability.FIND_DOCUMENTATION) == "search"


def test_capability_fallback_order(tmp_path):
    # Only browser registered -> documentation resolves to browser (fallback).
    reg = ToolRegistry()
    from tools.browser import BrowserTool

    reg.register(BrowserTool())
    resolver = CapabilityResolver(reg)
    assert resolver.resolve(Capability.FIND_DOCUMENTATION) == "browser"
    assert resolver.resolve(Capability.VERSION_CONTROL) is None
