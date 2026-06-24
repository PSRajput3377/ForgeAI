# Execution Specification

Contracts for autonomous execution. Narrative in
[`../docs/execution.md`](../docs/execution.md). Source: `packages/execution/`.

## Sandbox

- A `Sandbox` MUST implement `run(command, timeout) -> ExecutionResult` and MAY
  implement `setup`/`teardown` lifecycle hooks.
- Every sandbox MUST call the security check before running a command and MUST
  return `blocked=True` for a blocked command without executing it.
- `DockerSandbox` MUST run in an isolated container with no network by default
  and MUST destroy the container on teardown.
- `LocalSandbox`/`FakeSandbox` and `DockerSandbox` MUST be interchangeable behind
  the interface (offline testability — ADR-0016).
- `ExecutionResult` MUST carry: command, success, exit_code, stdout, stderr,
  duration, timed_out, blocked.

## Security

- The blocked-command list MUST reject (at minimum): `rm -rf /`, `sudo`,
  `chmod 777`, `chown`, `shutdown`, `reboot`, `mkfs`, fork bombs, and
  `curl|wget … | sh`. Enforcement MUST be independent of sandbox isolation.
- Every sandbox MUST enforce a timeout and MUST kill the process on timeout.
- Resource limits (CPU, memory, timeout) MUST be configurable per sandbox.

## Error classification

- Failures MUST be classified into a known `ErrorCategory`.
- `security` errors MUST be non-retryable.
- A classified error SHOULD include a hint (e.g. the missing module) and a fix
  strategy.

## Engine & retries

- The engine MUST run profile steps in order and stop at the first failure.
- The engine MUST NOT retry forever: retries MUST be bounded by `max_retries`.
- The engine MUST only retry when the error is retryable AND a fixer applied a
  change; otherwise it MUST stop and record failure.
- The engine MUST always run sandbox `teardown` (even on failure).
- Every run MUST produce a `RunRecord` (task, success, retries, duration,
  results, artifacts).

## Approval gates

- Gated actions (delete files, git push, merge PR, deploy) MUST default to
  denied and MUST require explicit approval (or configured auto-approval).

## Acceptance criteria

- [ ] Blocked commands rejected by every sandbox.
- [ ] Timeout kills the process and reports `timed_out`.
- [ ] Self-correcting loop recovers (fail → fix → pass) and is bounded.
- [ ] Security errors are not retried.
- [ ] Profiles detected per framework; steps skip undefined commands.
- [ ] Approval gate denies by default.
