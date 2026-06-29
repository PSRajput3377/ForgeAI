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
from models.openai_provider import OpenAIProvider
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

    Defaults to the Ollama provider; set ``MODEL_PROVIDER=openai`` for hosted
    real code generation (needs ``OPENAI_API_KEY``), or ``MODEL_PROVIDER=echo``
    for the deterministic, instant provider — for demos/CI on hardware that
    can't run the models (ADR-0003: providers are configurable, agent code
    doesn't change).
    """
    if settings.model_provider == "echo":
        provider = EchoProvider()
    elif settings.model_provider == "openai":
        provider = OpenAIProvider(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            timeout=settings.openai_timeout,
        )
    else:
        provider = OllamaProvider(base_url=settings.ollama_url, timeout=settings.ollama_timeout)

    # Pick the role->model map for the active provider. On OpenAI the Ollama
    # model names (qwen3:8b, …) don't exist, so use the openai_* settings.
    if settings.model_provider == "openai":
        planner_model = settings.openai_model_planner
        coder_model = settings.openai_model_coder
        research_model = settings.openai_model_research
        embed_model = settings.openai_model_embed
    else:
        planner_model = settings.model_planner
        coder_model = settings.model_coder
        research_model = settings.model_research
        embed_model = settings.model_embed

    role_models = {
        AgentRole.MANAGER: planner_model,
        AgentRole.PLANNER: planner_model,
        AgentRole.RESEARCHER: research_model,
        AgentRole.MEMORY: research_model,
        AgentRole.CODER: coder_model,
        AgentRole.EXECUTION: coder_model,
        AgentRole.TESTING: coder_model,
        AgentRole.REVIEW: planner_model,
        AgentRole.REFLECTION: coder_model,
        AgentRole.GIT: planner_model,
    }
    return ModelRouter(
        provider=provider,
        role_models=role_models,
        embed_model=embed_model,
        default_model=planner_model,
    )


async def run_request(
    user_request: str, **kwargs
) -> tuple[ProjectState, CollectingGitHubWorkflow | None]:
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
