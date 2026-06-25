"""Agent workflow endpoint.

Exposes the multi-agent run over HTTP. This is a thin API-layer wrapper around
``agents_runtime.run_request`` (which uses the Ollama-backed Model Router).

NOTE: a real run requires the Ollama service up with models pulled
(``make pull-models``). Without them the request will error at the provider —
the offline path is exercised by the test suite via EchoProvider.
"""

from __future__ import annotations

from evaluation import EvaluationStore
from fastapi import APIRouter, Depends, HTTPException, status
from observability.events import EventType
from prompts import active_versions
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents_runtime import run_request
from app.config import settings
from app.db.base import get_session
from app.github_propose import persist_agent_pr_proposal
from app.observability_runtime import observability
from app.performance import PerformanceStore
from app.pr_approvals import PRApprovalStore
from app.projects import ProjectService

router = APIRouter(prefix="/agents", tags=["agents"])


class RunRequest(BaseModel):
    user_request: str
    project_id: str | None = None
    project_path: str | None = None


class RunResponse(BaseModel):
    final_response: str
    review_verdict: str
    tasks: int
    files_changed: list[str]
    generated_files: dict[str, str]
    retries: int
    pr_approval_id: str | None = None
    project_id: str | None = None
    written_files: list[str] = []


@router.post("/run", response_model=RunResponse)
async def run(body: RunRequest, session: AsyncSession = Depends(get_session)) -> RunResponse:
    """Run the full agent workflow for a user request.

    If ``project_id`` is given it MUST resolve to a real project (404 otherwise);
    the run executes against that project's workspace dir and generated files are
    written there (Phase 13.2). The run is scored (12.1) and persisted (12.2).
    """
    # Phase 13.2: bind the run to a real project when an id is given.
    #
    # ``project_id`` has long doubled as the run/correlation id for the
    # observability timeline. We only enforce the project binding when the
    # project store is reachable: if the id resolves to no project, 404; if the
    # store itself is unavailable, degrade to treating project_id as a plain
    # correlation id (legacy behavior) so observability-only paths still work.
    project = None
    project_path = body.project_path
    if body.project_id is not None:
        try:
            project = await ProjectService(session).get(body.project_id)
        except Exception:  # noqa: BLE001 — project store unavailable; degrade
            project = None
            store_reachable = False
        else:
            store_reachable = True
        if store_reachable and project is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found")
        if project is not None:
            # The project's path takes precedence over an explicit project_path.
            project_path = project.path or project_path

    eval_store = EvaluationStore()
    state, github_collector = await run_request(
        body.user_request,
        project_id=body.project_id,
        project_path=project_path,
        evaluation_store=eval_store,
    )

    # Write the generated files into the project's workspace dir on disk.
    written_files: list[str] = []
    if project is not None:
        written_files = ProjectService(session).write_files(project, state.generated_code)

    pr_approval_id: str | None = None
    if github_collector and github_collector.collected:
        try:
            row = await PRApprovalStore(session).create(
                settings.github_owner,
                settings.github_repo,
                github_collector.collected,
            )
            pr_approval_id = row.id
            await observability.bus.emit(
                EventType.APPROVAL_REQUESTED,
                run_id=state.project_id,
                payload={
                    "approval_id": pr_approval_id,
                    "action": "create_pr",
                    "title": github_collector.collected.pr_title,
                },
            )
        except Exception:  # noqa: BLE001
            try:
                await session.rollback()
            except Exception:  # noqa: BLE001
                pass
    else:
        try:
            pr_approval_id = await persist_agent_pr_proposal(session, state)
        except Exception:  # noqa: BLE001
            try:
                await session.rollback()
            except Exception:  # noqa: BLE001
                pass

    # Persist the scored evaluation (best-effort; a run still succeeds even if
    # the analytics write fails — e.g. no DB configured).
    record = eval_store.for_run(state.project_id or "") or (
        eval_store.all()[-1] if eval_store.all() else None
    )
    if record is not None:
        record.prompt_versions = record.prompt_versions or active_versions()
        try:
            await PerformanceStore(session).add(record)
        except Exception:  # noqa: BLE001 — analytics persistence is non-critical
            try:
                await session.rollback()
            except Exception:  # noqa: BLE001
                pass

    return RunResponse(
        final_response=state.final_response,
        review_verdict=state.review_verdict.value,
        tasks=len(state.tasks),
        files_changed=sorted(state.generated_code.keys()),
        generated_files=dict(state.generated_code),
        retries=state.retry_count,
        pr_approval_id=pr_approval_id,
        project_id=body.project_id,
        written_files=written_files,
    )
