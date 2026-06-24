# GitHub Integration Specification

Contracts for GitHub integration. Narrative in
[`../docs/github.md`](../docs/github.md). Source: `packages/github/`.

## Provider

- `GitHubProvider` MUST define: get_repository, list/create branch,
  create_commit, open/get/merge PR, post_review, get_check_runs, list_issues.
- `RestGitHubProvider` (real) and `FakeGitHubProvider` (offline) MUST be
  interchangeable behind the interface.
- The fake MUST be deterministic and MUST allow scripting CI outcomes.

## Branching & commits

- Branch names MUST follow conventions: `feature/<slug>`, `fix/<slug>`,
  `docs/<slug>`.
- Agents MUST NOT commit directly to the default branch — always a task branch.
- A commit MUST advance the branch head.

## Pull requests

- PR bodies MUST include Summary, Changes, and Testing sections.
- A PR MUST start in the OPEN state.

## CI

- CI status MUST be derived from check runs (failure if any failed; success only
  if all succeeded).
- A CI failure MUST be classified (reusing the execution error classifier).
- Each poll MUST fetch checks once (no double-consume).

## Autonomous loop

- On CI failure, the manager MUST call the injected fixer, commit its fix, and
  re-run — bounded by `max_ci_retries`.
- The manager MUST NOT merge unless CI is green AND (no reviewer OR review
  approved).
- The manager MUST return a timeline of actions taken.

## Safety

- Force-push, deleting the default branch, and history rewrites MUST NOT be
  performed.
- Merge/delete/deploy MUST be gateable behind human approval.

## Commit authoring (Phase 8.1)

- Commits MUST be authored on a local clone via git (`LocalRepository`), not the
  REST API (ADR-0020). REST `create_commit` MUST raise `NotImplementedError`.
- File writes MUST go through the sandboxed FilesystemTool (path-escape safe).

## Resilience (Phase 8.1)

- The REST client MUST back off on 403/429 using `Retry-After` /
  `X-RateLimit-Reset`, bounded by a retry cap (no infinite loop).
- Collection reads MUST follow `Link: rel="next"` pagination, bounded by
  `max_pages`.

## Webhooks (Phase 8.1)

- Inbound webhooks MUST be HMAC-verified (`X-Hub-Signature-256`) before use.
- A failed-check webhook MUST map to a BUILD_FAILED event (push-not-poll).

## Approval-gated writes (Phase 8.2)

- A write workflow MUST be two-phase: `propose` (no writes) → human decision →
  `execute`.
- `propose` MUST NOT create any branch/commit/PR; it MUST open a pending
  approval request.
- `execute` MUST refuse (raise / HTTP 403) unless the request is approved.
- `ApprovalService` MUST track status (pending/approved/rejected) and MUST NOT
  allow deciding an already-decided request.

## Acceptance criteria

- [ ] Happy path: branch → commit → PR → approve → CI green → merge.
- [ ] propose() writes nothing; execute() refused while pending or rejected.
- [ ] execute() after approval creates the PR and returns its URL.
- [ ] CI fails → classified → fixer → re-run → green → merge (bounded).
- [ ] No fixer / red CI → not merged.
- [ ] Review requesting changes blocks merge.
- [ ] Conventional branch names; never commits to default branch.
- [ ] Entire suite runs offline via FakeGitHubProvider.
- [ ] Local clone → branch → commit → push verified with a bare local remote.
- [ ] Rate-limit backoff + pagination unit-tested with a mock transport.
- [ ] Webhook signature verification + event mapping tested.
- [ ] Live sandbox validation documented (`scripts/verify-github.sh`).
