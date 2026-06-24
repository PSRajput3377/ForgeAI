"""Async SQLAlchemy engine, session factory, and declarative base.

The same models run on PostgreSQL (production, via asyncpg) and SQLite
in-memory (tests, via aiosqlite) — selected by the URL. This keeps the entire
data layer testable offline (ADR-0018).
"""

from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


def _async_url(url: str) -> str:
    """Normalize a DATABASE_URL to an async driver."""
    if url.startswith("postgresql+psycopg://"):
        return url.replace("postgresql+psycopg://", "postgresql+asyncpg://", 1)
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


_engine = create_async_engine(_async_url(settings.database_url), future=True)
_session_factory = async_sessionmaker(_engine, expire_on_commit=False)


def get_engine():
    return _engine


def get_session_factory():
    return _session_factory


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency: yield an async DB session."""
    async with _session_factory() as session:
        yield session
