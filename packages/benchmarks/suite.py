"""The versioned benchmark suite — representative scenarios with expectations.

A fixed, versioned set of requests covering the kinds of work ForgeAI does, each
with an expected outcome to check against (spec §5). Bumping ``SUITE_VERSION``
when scenarios change keeps results comparable: a result is only meaningfully
compared against others from the same suite version.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel

SUITE_VERSION = "v1"


class Category(StrEnum):
    """The kind of engineering task a scenario exercises."""

    ADD_FEATURE = "add_feature"
    FIX_BUG = "fix_bug"
    REFACTOR = "refactor"
    WRITE_TESTS = "write_tests"
    CREATE_API = "create_api"


class Scenario(BaseModel):
    """One benchmark case: a request plus what a good run should achieve."""

    id: str
    name: str
    category: Category
    request: str
    expect_success: bool = True  # the run should end APPROVED
    max_retries: int = 2  # a good run should finish within this many retries


SUITE: list[Scenario] = [
    Scenario(
        id="add-feature-dark-mode",
        name="Add a feature",
        category=Category.ADD_FEATURE,
        request="Add a dark-mode toggle to the settings page",
    ),
    Scenario(
        id="fix-bug-null-deref",
        name="Fix a bug",
        category=Category.FIX_BUG,
        request="Fix the null pointer error when loading an empty project",
    ),
    Scenario(
        id="refactor-auth-module",
        name="Refactor a module",
        category=Category.REFACTOR,
        request="Refactor the auth module to extract token handling into its own service",
    ),
    Scenario(
        id="write-tests-payments",
        name="Write tests",
        category=Category.WRITE_TESTS,
        request="Write unit tests for the payments calculator",
    ),
    Scenario(
        id="create-api-crud-todos",
        name="Create an API",
        category=Category.CREATE_API,
        request="Create a CRUD REST API for todo items",
    ),
]
