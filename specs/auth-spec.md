# Auth & Multi-Tenancy Specification

Contracts for authentication, RBAC, and tenancy. Narrative in
[`../docs/auth.md`](../docs/auth.md).

## Authentication

- Passwords MUST be hashed with Argon2; plaintext MUST never be stored.
- Login MUST issue a short-lived access token and a long-lived refresh token.
- Protected routes MUST reject missing/invalid/expired/revoked tokens with 401.
- `refresh` MUST validate the token is of type `refresh`; `current_user` MUST
  validate type `access`.
- Logout MUST revoke the refresh token (and the presenting access token) so it
  cannot be reused.

## RBAC

- Roles MUST be one of `owner > admin > member > viewer` (ranked).
- Role checks MUST be "at least role X" using the rank, not equality.
- Inviting members MUST require ADMIN+.

## Workspace isolation

- A user MUST NOT read or act on a workspace they are not a member of
  (403, not a data leak).
- Creating an organization MUST make the creator the OWNER of its default
  workspace.

## Invitations

- Invites MUST be single-use and MUST expire.
- Accepting an invite MUST grant the invited role and MUST NOT create duplicate
  memberships.

## Data layer

- Models MUST run unchanged on PostgreSQL (prod) and SQLite (tests), selected by
  `DATABASE_URL` (ADR-0018).

## Audit & collaboration

- Significant actions MUST be recorded (activity/audit) with actor + workspace.

## Acceptance criteria

- [ ] Register/login/me/refresh/logout work; revoked tokens rejected.
- [ ] Argon2 hashing; no plaintext.
- [ ] Outsider blocked from a workspace (403).
- [ ] Member cannot invite; admin/owner can.
- [ ] Invite accept grants membership + writes activity.
- [ ] Full suite runs on in-memory SQLite.
