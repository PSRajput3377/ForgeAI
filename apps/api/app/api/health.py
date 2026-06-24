"""Health and readiness endpoints."""

from fastapi import APIRouter

from app.config import settings

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    """Liveness probe — confirms the API process is up."""
    return {"status": "ok", "environment": settings.environment}
