from __future__ import annotations

import gzip
import hashlib
import http.cookiejar
import json
from dataclasses import asdict, dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qsl, quote, urlencode, urljoin, urlsplit, urlunsplit
from urllib.request import HTTPCookieProcessor, Request, build_opener

BASE_URL = "https://coa.ascensionlogs.gg"
CHARACTER = "Gunspojoshe"
REALM = "Vol'Jin"
TIMEOUT_SECONDS = 20.0
MAX_RESPONSE_BYTES = 2 * 1024 * 1024

BROWSER_HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/138.0.0.0 Safari/537.36"
    ),
}

FETCH_CONTEXT_HEADERS = {
    **BROWSER_HEADERS,
    "Referer": f"{BASE_URL}/",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
}

ENDPOINTS = {
    "reports_public_control": (
        "/api/reports/public?"
        + urlencode(
            {
                "page": "1",
                "limit": "1",
                "sortBy": "created_at",
                "sortOrder": "desc",
            }
        )
    ),
    "character_search": ("/api/characters/search?" + urlencode({"q": CHARACTER, "limit": "20"})),
    "armory_by_name": (
        f"/api/armory/by-name/{quote(CHARACTER, safe='')}?" + urlencode({"realm": REALM})
    ),
}

BOOTSTRAPS = {
    "none": None,
    "home": "/",
    "armory_page": f"/armory/{quote(CHARACTER, safe='')}/{quote(REALM, safe='')}",
    "character_page": (
        f"/characters/{quote(CHARACTER, safe='')}/{quote(REALM, safe='')}?"
        + urlencode(
            {
                "phase": "0",
                "location": "World Bosses",
                "difficulty": "normal",
                "spec": "Tyrant",
            }
        )
    ),
}


@dataclass(frozen=True, slots=True)
class ProbeResult:
    variant: str
    endpoint: str
    route: str
    bootstrap_status: int | None
    cookie_count: int
    status: int | None
    bytes_uncompressed: int
    payload_hash: str | None
    content_type: str | None
    top_level_kind: str | None
    top_level_keys: tuple[str, ...]
    response_header_names: tuple[str, ...]
    error: str | None


def _sanitized_route(url: str) -> str:
    parts = urlsplit(url)
    query = "&".join(
        f"{key}=<value>" for key, _value in parse_qsl(parts.query, keep_blank_values=True)
    )
    return urlunsplit(("", "", parts.path or "/", query, ""))


def _decode_body(body: bytes, content_encoding: str | None) -> bytes:
    if content_encoding and content_encoding.casefold() == "gzip":
        try:
            return gzip.decompress(body)
        except (OSError, EOFError):
            return body
    return body


def _read_response(response: Any) -> tuple[int | None, str | None, bytes, tuple[str, ...]]:
    status = int(getattr(response, "status", response.getcode()))
    headers = response.headers
    content_type = headers.get_content_type() if headers else None
    header_names = (
        tuple(sorted({str(name).casefold() for name in headers.keys()})) if headers else ()
    )
    body = response.read(MAX_RESPONSE_BYTES + 1)
    if len(body) > MAX_RESPONSE_BYTES:
        body = body[:MAX_RESPONSE_BYTES]
    body = _decode_body(body, headers.get("Content-Encoding") if headers else None)
    return status, content_type, body, header_names


def _request(
    opener: Any,
    url: str,
    *,
    headers: dict[str, str],
) -> tuple[int | None, str | None, bytes, tuple[str, ...], str | None]:
    request = Request(url, headers=headers, method="GET")
    try:
        with opener.open(request, timeout=TIMEOUT_SECONDS) as response:
            status, content_type, body, header_names = _read_response(response)
            return status, content_type, body, header_names, None
    except HTTPError as exc:
        content_type = exc.headers.get_content_type() if exc.headers else None
        header_names = (
            tuple(sorted({str(name).casefold() for name in exc.headers.keys()}))
            if exc.headers
            else ()
        )
        body = exc.read(MAX_RESPONSE_BYTES + 1)
        if len(body) > MAX_RESPONSE_BYTES:
            body = body[:MAX_RESPONSE_BYTES]
        body = _decode_body(body, exc.headers.get("Content-Encoding") if exc.headers else None)
        return exc.code, content_type, body, header_names, f"HTTP {exc.code}: {exc.reason}"
    except URLError as exc:
        return None, None, b"", (), f"network error: {exc.reason}"
    except TimeoutError:
        return None, None, b"", (), "read timeout"


def _inspect_json(body: bytes) -> tuple[str | None, tuple[str, ...]]:
    if not body:
        return None, ()
    try:
        payload = json.loads(body)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return "non_json", ()
    if isinstance(payload, dict):
        return "object", tuple(sorted(str(key) for key in payload))
    if isinstance(payload, list):
        return "array", ()
    if payload is None:
        return "null", ()
    return type(payload).__name__, ()


def _probe_variant(
    *,
    variant: str,
    headers: dict[str, str],
    bootstrap_path: str | None,
) -> list[ProbeResult]:
    cookie_jar = http.cookiejar.CookieJar()
    opener = build_opener(HTTPCookieProcessor(cookie_jar))
    bootstrap_status: int | None = None
    if bootstrap_path:
        bootstrap_url = urljoin(f"{BASE_URL}/", bootstrap_path.lstrip("/"))
        bootstrap_headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": headers.get("Accept-Language", "en-US,en;q=0.9"),
            "User-Agent": headers.get("User-Agent", "Python-urllib/3.12"),
        }
        bootstrap_status, _content_type, _body, _header_names, _error = _request(
            opener,
            bootstrap_url,
            headers=bootstrap_headers,
        )

    results: list[ProbeResult] = []
    for endpoint_name, endpoint_path in ENDPOINTS.items():
        url = urljoin(f"{BASE_URL}/", endpoint_path.lstrip("/"))
        status, content_type, body, header_names, error = _request(
            opener,
            url,
            headers=headers,
        )
        top_level_kind, top_level_keys = _inspect_json(body)
        results.append(
            ProbeResult(
                variant=variant,
                endpoint=endpoint_name,
                route=_sanitized_route(url),
                bootstrap_status=bootstrap_status,
                cookie_count=sum(1 for _cookie in cookie_jar),
                status=status,
                bytes_uncompressed=len(body),
                payload_hash=hashlib.sha256(body).hexdigest() if body else None,
                content_type=content_type,
                top_level_kind=top_level_kind,
                top_level_keys=top_level_keys,
                response_header_names=header_names,
                error=error,
            )
        )
    return results


def main() -> int:
    variants: list[tuple[str, dict[str, str], str | None]] = [
        ("plain", {"Accept": "application/json"}, None),
        ("browser_headers", BROWSER_HEADERS, None),
        ("fetch_context", FETCH_CONTEXT_HEADERS, None),
    ]
    variants.extend(
        (
            f"fetch_context_after_{bootstrap_name}",
            FETCH_CONTEXT_HEADERS,
            bootstrap_path,
        )
        for bootstrap_name, bootstrap_path in BOOTSTRAPS.items()
        if bootstrap_path is not None
    )

    results: list[ProbeResult] = []
    for variant, headers, bootstrap_path in variants:
        results.extend(
            _probe_variant(
                variant=variant,
                headers=headers,
                bootstrap_path=bootstrap_path,
            )
        )

    payload = {
        "schema_version": 1,
        "tls_context": "python_default",
        "results": [asdict(result) for result in results],
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))

    control_results = [result for result in results if result.endpoint == "reports_public_control"]
    return 0 if any(result.status == 200 for result in control_results) else 4


if __name__ == "__main__":
    raise SystemExit(main())
