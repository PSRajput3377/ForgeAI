"""Health checks and Prometheus-style metrics.

- ``HealthRegistry`` aggregates per-dependency checks (db/redis/qdrant/...) into
  an overall status for ``/health`` and per-service probes.
- ``MetricsRegistry`` exposes counters/gauges/histograms in Prometheus text
  format (scrape target), with no prometheus_client dependency required offline.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from enum import StrEnum

from pydantic import BaseModel

Check = Callable[[], Awaitable[bool]]


class Health(StrEnum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class ComponentHealth(BaseModel):
    name: str
    healthy: bool


class HealthRegistry:
    """Runs registered dependency checks and aggregates the result."""

    def __init__(self) -> None:
        self._checks: dict[str, Check] = {}

    def register(self, name: str, check: Check) -> None:
        self._checks[name] = check

    async def status(self) -> dict:
        components: list[ComponentHealth] = []
        for name, check in self._checks.items():
            try:
                ok = await check()
            except (
                Exception
            ):  # noqa: BLE001 - a failing check is unhealthy, not a crash
                ok = False
            components.append(ComponentHealth(name=name, healthy=ok))

        healthy = sum(c.healthy for c in components)
        total = len(components)
        if total == 0 or healthy == total:
            overall = Health.HEALTHY
        elif healthy == 0:
            overall = Health.UNHEALTHY
        else:
            overall = Health.DEGRADED
        return {
            "status": overall.value,
            "components": {c.name: ("ok" if c.healthy else "down") for c in components},
        }


class MetricsRegistry:
    """Minimal Prometheus-compatible metrics (counters, gauges, histograms)."""

    def __init__(self) -> None:
        self._counters: dict[str, float] = {}
        self._gauges: dict[str, float] = {}
        self._hist: dict[str, list[float]] = {}

    def inc(self, name: str, value: float = 1.0) -> None:
        self._counters[name] = self._counters.get(name, 0.0) + value

    def gauge(self, name: str, value: float) -> None:
        self._gauges[name] = value

    def observe(self, name: str, value: float) -> None:
        self._hist.setdefault(name, []).append(value)

    def render(self) -> str:
        """Render metrics in Prometheus text exposition format."""
        lines: list[str] = []
        for name, val in sorted(self._counters.items()):
            lines.append(f"# TYPE {name} counter")
            lines.append(f"{name} {val}")
        for name, val in sorted(self._gauges.items()):
            lines.append(f"# TYPE {name} gauge")
            lines.append(f"{name} {val}")
        for name, vals in sorted(self._hist.items()):
            count = len(vals)
            total = sum(vals)
            lines.append(f"# TYPE {name} summary")
            lines.append(f"{name}_count {count}")
            lines.append(f"{name}_sum {total}")
        return "\n".join(lines) + "\n"
