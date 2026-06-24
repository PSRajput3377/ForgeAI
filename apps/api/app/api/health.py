"""Health, readiness, and Prometheus metrics endpoints."""

from fastapi import APIRouter, Response
from runtime.health import HealthRegistry, MetricsRegistry

from app.config import settings

router = APIRouter(tags=["health"])

# Process-wide registries (dependency probes + Prometheus metrics).
_health = HealthRegistry()
_metrics = MetricsRegistry()


async def _check_db() -> bool:
    """Readiness probe for PostgreSQL."""
    try:
        from sqlalchemy import text

        from app.db.base import get_session_factory

        async with get_session_factory()() as session:
            await session.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


_health.register("database", _check_db)


@router.get("/health")
def health() -> dict[str, str]:
    """Liveness probe — confirms the API process is up (cheap, no deps)."""
    return {"status": "ok", "environment": settings.environment}


@router.get("/health/ready")
async def readiness() -> dict:
    """Readiness probe — checks dependencies (db, …). Used by orchestrators."""
    return await _health.status()


@router.get("/metrics")
def metrics() -> Response:
    """Prometheus scrape endpoint."""
    return Response(content=_metrics.render(), media_type="text/plain; version=0.0.4")
