"""Wiring between the FastAPI app and the agent system.

Builds a ``ModelRouter`` from application settings. Defaults to the Ollama
provider; the role→model map comes straight from configuration (ADR-0003), so
nothing about models is hardcoded in agent code.
"""

from __future__ import annotations

from agents.workflow import run_workflow
from core.roles import AgentRole
from core.state import ProjectState
from models.echo import EchoProvider
from models.ollama import OllamaProvider
from models.router import ModelRouter

from app.config import settings
from app.github_propose import CollectingGitHubWorkflow, github_auto_propose_enabled
from app.github_runtime import build_provider


async def _github_workflow_kwargs() -> dict:
    """Optional GitHub wiring when owner/repo + token are configured."""
    if not github_auto_propose_enabled():
        return {}
    provider = build_provider()
    repo = await provider.get_repository(settings.github_owner, settings.github_repo)
    return {
        "github_workflow": CollectingGitHubWorkflow(),
        "github_repo": repo,
    }


def build_router() -> ModelRouter:
    """Construct the Model Router from settings.

    Defaults to the Ollama provider; set ``MODEL_PROVIDER=echo`` for the
    deterministic, instant provider — for demos/CI on hardware that can't run
    the models (ADR-0003: providers are configurable, agent code doesn't change).
    """
    if settings.model_provider == "echo":
        provider = EchoProvider()
    else:
        provider = OllamaProvider(base_url=settings.ollama_url, timeout=settings.ollama_timeout)
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


async def run_request(user_request: str, **kwargs) -> tuple[ProjectState, CollectingGitHubWorkflow | None]:
    """Run the agent workflow for a user request using the production router.

    Publishes lifecycle events to the process-wide observability bus so the
    timeline, metrics, and live WebSocket reflect the run.

    Returns ``(state, github_collector)`` when GitHub auto-propose is enabled.
    """
    from app.observability_runtime import observability

    gh_kwargs = await _github_workflow_kwargs()
    workflow = gh_kwargs.get("github_workflow")
    state = await run_workflow(
        build_router(),
        user_request,
        bus=observability.bus,
        **{**kwargs, **gh_kwargs},
    )
    return state, workflow if isinstance(workflow, CollectingGitHubWorkflow) else None
