"""Job queue + worker pool — turn blocking agent runs into queued background jobs.

    FastAPI → enqueue → [queue] → worker pool → result

This is the production model: non-blocking, scalable, retryable, schedulable.
The interface mirrors Celery/RQ; an in-memory backend backs offline tests, and a
Redis/Celery backend implements the same interface in production (ADR-0022).
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from enum import StrEnum

from pydantic import BaseModel, Field

from runtime.reliability import DeadLetterQueue, RetryPolicy

Handler = Callable[[dict], Awaitable[dict]]


class JobStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    DEAD = "dead"  # exhausted retries → DLQ


class Job(BaseModel):
    id: str
    task: str
    payload: dict = Field(default_factory=dict)
    status: JobStatus = JobStatus.QUEUED
    attempts: int = 0
    result: dict | None = None
    error: str = ""


class JobQueue:
    """In-memory async job queue with a worker pool, retries, and a DLQ."""

    def __init__(self, retry_policy: RetryPolicy | None = None):
        self._handlers: dict[str, Handler] = {}
        self._queue: asyncio.Queue[str] = asyncio.Queue()
        self._jobs: dict[str, Job] = {}
        self.retry_policy = retry_policy or RetryPolicy()
        self.dlq = DeadLetterQueue()
        self._counter = 0

    def register(self, task: str, handler: Handler) -> None:
        self._handlers[task] = handler

    async def enqueue(self, task: str, payload: dict | None = None) -> Job:
        if task not in self._handlers:
            raise ValueError(f"No handler registered for task: {task}")
        self._counter += 1
        job = Job(id=f"job-{self._counter}", task=task, payload=payload or {})
        self._jobs[job.id] = job
        await self._queue.put(job.id)
        return job

    def get_job(self, job_id: str) -> Job | None:
        return self._jobs.get(job_id)

    @property
    def depth(self) -> int:
        """Number of jobs waiting to be processed (queue length metric)."""
        return self._queue.qsize()

    async def _process(self, job: Job) -> None:
        handler = self._handlers[job.task]
        job.status = JobStatus.RUNNING
        for attempt in range(1, self.retry_policy.max_attempts + 1):
            job.attempts = attempt
            try:
                job.result = await handler(job.payload)
                job.status = JobStatus.SUCCEEDED
                return
            except (
                Exception
            ) as exc:  # noqa: BLE001 - job failures are data, not crashes
                job.error = str(exc)
        # Exhausted retries → dead-letter.
        job.status = JobStatus.DEAD
        self.dlq.add(job.id, job.payload, job.error, job.attempts)

    async def run_workers(self, *, concurrency: int = 4, drain: bool = True) -> None:
        """Process queued jobs with ``concurrency`` workers.

        With ``drain=True`` (default), returns once the queue is empty — ideal
        for tests and batch runs. A production worker would loop forever.
        """

        async def worker() -> None:
            while True:
                try:
                    job_id = self._queue.get_nowait()
                except asyncio.QueueEmpty:
                    return
                try:
                    await self._process(self._jobs[job_id])
                finally:
                    self._queue.task_done()

        if drain:
            await asyncio.gather(*(worker() for _ in range(concurrency)))
