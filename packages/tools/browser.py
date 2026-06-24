"""BrowserTool — read-only web access (visit, extract HTML/text).

Initial version is read-only and uses httpx (no JS execution). Click/forms/login
via Playwright come later. Requires the NETWORK permission, which is not granted
by default.
"""

from __future__ import annotations

import re

import httpx

from tools.base import Permission, Tool, ToolErrorCode, ToolInput, ToolResult

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")


class BrowserTool(Tool):
    name = "browser"
    description = "Read-only web access: visit a URL and extract HTML or text."

    def __init__(self, timeout: float = 20.0):
        self.timeout = timeout

    def permission_for(self, action: str) -> Permission | None:
        return Permission.NETWORK

    async def execute(self, tool_input: ToolInput) -> ToolResult:
        action = tool_input.action
        if action not in {"visit", "extract_text", "extract_html"}:
            return self._unknown_action(action)
        url = tool_input.args.get("url")
        if not url:
            return ToolResult.fail(
                self.name, ToolErrorCode.INVALID_INPUT, "Missing url"
            )
        if not url.startswith(("http://", "https://")):
            return ToolResult.fail(
                self.name, ToolErrorCode.INVALID_INPUT, "url must be http(s)"
            )

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout, follow_redirects=True
            ) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                html = resp.text
        except httpx.TimeoutException:
            return ToolResult.fail(
                self.name, ToolErrorCode.TIMEOUT, "Request timed out", retryable=True
            )
        except httpx.HTTPError as exc:
            return ToolResult.fail(
                self.name, ToolErrorCode.EXECUTION_FAILED, str(exc), retryable=True
            )

        if action == "extract_text" or action == "visit":
            text = _WS_RE.sub(" ", _TAG_RE.sub(" ", html)).strip()
            return ToolResult.ok(self.name, output=text, status_code=resp.status_code)
        return ToolResult.ok(self.name, output=html, status_code=resp.status_code)
