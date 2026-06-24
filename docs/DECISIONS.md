# Architecture Decision Records (ADRs)

A running log of significant decisions. Newest at the top. Each entry:
what we decided, why, and what we considered.

---

## ADR-0001 — Build as a multi-agent team, not a single LLM call
**Phase:** 0 · **Status:** Accepted

**Decision:** ForgeAI orchestrates specialist agents (Planner, Researcher,
Coder, Tester, Reviewer, DevOps) under an Engineering Manager, instead of a
single do-everything LLM call.

**Why:** Separation of concerns, checkpoints (Tester/Reviewer can reject),
traceability, and tighter per-agent prompts.

**Considered:** Single-model chatbot (rejected — no division of labor or
verification step).

---

## ADR-0002 — The Engineering Manager never writes code
**Phase:** 0 · **Status:** Accepted

**Decision:** The Manager only interprets, decomposes, delegates, and sequences.
All code is produced by specialist agents.

**Why:** Keeps orchestration clean and each specialist focused; mirrors a real
tech lead.

---

## ADR-0003 — All LLM access goes through a Model Router
**Phase:** 0 · **Status:** Accepted

**Decision:** Agents call a LiteLLM-based Model Router, never a provider SDK
directly. Provider/model is configurable at runtime (Ollama, Gemini, Groq,
OpenRouter, ...).

**Why:** Provider independence; add/swap providers with near-zero code change.

---

## ADR-0004 — Three purpose-specific data stores
**Phase:** 0 · **Status:** Accepted

**Decision:** PostgreSQL (system of record), Redis (jobs/queue/locks/ephemeral
state), Qdrant (vector embeddings for memory & RAG).

**Why:** Each store is used for what it's best at rather than overloading one.

---

## ADR-0005 — Ruthless MVP scope for v1.0
**Phase:** 0 · **Status:** Accepted

**Decision:** v1.0 = Login, Create Project, Chat, Planner+Coder+Review agents,
local file editing, Docker execution, project memory. Slack/Jira/AWS/browser
automation are explicitly deferred.

**Why:** Prove the core team-of-agents loop before expanding surface area.
