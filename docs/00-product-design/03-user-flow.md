# 03 — User Flow & Delegation Model

## End-to-end user flow

```
Login
  ↓
Create Project
  ↓
Choose Stack
  ↓
Dashboard Opens
  ↓
Type Task               e.g. "Add JWT authentication"
  ↓
Planner Creates Plan
  ↓
Research Starts
  ↓
Coding Begins
  ↓
Tests Run
  ↓
Review
  ↓
Result                  (diff / PR / running app)
```

## The delegation model

When a task arrives, the **Engineering Manager** receives it and **delegates**.
It does not write code itself.

```
                 Engineering Manager
                         │
        ┌────────┬───────┼───────┬──────────────┬──────┬────────┐
        ▼        ▼       ▼       ▼              ▼      ▼        ▼
    Research  Coding  Testing  Review  Documentation  Git    DevOps
```

The Manager's responsibilities:

- Interpret the user's task.
- Break it into sub-tasks.
- Assign each sub-task to the right specialist.
- Sequence the work and handle hand-offs.
- Decide when the result is good enough to return.

**The Manager never writes code — it delegates. Exactly like a tech lead.**

This is the core orchestration contract that Phase 4 (Agent Architecture)
and Phase 7 (Multi-Agent Workflow) must enforce.
