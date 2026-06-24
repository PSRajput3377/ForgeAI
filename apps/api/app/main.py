"""FastAPI application entrypoint.

Phase 1 wires up the app, CORS, logging, and a health route only. The agent
and service layers are added in later phases along the documented request path.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.api.agents import router as agents_router
from app.api.health import router as health_router
from app.api.observability import router as observability_router
from app.config import settings
from app.logging import configure_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown hooks."""
    configure_logging()
    logger.info("ForgeAI API starting (env={})", settings.environment)
    yield
    logger.info("ForgeAI API shutting down")


app = FastAPI(
    title="ForgeAI API",
    version="0.1.0",
    description="Autonomous AI engineering platform — backend.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tightened in Phase 2 (auth) / Phase 11 (deploy)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(agents_router)
app.include_router(observability_router)


@app.get("/")
def root() -> dict[str, str]:
    """Service banner."""
    return {"service": "forge-api", "version": "0.1.0"}
