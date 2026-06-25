"""Tests for the agent marketplace (Phase 12.10).

Proves spec §9: descriptors register without running code, registration is
approval-gated, discovery returns only approved agents, and the contract check
accepts a conforming agent while rejecting violators. All offline.
"""

import pytest
from agents.planner import PlannerAgent
from marketplace import (
    AgentDescriptor,
    ContractError,
    MarketplaceRegistry,
    RegistrationStatus,
    check_agent_contract,
)


def _descriptor(name="security-scanner") -> AgentDescriptor:
    return AgentDescriptor(
        name=name,
        role="review",
        description="Scans diffs for vulnerabilities",
        author="acme",
        entrypoint="acme_agents.security:SecurityAgent",
        capabilities=["sast", "secrets"],
    )


# --- registration lifecycle -------------------------------------------------


def test_register_is_pending_and_runs_no_code():
    reg = MarketplaceRegistry()
    d = reg.register(_descriptor())
    assert d.status is RegistrationStatus.PENDING
    # entrypoint is recorded but never imported — purely metadata.
    assert d.entrypoint == "acme_agents.security:SecurityAgent"


def test_duplicate_registration_rejected():
    reg = MarketplaceRegistry()
    reg.register(_descriptor())
    with pytest.raises(ValueError, match="already registered"):
        reg.register(_descriptor())


def test_discovery_returns_only_approved():
    reg = MarketplaceRegistry()
    reg.register(_descriptor("a"))
    reg.register(_descriptor("b"))
    reg.approve("a")
    discovered = reg.discover()
    assert [d.name for d in discovered] == ["a"]
    # The unapproved one is still pending, not discoverable.
    assert [d.name for d in reg.pending()] == ["b"]


def test_reject_keeps_agent_undiscoverable():
    reg = MarketplaceRegistry()
    reg.register(_descriptor())
    reg.reject("security-scanner")
    assert reg.discover() == []
    assert reg.get("security-scanner").status is RegistrationStatus.REJECTED


def test_approve_unknown_raises():
    with pytest.raises(KeyError):
        MarketplaceRegistry().approve("ghost")


# --- contract check ---------------------------------------------------------


def test_contract_accepts_conforming_agent():
    # A real platform agent satisfies the contract.
    check_agent_contract(PlannerAgent)  # does not raise


def test_contract_rejects_non_baseagent():
    class NotAnAgent:
        role = "review"

        async def run(self, state):
            return state

    with pytest.raises(ContractError, match="BaseAgent"):
        check_agent_contract(NotAnAgent)


def test_contract_rejects_missing_role():
    from agents.base import BaseAgent

    class NoRole(BaseAgent):
        async def run(self, state):
            return state

    # role is declared on BaseAgent as a bare annotation; an instance/class
    # without a concrete value fails the check.
    NoRole.role = None
    with pytest.raises(ContractError, match="role"):
        check_agent_contract(NoRole)


def test_contract_rejects_sync_run():
    from agents.base import BaseAgent

    class SyncRun(BaseAgent):
        role = "review"

        def run(self, state):  # not async
            return state

    with pytest.raises(ContractError, match="async"):
        check_agent_contract(SyncRun)
