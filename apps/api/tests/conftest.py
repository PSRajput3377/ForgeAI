"""Shared test fixtures for the agent system."""

import pytest
from core.roles import AgentRole
from models.echo import EchoProvider
from models.router import ModelRouter


@pytest.fixture
def echo_router() -> ModelRouter:
    """A ModelRouter backed by the offline EchoProvider (no network, no models)."""
    role_models = {role: f"echo-{role.value}" for role in AgentRole}
    return ModelRouter(
        provider=EchoProvider(),
        role_models=role_models,
        embed_model="echo-embed",
        default_model="echo-default",
    )
