"""Shared test fixtures for the agent system and the API."""

import pytest
import pytest_asyncio
from core.roles import AgentRole
from httpx import ASGITransport, AsyncClient
from models.echo import EchoProvider
from models.router import ModelRouter
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


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


@pytest_asyncio.fixture
async def client(monkeypatch):
    """AsyncClient bound to the app with a fresh in-memory SQLite DB and a clean
    token denylist. Used by the auth + multi-tenancy tests (offline, ADR-0018)."""
    from app.auth.revocation import InMemoryDenylist
    from app.config import settings
    from app.db.base import Base, get_session
    from app.main import app

    # Keep the offline suite hermetic: the API now discovers the repo-root .env
    # regardless of cwd, which may carry a real GITHUB_TOKEN / MODEL_PROVIDER.
    # Tests that need those set them explicitly; the default here is offline.
    monkeypatch.setattr(settings, "github_token", "")
    monkeypatch.setattr(settings, "model_provider", "echo")

    engine = create_async_engine("sqlite+aiosqlite://", future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)

    async def override_session():
        async with factory() as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    monkeypatch.setattr("app.auth.deps.denylist", InMemoryDenylist())
    monkeypatch.setattr("app.api.auth.denylist", InMemoryDenylist())

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()
    await engine.dispose()
