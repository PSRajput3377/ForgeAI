"""execution — autonomous code execution & Docker sandboxing.

Turns ForgeAI from "generate code" into "generate → run → test → debug → fix →
verify". The ExecutionEngine runs a project's profile inside an isolated sandbox
and self-corrects via the reflection/retry loop.

Offline by default: ``FakeSandbox``/``LocalSandbox`` run the whole loop without
Docker; ``DockerSandbox`` provides real isolation in production (ADR-0016).
"""

from execution.approval import ApprovalGate, GatedAction
from execution.artifacts import ArtifactManager, LogCollector, RunRecord
from execution.engine import ExecutionEngine, Fixer, RetryManager, StepOutcome
from execution.errors import ClassifiedError, ErrorCategory, classify_error
from execution.profiles import (
    ExecutionProfile,
    profile_for_framework,
    profile_for_project,
)
from execution.sandbox import (
    DockerSandbox,
    ExecutionResult,
    FakeSandbox,
    LocalSandbox,
    Sandbox,
)
from execution.security import ResourceLimits, check_command
from execution.test_generation import scaffold_for

__all__ = [
    "ApprovalGate",
    "ArtifactManager",
    "ClassifiedError",
    "DockerSandbox",
    "ErrorCategory",
    "ExecutionEngine",
    "ExecutionProfile",
    "ExecutionResult",
    "FakeSandbox",
    "Fixer",
    "GatedAction",
    "LocalSandbox",
    "LogCollector",
    "ResourceLimits",
    "RetryManager",
    "RunRecord",
    "Sandbox",
    "StepOutcome",
    "check_command",
    "classify_error",
    "profile_for_framework",
    "profile_for_project",
    "scaffold_for",
]
