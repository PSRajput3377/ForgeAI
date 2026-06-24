"""Resilience helpers for the real GitHub REST API: rate-limit backoff + pagination.

GitHub returns 403/429 with `Retry-After` / `X-RateLimit-Reset` when limits are
hit, and paginates large collections via `Link: ...rel="next"`. Fake providers
never exercise these paths, so they are isolated here and unit-tested with a
mock transport.
"""

from __future__ import annotations

import asyncio
import re

import httpx

_NEXT_LINK_RE = re.compile(r'<([^>]+)>;\s*rel="next"')


def parse_next_link(link_header: str | None) -> str | None:
    """Return the `rel="next"` URL from a GitHub Link header, or None."""
    if not link_header:
        return None
    m = _NEXT_LINK_RE.search(link_header)
    return m.group(1) if m else None


def retry_after_seconds(response: httpx.Response, *, now: float = 0.0) -> float | None:
    """Compute how long to wait from a rate-limited response.

    Prefers `Retry-After` (seconds); falls back to `X-RateLimit-Reset` (epoch)
    minus ``now``. Returns None if the response isn't a rate-limit signal.
    """
    if response.status_code not in (403, 429):
        return None
    retry_after = response.headers.get("Retry-After")
    if retry_after is not None:
        try:
            return max(0.0, float(retry_after))
        except ValueError:
            pass
    remaining = response.headers.get("X-RateLimit-Remaining")
    reset = response.headers.get("X-RateLimit-Reset")
    if remaining == "0" and reset is not None:
        try:
            return max(0.0, float(reset) - now)
        except ValueError:
            pass
    return None


async def request_with_backoff(
    client: httpx.AsyncClient,
    method: str,
    url: str,
    *,
    max_retries: int = 5,
    sleep=asyncio.sleep,
    clock=lambda: 0.0,
    **kwargs,
) -> httpx.Response:
    """Issue a request, backing off and retrying on 403/429 rate limits.

    ``sleep`` and ``clock`` are injectable so tests run instantly and
    deterministically.
    """
    attempt = 0
    while True:
        response = await client.request(method, url, **kwargs)
        wait = retry_after_seconds(response, now=clock())
        if wait is None or attempt >= max_retries:
            return response
        await sleep(wait)
        attempt += 1


async def paginate(
    client: httpx.AsyncClient,
    url: str,
    *,
    max_pages: int = 100,
    **kwargs,
) -> list:
    """Follow `rel="next"` links, concatenating JSON array pages.

    Bounds at ``max_pages`` to avoid runaway loops; logs nothing silently —
    callers can compare len() against expectations.
    """
    items: list = []
    pages = 0
    next_url: str | None = url
    while next_url and pages < max_pages:
        response = await request_with_backoff(client, "GET", next_url, **kwargs)
        response.raise_for_status()
        page = response.json()
        if isinstance(page, list):
            items.extend(page)
        else:
            items.append(page)
        next_url = parse_next_link(response.headers.get("Link"))
        kwargs.pop("params", None)  # params only apply to the first request
        pages += 1
    return items
