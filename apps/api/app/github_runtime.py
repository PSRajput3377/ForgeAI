"""Wiring between the FastAPI app and the GitHub integration.

Selects the GitHub provider from configuration: a real ``RestGitHubProvider``
when ``GITHUB_TOKEN`` is set, otherwise the offline ``FakeGitHubProvider`` so the
platform still runs (and demos) with no credentials.

This is the seam that turns the Phase 8 design into a live integration without
touching agent or workflow code (ADR-0019).
"""

from __future__ import annotations

from github.manager import GitHubManager
from github.provider import FakeGitHubProvider, GitHubProvider
from github.rest_provider import RestGitHubProvider

from app.config import settings


def github_configured() -> bool:
    """True if a real GitHub token is configured."""
    return bool(settings.github_token)


def build_provider() -> GitHubProvider:
    """Return the live provider when a token is set, else the offline fake."""
    if github_configured():
        return RestGitHubProvider(token=settings.github_token, api_url=settings.github_api_url)
    return FakeGitHubProvider()


def build_manager(max_ci_retries: int = 3) -> GitHubManager:
    """Assemble a GitHubManager over the configured provider."""
    return GitHubManager(build_provider(), max_ci_retries=max_ci_retries)
