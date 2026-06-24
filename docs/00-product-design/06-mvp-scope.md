# 06 — MVP Scope (v1.0)

> **This is the most critical document in Phase 0.**
> Many projects fail because they try to build everything. We will not.

## In scope for v1.0

✅ Login
✅ Create Project
✅ Chat Interface
✅ Planner Agent
✅ Coding Agent
✅ Review Agent
✅ Local File Editing
✅ Docker Code Execution
✅ Project Memory

That's it.

## Explicitly OUT of scope (for now)

❌ Slack
❌ Jira
❌ AWS deployment
❌ Browser automation

These come **later**, after v1.0 proves the core loop works.

## Reading this against the full design

The full design (e.g. Researcher, Tester, DevOps agents; GitHub PRs; the
full multi-provider Settings UI) is the **north star**. The MVP is the
**smallest slice that proves the core team-of-agents loop**:

> task in → Planner → Coder → Reviewer → file changes executed safely in
> Docker → remembered.

Anything not on the "in scope" list above does not get built in v1.0, even if
it's documented elsewhere. When in doubt, cut it.
