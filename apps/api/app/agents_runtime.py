"""Wiring between the FastAPI app and the agent system.

Builds a ``ModelRouter`` from application settings. Defaults to the Ollama
provider; the role→model map comes straight from configuration (ADR-0003), so
nothing about models is hardcoded in agent code.
"""

from __future__ import annotations

from agents.workflow import run_workflow
from core.roles import AgentRole
from core.state import ProjectState
from models.ollama import OllamaProvider
from models.router import ModelRouter

from app.config import settings


def build_router() -> ModelRouter:
    """Construct the production Model Router from settings (Ollama-backed)."""
    provider = OllamaProvider(base_url=settings.ollama_url)
    role_models = {
        AgentRole.MANAGER: settings.model_planner,
        AgentRole.PLANNER: settings.model_planner,
        AgentRole.RESEARCHER: settings.model_research,
        AgentRole.MEMORY: settings.model_research,
        AgentRole.CODER: settings.model_coder,
        AgentRole.EXECUTION: settings.model_coder,
        AgentRole.TESTING: settings.model_coder,
        AgentRole.REVIEW: settings.model_planner,
        AgentRole.REFLECTION: settings.model_coder,
        AgentRole.GIT: settings.model_planner,
    }
    return ModelRouter(
        provider=provider,
        role_models=role_models,
        embed_model=settings.model_embed,
        default_model=settings.model_planner,
    )


async def run_request(user_request: str, **kwargs) -> ProjectState:
    """Run the agent workflow for a user request using the production router.

    Publishes lifecycle events to the process-wide observability bus so the
    timeline, metrics, and live WebSocket reflect the run.
    """
    from app.observability_runtime import observability

    return await run_workflow(
        build_router(), user_request, bus=observability.bus, **kwargs
    )
