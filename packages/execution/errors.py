"""Error classification — turn raw logs into a typed error + fix strategy.

The Reflection Engine uses the classification to decide *how* to fix: a missing
dependency is fixed differently from a syntax error or a failing assertion.
Different errors trigger different fix strategies (Phase 5 design).
"""

from __future__ import annotations

import re
from enum import StrEnum

from pydantic import BaseModel


class ErrorCategory(StrEnum):
    DEPENDENCY = "dependency"
    SYNTAX = "syntax"
    RUNTIME = "runtime"
    TEST_FAILURE = "test_failure"
    SECURITY = "security"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"


class ClassifiedError(BaseModel):
    """A categorized error plus a suggested fix strategy."""

    category: ErrorCategory
    detail: str = ""
    # Machine hint for the fixer, e.g. the missing module name.
    hint: str = ""
    fix_strategy: str = ""
    retryable: bool = True


# (category, compiled regex, capture-group name for the hint, strategy text)
_RULES: list[tuple[ErrorCategory, re.Pattern, str, str]] = [
    (
        ErrorCategory.DEPENDENCY,
        re.compile(r"(?:ModuleNotFoundError|ImportError)[^'\"]*['\"](?P<mod>[\w\-\.]+)['\"]"),
        "mod",
        "Add the missing dependency and reinstall, then retry.",
    ),
    (
        ErrorCategory.DEPENDENCY,
        re.compile(r"Cannot find module ['\"](?P<mod>[\w\-\./@]+)['\"]"),
        "mod",
        "Install the missing npm package, then retry.",
    ),
    (
        ErrorCategory.SYNTAX,
        re.compile(r"(SyntaxError|IndentationError|Unexpected token)(?P<rest>.*)"),
        "rest",
        "Fix the syntax error reported in the traceback, then retry.",
    ),
    (
        ErrorCategory.TEST_FAILURE,
        re.compile(r"(FAILED|AssertionError|assert |\d+ failed)(?P<rest>.*)"),
        "rest",
        "Adjust the code (or the test) so the assertion holds, then re-run tests.",
    ),
    (
        ErrorCategory.RUNTIME,
        re.compile(r"(?P<exc>\w*Error|Exception|Traceback)(?P<rest>.*)"),
        "rest",
        "Diagnose the runtime exception from the traceback and fix the cause.",
    ),
]

_SECURITY_RE = re.compile(r"(secret|api[_-]?key|password|token)\s*[:=]\s*\S+", re.IGNORECASE)


def classify_error(stderr: str, stdout: str = "", *, timed_out: bool = False) -> ClassifiedError:
    """Classify a failure from its logs."""
    if timed_out:
        return ClassifiedError(
            category=ErrorCategory.TIMEOUT,
            detail="Execution timed out",
            fix_strategy="Reduce work or increase the timeout; check for an infinite loop.",
        )

    text = f"{stderr}\n{stdout}"

    if _SECURITY_RE.search(text):
        return ClassifiedError(
            category=ErrorCategory.SECURITY,
            detail="Possible secret leaked in output",
            fix_strategy="Remove the secret and use an environment variable.",
            retryable=False,
        )

    for category, pattern, group, strategy in _RULES:
        m = pattern.search(text)
        if m:
            try:
                hint = (m.group(group) or "").strip()
            except IndexError:
                hint = ""
            return ClassifiedError(
                category=category,
                detail=m.group(0)[:200],
                hint=hint,
                fix_strategy=strategy,
            )

    return ClassifiedError(
        category=ErrorCategory.UNKNOWN,
        detail=(stderr or stdout)[:200],
        fix_strategy="Inspect the logs and attempt a targeted fix.",
    )
