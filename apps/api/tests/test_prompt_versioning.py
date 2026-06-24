"""Tests for prompt versioning (Phase 12.3).

Proves spec §3: prompts are versioned and addressable, ``system_prompt(role)``
is unchanged for callers, versions are append-only (no in-place mutation), and a
run records the versions it used. All offline.
"""

import pytest
from core.roles import AgentRole
from prompts import PROMPTS, PromptRegistry, active_version, active_versions, system_prompt


def test_system_prompt_backward_compatible():
    # Active version is v1 and matches the original flat dict body.
    for role in AgentRole:
        assert system_prompt(role) == PROMPTS[role]
        assert active_version(role) == "v1"


def test_active_versions_covers_every_role():
    versions = active_versions()
    assert set(versions) == {role.value for role in AgentRole}
    assert all(v == "v1" for v in versions.values())


def test_register_adds_and_activates_new_version():
    reg = PromptRegistry()
    reg.register(AgentRole.PLANNER, "v2", "Plan better.")
    assert reg.active_version(AgentRole.PLANNER) == "v2"
    assert reg.get(AgentRole.PLANNER) == "Plan better."
    # v1 is still retrievable by name — history preserved.
    assert reg.get(AgentRole.PLANNER, "v1") == PROMPTS[AgentRole.PLANNER]
    assert reg.versions(AgentRole.PLANNER) == ["v1", "v2"]


def test_register_without_activation_keeps_active():
    reg = PromptRegistry()
    reg.register(AgentRole.CODER, "v2", "Code better.", activate=False)
    assert reg.active_version(AgentRole.CODER) == "v1"
    assert reg.get(AgentRole.CODER, "v2") == "Code better."


def test_versions_are_immutable():
    reg = PromptRegistry()
    with pytest.raises(ValueError, match="immutable"):
        reg.register(AgentRole.PLANNER, "v1", "overwrite attempt")


def test_activate_switches_and_validates():
    reg = PromptRegistry()
    reg.register(AgentRole.REVIEW, "v2", "Review better.", activate=False)
    reg.activate(AgentRole.REVIEW, "v2")
    assert reg.active_version(AgentRole.REVIEW) == "v2"
    with pytest.raises(KeyError):
        reg.activate(AgentRole.REVIEW, "v99")


def test_registry_isolation():
    # A fresh registry doesn't see another's registrations (no shared state).
    a = PromptRegistry()
    b = PromptRegistry()
    a.register(AgentRole.GIT, "v2", "Ship it.")
    assert a.active_version(AgentRole.GIT) == "v2"
    assert b.active_version(AgentRole.GIT) == "v1"


async def test_workflow_records_active_prompt_versions(echo_router):
    """A scored run records the prompt version each role used (spec §3)."""
    from agents.workflow import run_workflow
    from evaluation import EvaluationStore

    store = EvaluationStore()
    await run_workflow(echo_router, "Add a flag", project_id="run-pv", evaluation_store=store)
    ev = store.for_run("run-pv")
    assert ev is not None
    assert ev.prompt_versions["planner"] == "v1"
    assert set(ev.prompt_versions) == {role.value for role in AgentRole}
