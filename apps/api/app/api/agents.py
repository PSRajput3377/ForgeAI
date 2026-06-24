"""Agent workflow endpoint.

Exposes the multi-agent run over HTTP. This is a thin API-layer wrapper around
``agents_runtime.run_request`` (which uses the Ollama-backed Model Router).

NOTE: a real run requires the Ollama service up with models pulled
(``make pull-models``). Without them the request will error at the provider —
the offline path is exercised by the test suite via EchoProvider.
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.agents_runtime import run_request

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
async def run(body: RunRequest) -> RunResponse:
    """Run the full agent workflow for a user request."""
    state = await run_request(
        body.user_request,
        project_id=body.project_id,
        project_path=body.project_path,
    )
    return RunResponse(
        final_response=state.final_response,
        review_verdict=state.review_verdict.value,
        tasks=len(state.tasks),
        files_changed=sorted(state.generated_code.keys()),
        retries=state.retry_count,
    )
