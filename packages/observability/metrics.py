"""Metrics collector — per-agent / per-tool / per-run statistics from events.

Subscribes to the event bus and aggregates: success rate, average duration,
counts, and token/cost totals. Powers the Metrics Dashboard. Cost is tracked
even though the MVP uses free local models, so swapping to a paid provider later
needs no new plumbing.
"""

from __future__ import annotations

from pydantic import BaseModel

from observability.events import Event, EventType


class AgentStat(BaseModel):
    runs: int = 0
    successes: int = 0
    failures: int = 0
    total_duration: float = 0.0

    @property
    def success_rate(self) -> float:
        total = self.successes + self.failures
        return (self.successes / total) if total else 0.0

    @property
    def avg_duration(self) -> float:
        return (self.total_duration / self.runs) if self.runs else 0.0


class ToolStat(BaseModel):
    calls: int = 0
    failures: int = 0
    total_duration: float = 0.0

    @property
    def avg_duration(self) -> float:
        return (self.total_duration / self.calls) if self.calls else 0.0


class MetricsCollector:
    """Aggregates events into agent/tool/cost metrics."""

    def __init__(self) -> None:
        self.agents: dict[str, AgentStat] = {}
        self.tools: dict[str, ToolStat] = {}
        self.tasks_total = 0
        self.tasks_succeeded = 0
        self.prompt_tokens = 0
        self.completion_tokens = 0

    def handle(self, event: Event) -> None:
        """Event-bus subscriber: update metrics from an event."""
        match event.type:
            case EventType.AGENT_COMPLETED | EventType.AGENT_FAILED:
                stat = self.agents.setdefault(event.agent or "unknown", AgentStat())
                stat.runs += 1
                stat.total_duration += float(event.payload.get("duration", 0.0))
                if event.type == EventType.AGENT_COMPLETED:
                    stat.successes += 1
                else:
                    stat.failures += 1
            case EventType.TOOL_COMPLETED:
                name = event.payload.get("tool", "unknown")
                stat = self.tools.setdefault(name, ToolStat())
                stat.calls += 1
                stat.total_duration += float(event.payload.get("duration", 0.0))
                if not event.payload.get("success", True):
                    stat.failures += 1
            case EventType.RUN_COMPLETED:
                self.tasks_total += 1
                if event.payload.get("success"):
                    self.tasks_succeeded += 1
                self.prompt_tokens += int(event.payload.get("prompt_tokens", 0))
                self.completion_tokens += int(event.payload.get("completion_tokens", 0))

    @property
    def success_rate(self) -> float:
        return (self.tasks_succeeded / self.tasks_total) if self.tasks_total else 0.0

    def snapshot(self) -> dict:
        """Dashboard-ready summary."""
        return {
            "tasks_total": self.tasks_total,
            "success_rate": self.success_rate,
            "agents": {
                name: {
                    "success_rate": s.success_rate,
                    "avg_duration": s.avg_duration,
                    "runs": s.runs,
                }
                for name, s in self.agents.items()
            },
            "tools": {
                name: {
                    "calls": t.calls,
                    "failures": t.failures,
                    "avg_duration": t.avg_duration,
                }
                for name, t in self.tools.items()
            },
            "tokens": {
                "prompt": self.prompt_tokens,
                "completion": self.completion_tokens,
            },
        }
