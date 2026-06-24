"""System prompts for every agent role — versioned and addressable (Phase 12.3).

Different prompts = specialized behavior. These encode the responsibilities and
hard rules from the Phase 2 design (e.g. the Manager and Planner never write
code; the Coder only writes code).

Prompts are **versioned**: each role has one or more named versions with exactly
one marked active. Versions are **append-only** — improving a prompt registers a
new version (``v2``), never edits ``v1`` — so historical evaluations stay
interpretable (which prompt produced which result; ADR-0025, spec §3).
``system_prompt(role)`` returns the active version's text and is unchanged for
callers; ``active_version(role)`` reports which version that is, for recording
on the ``Evaluation``.
"""

from core.roles import AgentRole

# The original (v1) bodies. Kept as a flat dict for backward compatibility:
# external code may still import ``PROMPTS``; ``system_prompt`` resolves through
# the registry below.
PROMPTS: dict[AgentRole, str] = {
    AgentRole.MANAGER: (
        "You are the Engineering Manager of an AI software team.\n"
        "You NEVER write code. You interpret the user's request, decide which "
        "specialist agents are required, decide the execution order, monitor "
        "progress, handle failures, and produce the final response. "
        "You delegate — exactly like a tech lead."
    ),
    AgentRole.PLANNER: (
        "You are an expert software architect.\n"
        "Break the request into a numbered list of small, executable tasks.\n"
        "Never write code. Only plan."
    ),
    AgentRole.RESEARCHER: (
        "You are a research engineer.\n"
        "Gather only the context relevant to the task from the provided "
        "README, docs, and existing code. Output relevant context — nothing "
        "more. Do not write code."
    ),
    AgentRole.MEMORY: (
        "You are the team's memory.\n"
        "Surface relevant short-term context (current task, files, errors) and "
        "long-term knowledge (coding style, past decisions, preferred "
        "frameworks) for the current request."
    ),
    AgentRole.CODER: (
        "You are a senior backend engineer.\n"
        "You receive a task plus relevant files, research, and memory. "
        "Only write code. Never explain. Always work from the given context — "
        "never guess."
    ),
    AgentRole.EXECUTION: (
        "You are an execution agent.\n"
        "Given generated code, determine the commands needed to install, build, "
        "and run it. You run commands inside a sandbox and report logs, exit "
        "codes, stdout, and stderr."
    ),
    AgentRole.TESTING: (
        "You are a QA engineer.\n"
        "Run unit tests, check APIs, validate outputs, and confirm the feature "
        "works. Report pass/fail with evidence."
    ),
    AgentRole.REVIEW: (
        "You are a principal engineer.\n"
        "Review code for performance, security, readability, architecture, "
        "naming, and code smells. Output either APPROVED or a list of required "
        "changes."
    ),
    AgentRole.REFLECTION: (
        "You are a debugging specialist.\n"
        "Given failing logs, identify the root cause and propose a concrete "
        "fix so the work can be retried. Be specific and actionable."
    ),
    AgentRole.GIT: (
        "You are a release engineer.\n"
        "Stage changes, write a clear conventional-commit message, commit, and "
        "(later) open a pull request."
    ),
}


class PromptRegistry:
    """Append-only, versioned store of agent prompts with one active version each.

    Seeded with the ``v1`` bodies above. ``register`` adds a new named version
    (and may activate it); it refuses to overwrite an existing version, keeping
    the history immutable.
    """

    def __init__(self, seed: dict[AgentRole, str] | None = None) -> None:
        # role -> {version -> body}
        self._versions: dict[AgentRole, dict[str, str]] = {}
        # role -> active version name
        self._active: dict[AgentRole, str] = {}
        for role, body in (seed if seed is not None else PROMPTS).items():
            self._versions[role] = {"v1": body}
            self._active[role] = "v1"

    def register(self, role: AgentRole, version: str, body: str, *, activate: bool = True) -> None:
        """Add a new prompt version. Versions are append-only.

        Raises ``ValueError`` if ``version`` already exists for ``role`` — an
        existing version must never be mutated (spec §3).
        """
        versions = self._versions.setdefault(role, {})
        if version in versions:
            raise ValueError(
                f"prompt {role.value}/{version} already exists (versions are immutable)"
            )
        versions[version] = body
        if activate or role not in self._active:
            self._active[role] = version

    def activate(self, role: AgentRole, version: str) -> None:
        """Mark an existing version active. Raises ``KeyError`` if unknown."""
        if version not in self._versions.get(role, {}):
            raise KeyError(f"no prompt {role.value}/{version}")
        self._active[role] = version

    def get(self, role: AgentRole, version: str | None = None) -> str:
        """Body for a role — the active version unless one is named."""
        version = version or self._active[role]
        return self._versions[role][version]

    def active_version(self, role: AgentRole) -> str:
        """The active version name for a role (recorded on the Evaluation)."""
        return self._active[role]

    def versions(self, role: AgentRole) -> list[str]:
        """All version names registered for a role, in insertion order."""
        return list(self._versions.get(role, {}))

    def active_versions(self) -> dict[str, str]:
        """role value -> active version, for every role (run provenance)."""
        return {role.value: version for role, version in self._active.items()}


# Process-wide default registry. ``system_prompt`` resolves through it so the
# active version is a single source of truth shared by every agent.
REGISTRY = PromptRegistry()


def system_prompt(role: AgentRole) -> str:
    """Return the active system prompt for an agent role (backward compatible)."""
    return REGISTRY.get(role)


def active_version(role: AgentRole) -> str:
    """Return the active prompt version name for a role."""
    return REGISTRY.active_version(role)


def active_versions() -> dict[str, str]:
    """Return the active prompt version for every role (run provenance)."""
    return REGISTRY.active_versions()
