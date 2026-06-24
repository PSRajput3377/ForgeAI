"""Rate-limit backoff and pagination, tested with httpx.MockTransport (no network)."""

import httpx
import pytest
from github.rest_support import (
    paginate,
    parse_next_link,
    request_with_backoff,
    retry_after_seconds,
)


def test_parse_next_link():
    header = (
        '<https://api.github.com/x?page=2>; rel="next", '
        '<https://api.github.com/x?page=5>; rel="last"'
    )
    assert parse_next_link(header) == "https://api.github.com/x?page=2"
    assert parse_next_link(None) is None
    assert parse_next_link('<...>; rel="last"') is None


def test_retry_after_header_seconds():
    resp = httpx.Response(429, headers={"Retry-After": "30"})
    assert retry_after_seconds(resp) == 30.0


def test_retry_after_from_ratelimit_reset():
    resp = httpx.Response(403, headers={"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": "100"})
    assert retry_after_seconds(resp, now=40.0) == 60.0


def test_non_ratelimit_response_returns_none():
    assert retry_after_seconds(httpx.Response(200)) is None
    assert retry_after_seconds(httpx.Response(404)) is None


@pytest.mark.asyncio
async def test_backoff_retries_then_succeeds():
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] < 3:
            return httpx.Response(429, headers={"Retry-After": "5"})
        return httpx.Response(200, json={"ok": True})

    slept: list[float] = []

    async def fake_sleep(s):
        slept.append(s)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url="https://api.github.com") as client:
        resp = await request_with_backoff(client, "GET", "/rate", sleep=fake_sleep)

    assert resp.status_code == 200
    assert calls["n"] == 3
    assert slept == [5.0, 5.0]  # backed off twice before success


@pytest.mark.asyncio
async def test_backoff_gives_up_after_max_retries():
    def handler(request):
        return httpx.Response(429, headers={"Retry-After": "1"})

    async def fake_sleep(s):
        pass

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url="https://api.github.com") as client:
        resp = await request_with_backoff(client, "GET", "/rate", max_retries=2, sleep=fake_sleep)
    assert resp.status_code == 429  # returns the last response, doesn't loop forever


@pytest.mark.asyncio
async def test_pagination_follows_next_links():
    pages = {
        "/items": ([1, 2], '<https://api.github.com/items?page=2>; rel="next"'),
        "/items?page=2": ([3, 4], '<https://api.github.com/items?page=3>; rel="next"'),
        "/items?page=3": ([5], None),
    }

    def handler(request: httpx.Request) -> httpx.Response:
        key = request.url.raw_path.decode()
        body, link = pages[key]
        headers = {"Link": link} if link else {}
        return httpx.Response(200, json=body, headers=headers)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url="https://api.github.com") as client:
        items = await paginate(client, "/items")
    assert items == [1, 2, 3, 4, 5]
