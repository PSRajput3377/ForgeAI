"""Tests for the Model Router and providers."""

import pytest
from core.roles import AgentRole
from models.base import Message


@pytest.mark.asyncio
async def test_router_uses_role_specific_model(echo_router):
    resp = await echo_router.complete_for(
        AgentRole.CODER, [Message(role="user", content="hello")]
    )
    assert resp.model == "echo-coder"
    assert "hello" in resp.content


@pytest.mark.asyncio
async def test_router_default_model_fallback(echo_router):
    # A role not in the map falls back to the default model.
    echo_router.role_models.pop(AgentRole.GIT)
    assert echo_router.model_for(AgentRole.GIT) == "echo-default"


@pytest.mark.asyncio
async def test_embed_returns_vector(echo_router):
    vec = await echo_router.embed("some text")
    assert isinstance(vec, list) and len(vec) == 3
