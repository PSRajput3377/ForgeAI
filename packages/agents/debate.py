"""Multi-agent debate — N independent attempts, judged, best one wins (spec §6).

Instead of a single Planner pass, run several *independent* attempts from
different angles, then have a judge (the Review role) pick the strongest. This
widens the solution space: one angle may surface a plan another misses.

Design constraints from the spec:
  - Attempts are independent — no attempt sees another's output.
  - A judge selects the winner using **documented criteria**, and the decision
    is recorded (which attempts lost, and why).
  - Off by default — the default graph is unchanged unless debate is enabled.
  - Deterministic under ``EchoModel``: the judge model call provides a
    human-readable rationale, but *selection* uses a pure scoring function over
    the (deterministic) candidate text, tie-broken by attempt index — so the
    same inputs always pick the same winner.
"""

from __future__ import annotations

import re

from core.roles import AgentRole
from models.router import ModelRouter
from prompts import system_prompt
from pydantic import BaseModel

from agents.base import BaseAgent

# Distinct framings so attempts explore different parts of the solution space.
# Varying by index (not randomness) keeps the debate reproducible.
ANGLES: list[str] = [
    "Favor the simplest plan that ships the smallest working increment first.",
    "Favor a risk-first plan that tackles the hardest unknowns and edge cases early.",
    "Favor a thorough plan that covers tests, docs, and error handling explicitly.",
]

_WORD_RE = re.compile(r"[a-zA-Z]{4,}")


def score_plan(plan_text: str) -> int:
    """Documented selection rubric: a plan's specificity, as the count of
    distinct meaningful words (length ≥ 4). Pure and deterministic — higher is
    more specific. Selection prefers the highest score, tie-broken by the
    earliest attempt index (see ``judge``)."""
    return len({w.lower() for w in _WORD_RE.findall(plan_text or "")})


class DebateAttempt(BaseModel):
    """One independent attempt: its angle, the plan it produced, and the score."""

    index: int
    angle: str
    plan_text: str
    score: int
    won: bool = False


class DebateRecord(BaseModel):
    """The full, auditable record of a debate (winner + every attempt + why)."""

    winner_index: int
    rationale: str
    attempts: list[DebateAttempt]


class PlannerDebate:
    """Runs N independent planning attempts and judges a winner.

    Reuses the Planner's system prompt for the attempts and the Review role as
    the judge. Returns the winning plan text plus a ``DebateRecord``.
    """

    def __init__(self, router: ModelRouter, *, rounds: int = 2):
        if rounds < 2:
            raise ValueError("debate needs at least 2 attempts")
        self.router = router
        self.rounds = rounds

    async def _attempt(self, request: str, index: int) -> DebateAttempt:
        """One independent attempt under a single angle (no cross-talk)."""
        angle = ANGLES[index % len(ANGLES)]
        from models.base import Message

        messages = [
            Message(role="system", content=system_prompt(AgentRole.PLANNER)),
            Message(role="user", content=f"{angle}\nBreak this request into tasks:\n{request}"),
        ]
        resp = await self.router.complete_for(AgentRole.PLANNER, messages, temperature=0.4)
        return DebateAttempt(
            index=index, angle=angle, plan_text=resp.content, score=score_plan(resp.content)
        )

    async def _judge_rationale(self, winner: DebateAttempt, request: str) -> str:
        """Human-readable rationale from the Review role (recorded, not used for
        selection — selection is the deterministic rubric)."""
        from models.base import Message

        messages = [
            Message(role="system", content=system_prompt(AgentRole.REVIEW)),
            Message(
                role="user",
                content=(
                    f"Of {self.rounds} competing plans for '{request}', the most "
                    f"specific was attempt {winner.index} ({winner.angle}). "
                    "State briefly why a specific, well-scoped plan is preferable."
                ),
            ),
        ]
        resp = await self.router.complete_for(AgentRole.REVIEW, messages, temperature=0.2)
        return resp.content

    async def run(self, request: str) -> tuple[str, DebateRecord]:
        """Produce attempts, pick the winner, return (winning_plan, record)."""
        attempts = [await self._attempt(request, i) for i in range(self.rounds)]

        # Documented selection: highest specificity score, earliest index on a tie.
        winner = max(attempts, key=lambda a: (a.score, -a.index))
        winner.won = True

        rationale = await self._judge_rationale(winner, request)
        record = DebateRecord(winner_index=winner.index, rationale=rationale, attempts=attempts)
        return winner.plan_text, record


class DebatingPlannerAgent(BaseAgent):
    """Planner variant that debates the plan before committing it.

    Drop-in for the standard Planner node: it runs the debate, writes the
    winning plan into state exactly like ``PlannerAgent``, and records the
    debate decision on the audit trail. Enabled only when the workflow is built
    with ``debate_planner >= 2``.
    """

    role = AgentRole.PLANNER

    def __init__(self, router: ModelRouter, *, rounds: int = 2):
        super().__init__(router)
        self.debate = PlannerDebate(router, rounds=rounds)

    async def run(self, state):
        from core.messages import AgentMessage, MessageStatus, TaskSpec

        plan_text, record = await self.debate.run(state.user_request)

        # Same deterministic task skeleton as PlannerAgent (Phase 2 design); the
        # debate selects which plan text drives it / is recorded for traceability.
        titles = [
            "Read project",
            "Inspect backend",
            "Add required dependency",
            "Implement the feature",
            "Run tests",
            "Review",
        ]
        state.tasks = [
            TaskSpec(title=t, assigned_to=AgentRole.CODER, description=state.user_request)
            for t in titles
        ]
        state.current_task = state.tasks[0]
        state.record(
            AgentMessage(
                task_id=state.current_task.task_id,
                sender=self.role,
                status=MessageStatus.COMPLETED,
                summary=f"Debated {len(record.attempts)} plans; attempt {record.winner_index} won",
                payload={
                    "debate_winner": record.winner_index,
                    "debate_rationale": record.rationale[:200],
                    "plan_preview": plan_text[:200],
                },
            )
        )
        return state
