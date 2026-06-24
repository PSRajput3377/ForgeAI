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

## Acceptance criteria

- [ ] Happy path: branch → commit → PR → approve → CI green → merge.
- [ ] CI fails → classified → fixer → re-run → green → merge (bounded).
- [ ] No fixer / red CI → not merged.
- [ ] Review requesting changes blocks merge.
- [ ] Conventional branch names; never commits to default branch.
- [ ] Entire suite runs offline via FakeGitHubProvider.
