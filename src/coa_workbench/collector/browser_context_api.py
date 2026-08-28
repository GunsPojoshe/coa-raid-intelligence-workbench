from __future__ import annotations

import time
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator, Mapping
from urllib.error import URLError
from urllib.parse import urlsplit
from urllib.request import Request

from coa_workbench.collector.browser_observatory import (
    BROWSER_RUNTIME_REQUIREMENT,
    PlaywrightUnavailableError,
)

_BROWSER_CONTEXT_API_VERSION = "browser-context-api-v1"
_EDGE_CHALLENGE_MARKERS = (
    "challenges.cloudflare.com",
    "/cdn-cgi/challenge-platform/",
)
_FETCH_SCRIPT = """
async (url) => {
  try {
    const response = await fetch(url, {
      method: 'GET',
      headers: {'Accept': 'application/json'},
      credentials: 'include',
      cache: 'no-store',
      redirect: 'follow'
    });
    return {
      ok: true,
      status: response.status,
      contentType: response.headers.get('content-type'),
      body: await response.text()
    };
  } catch (error) {
    return {
      ok: false,
      error: String(error)
    };
  }
}
"""


class _ResponseHeaders:
    def __init__(self, content_type: str | None) -> None:
        self._content_type = content_type

    def get_content_type(self) -> str | None:
        if not self._content_type:
            return None
        return self._content_type.split(";", 1)[0].strip() or None


class _BufferedResponse:
    def __init__(self, *, status: int, content_type: str | None, body: bytes) -> None:
        self.status = status
        self.headers = _ResponseHeaders(content_type)
        self._body = body
        self._offset = 0

    def __enter__(self) -> _BufferedResponse:
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        return None

    def read1(self, size: int) -> bytes:
        if size < 1 or self._offset >= len(self._body):
            return b""
        end = min(self._offset + size, len(self._body))
        chunk = self._body[self._offset : end]
        self._offset = end
        return chunk


@dataclass(frozen=True, slots=True)
class BrowserContextApiConfig:
    start_url: str
    allowed_host: str
    user_data_dir: Path
    navigation_timeout_seconds: float = 45.0
    clearance_timeout_seconds: float = 120.0

    def validate(self) -> None:
        parts = urlsplit(self.start_url)
        if parts.scheme != "https" or parts.hostname != self.allowed_host:
            raise ValueError("start_url must be HTTPS and match allowed_host")
        if self.navigation_timeout_seconds <= 0:
            raise ValueError("navigation_timeout_seconds must be greater than zero")
        if self.clearance_timeout_seconds <= 0:
            raise ValueError("clearance_timeout_seconds must be greater than zero")


class BrowserPageUrlOpener:
    """urllib-style opener backed by same-origin fetch() in an already-open browser page."""

    def __init__(self, page: Any, *, allowed_host: str) -> None:
        self.page = page
        self.allowed_host = allowed_host

    def __call__(self, request: Request, **_kwargs: object) -> _BufferedResponse:
        if request.get_method().upper() != "GET":
            raise URLError("browser-context API transport only supports GET")
        parts = urlsplit(request.full_url)
        if parts.scheme != "https" or parts.hostname != self.allowed_host:
            raise URLError("browser-context API request must stay on the allowed HTTPS host")

        result = self.page.evaluate(_FETCH_SCRIPT, request.full_url)
        if not isinstance(result, Mapping):
            raise URLError("browser-context API fetch returned an invalid result")
        if result.get("ok") is not True:
            raise URLError(str(result.get("error") or "browser-context API fetch failed"))

        try:
            status = int(result.get("status"))
        except (TypeError, ValueError) as exc:
            raise URLError("browser-context API fetch returned an invalid status") from exc
        content_type_raw = result.get("contentType")
        content_type = str(content_type_raw) if content_type_raw else None
        body_raw = result.get("body")
        if body_raw is None:
            raise URLError("browser-context API fetch returned no response body")
        body = str(body_raw).encode("utf-8")
        return _BufferedResponse(status=status, content_type=content_type, body=body)


def _load_sync_playwright() -> Any:
    try:
        from playwright.sync_api import sync_playwright
    except ModuleNotFoundError as exc:
        raise PlaywrightUnavailableError(
            "Browser-context API acquisition requires Playwright. Use the ephemeral runtime with "
            f"uv run --with '{BROWSER_RUNTIME_REQUIREMENT}' and install Chromium with "
            f"uv run --with '{BROWSER_RUNTIME_REQUIREMENT}' playwright install chromium."
        ) from exc
    return sync_playwright


def _managed_edge_challenge_visible(page: Any) -> bool:
    try:
        title = str(page.title() or "").casefold()
        body = str(page.content() or "").casefold()
    except Exception:
        return False
    if "just a moment" in title:
        return True
    return all(marker in body for marker in _EDGE_CHALLENGE_MARKERS)


def _wait_for_browser_clearance(page: Any, *, timeout_seconds: float) -> None:
    deadline = time.monotonic() + timeout_seconds
    announced = False
    while _managed_edge_challenge_visible(page):
        if not announced:
            print(
                "Browser challenge detected. Complete it in the opened browser window; "
                "API acquisition will continue automatically."
            )
            announced = True
        if time.monotonic() >= deadline:
            raise TimeoutError(
                f"browser challenge was not cleared within {timeout_seconds:g} seconds"
            )
        page.wait_for_timeout(1000)


@contextmanager
def browser_context_url_opener(
    config: BrowserContextApiConfig,
) -> Iterator[BrowserPageUrlOpener]:
    """Open a headed persistent browser context without HAR/trace and yield an API opener."""

    config.validate()
    config.user_data_dir.mkdir(parents=True, exist_ok=True)
    sync_playwright = _load_sync_playwright()

    with sync_playwright() as playwright:
        context = playwright.chromium.launch_persistent_context(
            config.user_data_dir,
            headless=False,
            no_viewport=True,
        )
        try:
            page = context.pages[0] if context.pages else context.new_page()
            page.goto(
                config.start_url,
                wait_until="domcontentloaded",
                timeout=config.navigation_timeout_seconds * 1000,
            )
            _wait_for_browser_clearance(
                page,
                timeout_seconds=config.clearance_timeout_seconds,
            )
            yield BrowserPageUrlOpener(page, allowed_host=config.allowed_host)
        finally:
            context.close()


__all__ = [
    "BrowserContextApiConfig",
    "BrowserPageUrlOpener",
    "browser_context_url_opener",
]
