"""Agent workflow endpoint.

Exposes the multi-agent run over HTTP. This is a thin API-layer wrapper around
``agents_runtime.run_request`` (which uses the Ollama-backed Model Router).

NOTE: a real run requires the Ollama service up with models pulled
(``make pull-models``). Without them the request will error at the provider —
the offline path is exercised by the test suite via EchoProvider.
"""

from __future__ import annotations

from evaluation import EvaluationStore
from fastapi import APIRouter, Depends
from prompts import active_versions
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents_runtime import run_request
from app.db.base import get_session
from app.performance import PerformanceStore

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
    retries: int


@router.post("/run", response_model=RunResponse)
async def run(body: RunRequest, session: AsyncSession = Depends(get_session)) -> RunResponse:
    """Run the full agent workflow for a user request.

    The run is scored (Phase 12.1) and the evaluation persisted to the
    Performance Database (12.2), so the Agent Analytics dashboard reflects it.
    """
    eval_store = EvaluationStore()
    state = await run_request(
        body.user_request,
        project_id=body.project_id,
        project_path=body.project_path,
        evaluation_store=eval_store,
    )

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
        retries=state.retry_count,
    )
