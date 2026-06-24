# 01 — Product Vision

> The single most important question Phase 0 answers:
> **What exactly are we building?**

## The one idea everything revolves around

ForgeAI is an **autonomous AI engineering platform** that behaves like a
**team of software engineers**, not a single chatbot.

The entire product is a reaction to the limitation of single-model tools:

```
Single chatbot:            ForgeAI:

User                       User
  ↓                          ↓
 LLM                      Engineering Manager
  ↓                          ↓
Answer                     Planner
                             ↓
                           Researcher
                             ↓
                           Coder
                             ↓
                           Tester
                             ↓
                           Reviewer
                             ↓
                           DevOps
                             ↓
                           Result
```

## Why a team beats a single model

A single LLM call tries to do everything at once: understand, plan, write,
verify. It has no division of labor, no checkpoints, and no second opinion.

A **team** gives us:

- **Separation of concerns** — each agent does one job well.
- **Checkpoints** — the Tester and Reviewer can reject bad work before it ships.
- **Traceability** — every step is observable (you watch the team work).
- **Better prompts** — a focused "Coder" prompt beats a do-everything prompt.

## The Manager principle

The **Engineering Manager never writes code.** It delegates — exactly like a
real tech lead. This is a hard rule, not a suggestion. It keeps the
orchestration layer clean and every specialist agent focused.

See [`03-user-flow.md`](03-user-flow.md) for how delegation plays out.
