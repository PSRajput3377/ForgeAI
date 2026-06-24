# Security

ForgeAI runs AI-generated code and lets agents touch a filesystem and a shell.
That makes security a first-class concern, not an afterthought. This document
states the rules; they are binding on every phase.

## Threat model (in one line)

The agents are **semi-trusted**: their *intent* is to help, but their *output*
(LLM-generated code and commands) is **untrusted** and may be wrong, unsafe, or
manipulated via prompt injection in project files.

## Core rules

1. **Never execute commands on the host.** All command/code execution happens
   inside a Docker sandbox (Phase: Docker Sandbox). The Execution agent has no
   host shell access.
2. **Always sandbox.** Containers are resource-limited (CPU/memory), have
   **no network by default**, and are destroyed after use.
3. **Validate every file path.** The Filesystem tool resolves paths against a
   project `root` and rejects anything that escapes it (no `../` traversal,
   no absolute paths outside root). Enforced and tested today.
4. **Restrict destructive operations.** File **delete** and **rename** are not
   exposed to agents in the MVP. Writes are confined to the project root.
5. **Least privilege for tools.** Each tool declares and is limited to its
   scope ([tools.md](tools.md)). The Git tool cannot touch the filesystem
   outside the repo; the DB tool uses scoped, parameterized queries.

## Application security

- **Authentication:** JWT bearer tokens; secret from `JWT_SECRET` (never
  committed). Tighten CORS from the dev `*` before any non-local deployment.
- **Secrets:** only via environment (`.env`, gitignored). `.env.example` ships
  **no real keys**; the MVP needs none (local Ollama).
- **Rate limiting:** agent runs are expensive — per-user/run limits applied at
  the API layer (planned with auth).
- **Input validation:** all request bodies are Pydantic-validated; all
  agent-to-agent messages are typed contracts ([state.md](state.md)).
- **Prompt injection:** treat file/doc content the Researcher reads as data, not
  instructions; the Reviewer is a checkpoint before code is committed.

## Data handling

- Local-first: with Ollama, prompts and code never leave the machine
  ([decisions.md](decisions.md)).
- The audit trail (`messages`) records every agent action for traceability.

## Status

| Control                         | Status                         |
|---------------------------------|--------------------------------|
| Path validation / sandboxed FS  | ✅ implemented + tested        |
| Delete/rename withheld          | ✅ (not exposed)               |
| Docker execution sandbox        | 🔜 Docker Sandbox phase        |
| JWT auth + rate limiting        | 🔜 Authentication phase        |
| Network-restricted containers   | 🔜 Docker Sandbox phase        |

Formal requirements: this doc is the policy; per-component enforcement is
checked against the specs in [`../specs/`](../specs/).
