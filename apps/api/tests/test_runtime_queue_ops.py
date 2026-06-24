"""Tests for the job queue/worker pool, health, metrics, flags, parallelism."""

import pytest
from runtime.features import FeatureFlags, NetworkPolicy
from runtime.health import Health, HealthRegistry, MetricsRegistry
from runtime.parallelism import SubTask, merge_results, run_parallel
from runtime.queue import JobQueue, JobStatus
from runtime.reliability import RetryPolicy


@pytest.mark.asyncio
async def test_queue_processes_jobs_with_workers():
    q = JobQueue()
    processed = []

    async def handler(payload):
        processed.append(payload["n"])
        return {"doubled": payload["n"] * 2}

    q.register("double", handler)
    for n in range(5):
        await q.enqueue("double", {"n": n})
    assert q.depth == 5

    await q.run_workers(concurrency=3)
    assert sorted(processed) == [0, 1, 2, 3, 4]
    assert q.depth == 0


@pytest.mark.asyncio
async def test_failed_job_retries_then_dead_letters():
    q = JobQueue(retry_policy=RetryPolicy(max_attempts=2))

    async def always_fail(payload):
        raise RuntimeError("boom")

    q.register("bad", always_fail)
    job = await q.enqueue("bad", {"x": 1})
    await q.run_workers(concurrency=1)

    done = q.get_job(job.id)
    assert done.status == JobStatus.DEAD
    assert done.attempts == 2
    assert len(q.dlq) == 1


@pytest.mark.asyncio
async def test_enqueue_unknown_task_rejected():
    q = JobQueue()
    with pytest.raises(ValueError):
        await q.enqueue("nope", {})


@pytest.mark.asyncio
async def test_health_registry_aggregates():
    reg = HealthRegistry()

    async def up():
        return True

    async def down():
        return False

    reg.register("postgres", up)
    reg.register("redis", up)
    status = await reg.status()
    assert status["status"] == Health.HEALTHY.value

    reg.register("qdrant", down)
    status = await reg.status()
    assert status["status"] == Health.DEGRADED.value
    assert status["components"]["qdrant"] == "down"


@pytest.mark.asyncio
async def test_health_check_exception_is_unhealthy():
    reg = HealthRegistry()

    async def boom():
        raise RuntimeError("connection refused")

    reg.register("redis", boom)
    status = await reg.status()
    assert status["status"] == Health.UNHEALTHY.value


def test_metrics_render_prometheus_format():
    m = MetricsRegistry()
    m.inc("agent_runs_total", 3)
    m.gauge("queue_depth", 7)
    m.observe("agent_latency_seconds", 1.5)
    m.observe("agent_latency_seconds", 2.5)
    out = m.render()
    assert "agent_runs_total 3" in out
    assert "queue_depth 7" in out
    assert "agent_latency_seconds_count 2" in out
    assert "agent_latency_seconds_sum 4.0" in out


def test_feature_flags_default_and_override():
    flags = FeatureFlags(defaults={"experimental_agent": False})
    assert not flags.enabled("experimental_agent")
    flags.override("experimental_agent", "ws-1", True)
    assert flags.enabled("experimental_agent", "ws-1")
    assert not flags.enabled("experimental_agent", "ws-2")


def test_network_policy_allowlist():
    policy = NetworkPolicy()
    assert policy.is_allowed("https://github.com/user/repo")
    assert policy.is_allowed("https://docs.python.org/3/")
    assert not policy.is_allowed("https://evil.example.com/exfil")
    policy.allow("internal.corp")
    assert policy.is_allowed("https://api.internal.corp/x")


@pytest.mark.asyncio
async def test_multi_agent_parallel_split_merge():
    subtasks = [
        SubTask(id="fe", description="build UI", lane="frontend"),
        SubTask(id="be", description="build API", lane="backend"),
        SubTask(id="db", description="schema", lane="database"),
    ]

    async def runner(st):
        if st.lane == "database":
            raise RuntimeError("migration conflict")
        return {"lane": st.lane, "done": True}

    results = await run_parallel(subtasks, runner, concurrency=3)
    merged = merge_results(results)
    assert merged["total"] == 3
    assert merged["succeeded"] == 2
    assert merged["failed"] == 1
    assert "db" in merged["errors"]
    assert merged["by_lane"]["frontend"] is True
