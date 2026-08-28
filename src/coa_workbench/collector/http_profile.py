from __future__ import annotations

import http.cookiejar
import ssl
from dataclasses import dataclass
from typing import Any, Callable
from urllib.parse import urlsplit
from urllib.request import HTTPCookieProcessor, HTTPSHandler, Request, build_opener

OpenUrl = Callable[..., Any]
FETCH_CONTEXT_PROFILE_VERSION = "coa-fetch-context-v1"


@dataclass(frozen=True, slots=True)
class HttpRequestProfile:
    version: str
    headers: tuple[tuple[str, str], ...]

    @property
    def header_names(self) -> tuple[str, ...]:
        return tuple(name for name, _value in self.headers)

    def as_headers(self) -> dict[str, str]:
        return dict(self.headers)


COA_FETCH_CONTEXT_V1 = HttpRequestProfile(
    version=FETCH_CONTEXT_PROFILE_VERSION,
    headers=(
        ("Accept", "application/json, text/plain, */*"),
        ("Accept-Language", "en-US,en;q=0.9"),
        ("Cache-Control", "no-cache"),
        ("Pragma", "no-cache"),
        (
            "User-Agent",
            (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/138.0.0.0 Safari/537.36"
            ),
        ),
        ("Referer", "https://coa.ascensionlogs.gg/"),
        ("Sec-Fetch-Dest", "empty"),
        ("Sec-Fetch-Mode", "cors"),
        ("Sec-Fetch-Site", "same-origin"),
    ),
)


def _normalized_origin(url: str) -> tuple[str, str, int]:
    parts = urlsplit(url)
    scheme = parts.scheme.casefold()
    hostname = parts.hostname.casefold() if parts.hostname else ""
    if scheme not in {"http", "https"} or not hostname:
        raise ValueError("HTTP session URL must contain an http(s) origin")
    if parts.username or parts.password:
        raise ValueError("HTTP session URL must not contain credentials")
    port = parts.port
    if port is None:
        port = 443 if scheme == "https" else 80
    return scheme, hostname, port


class SameOriginHttpSession:
    """Versioned same-origin HTTP session with an in-memory cookie jar."""

    def __init__(
        self,
        base_url: str,
        *,
        profile: HttpRequestProfile = COA_FETCH_CONTEXT_V1,
        opener: OpenUrl | Any | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.profile = profile
        self._origin = _normalized_origin(self.base_url)
        self._cookie_jar = http.cookiejar.CookieJar()
        if opener is None:
            handlers: list[Any] = [HTTPCookieProcessor(self._cookie_jar)]
            if self._origin[0] == "https":
                handlers.insert(0, HTTPSHandler(context=ssl.create_default_context()))
            self._opener: OpenUrl | Any = build_opener(*handlers)
        else:
            self._opener = opener

    @property
    def cookie_count(self) -> int:
        return sum(1 for _cookie in self._cookie_jar)

    def _validate_same_origin(self, url: str) -> None:
        if _normalized_origin(url) != self._origin:
            raise ValueError("HTTP session refuses a cross-origin request")

    def build_request(self, url: str, *, method: str = "GET") -> Request:
        self._validate_same_origin(url)
        return Request(url, headers=self.profile.as_headers(), method=method)

    def open(
        self,
        request: Request,
        *,
        timeout: float,
        context: ssl.SSLContext | None = None,
    ) -> Any:
        self._validate_same_origin(request.full_url)
        target = getattr(self._opener, "open", self._opener)
        return target(request, timeout=timeout)

    def safe_request_metadata(self, request: Request) -> dict[str, Any]:
        return {
            "http_profile_version": self.profile.version,
            "http_profile_header_names": list(self.profile.header_names),
            "request_header_names": sorted(request.headers),
        }
