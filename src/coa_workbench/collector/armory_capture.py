from __future__ import annotations

import json
import re
import ssl
from dataclasses import dataclass
from datetime import datetime, timezone
from html.parser import HTMLParser
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode, urljoin, urlsplit
from urllib.request import Request, urlopen

from .raw_archive import (
    RawArchive,
    RawCapture,
    capture_to_dict,
    request_key_from_url,
    sanitize_url,
)
from .source_registry import SourceRegistry

OpenUrl = Callable[..., Any]
_MAX_ASSET_COUNT = 32
_MAX_ASSET_BYTES = 16 * 1024 * 1024
_API_ROUTE_PATTERN = re.compile(
    r"(?:https://coa\.ascensionlogs\.gg)?"
    r"(/api/[A-Za-z0-9_./?=&%${}:+\-]+)"
)


@dataclass(frozen=True, slots=True)
class EmbeddedJsonCapture:
    script_index: int
    script_id: str | None
    script_type: str | None
    capture: RawCapture


@dataclass(frozen=True, slots=True)
class BuildAssetCapture:
    url: str
    asset_kind: str
    status: int | None
    content_type: str | None
    capture: RawCapture | None
    api_route_candidates: tuple[str, ...]
    error: str | None


@dataclass(frozen=True, slots=True)
class BuildPageCapture:
    page_kind: str
    url: str
    status: int | None
    content_type: str | None
    capture: RawCapture | None
    embedded_json: tuple[EmbeddedJsonCapture, ...]
    assets: tuple[BuildAssetCapture, ...]
    error: str | None


class _BuildHtmlParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self._inside_script = False
        self._attrs: dict[str, str | None] = {}
        self._parts: list[str] = []
        self.scripts: list[tuple[dict[str, str | None], str]] = []
        self.links: list[dict[str, str | None]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        prepared = {str(key).casefold(): value for key, value in attrs}
        lowered = tag.casefold()
        if lowered == "script" and not self._inside_script:
            self._inside_script = True
            self._attrs = prepared
            self._parts = []
        elif lowered == "link":
            self.links.append(prepared)

    def handle_data(self, data: str) -> None:
        if self._inside_script:
            self._parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.casefold() != "script" or not self._inside_script:
            return
        self.scripts.append((self._attrs, "".join(self._parts)))
        self._inside_script = False
        self._attrs = {}
        self._parts = []


def _required_segment(value: str, label: str) -> str:
    prepared = value.strip()
    if not prepared:
        raise ValueError(f"{label} cannot be empty")
    if len(prepared) > 120:
        raise ValueError(f"{label} is too long")
    return quote(prepared, safe="")


def build_armory_url(base_url: str, *, character: str, realm: str) -> str:
    path = f"/armory/{_required_segment(character, 'character')}/{_required_segment(realm, 'realm')}"
    return urljoin(f"{base_url.rstrip('/')}/", path.lstrip("/"))


def build_character_url(
    base_url: str,
    *,
    character: str,
    realm: str,
    phase: int = 0,
    location: str = "World Bosses",
    difficulty: str = "normal",
    spec: str | None = None,
) -> str:
    path = (
        f"/characters/{_required_segment(character, 'character')}/"
        f"{_required_segment(realm, 'realm')}"
    )
    query_values: list[tuple[str, str]] = [
        ("phase", str(phase)),
        ("location", location),
        ("difficulty", difficulty),
    ]
    if spec and spec.strip():
        query_values.append(("spec", spec.strip()))
    return urljoin(f"{base_url.rstrip('/')}/", path.lstrip("/")) + "?" + urlencode(query_values)


def _parse_html(body: bytes) -> _BuildHtmlParser | None:
    try:
        text = body.decode("utf-8")
    except UnicodeDecodeError:
        return None
    parser = _BuildHtmlParser()
    parser.feed(text)
    return parser


def _json_scripts(
    parser: _BuildHtmlParser | None,
) -> list[tuple[int, dict[str, str | None], bytes]]:
    if parser is None:
        return []
    result: list[tuple[int, dict[str, str | None], bytes]] = []
    for index, (attrs, script_text) in enumerate(parser.scripts):
        candidate = script_text.strip()
        if not candidate:
            continue
        script_type = (attrs.get("type") or "").casefold()
        script_id = (attrs.get("id") or "").casefold()
        explicitly_json = "json" in script_type or script_id in {
            "__next_data__",
            "__nuxt_data__",
            "__sveltekit_data__",
        }
        if not explicitly_json and candidate[:1] not in {"{", "["}:
            continue
        try:
            json.loads(candidate)
        except json.JSONDecodeError:
            continue
        result.append((index, attrs, candidate.encode("utf-8")))
    return result


def _asset_urls(
    parser: _BuildHtmlParser | None,
    *,
    page_url: str,
    base_url: str,
) -> list[tuple[str, str]]:
    if parser is None:
        return []
    source_host = urlsplit(base_url).hostname
    candidates: list[tuple[str, str]] = []
    for attrs, _script_text in parser.scripts:
        source = attrs.get("src")
        if source:
            candidates.append(("script", urljoin(page_url, source)))
    for attrs in parser.links:
        relationship = (attrs.get("rel") or "").casefold()
        reference = attrs.get("href")
        if reference and relationship in {"modulepreload", "preload"}:
            candidates.append((relationship, urljoin(page_url, reference)))

    result: list[tuple[str, str]] = []
    seen: set[str] = set()
    for kind, url in candidates:
        parts = urlsplit(url)
        if parts.hostname != source_host or parts.scheme != "https":
            continue
        if url in seen:
            continue
        seen.add(url)
        result.append((kind, url))
        if len(result) >= _MAX_ASSET_COUNT:
            break
    return result


def _api_route_candidates(body: bytes) -> tuple[str, ...]:
    text = body.decode("utf-8", errors="ignore").replace("\\/", "/")
    candidates: set[str] = set()
    for match in _API_ROUTE_PATTERN.finditer(text):
        candidate = match.group(1).rstrip(".,;:)]}")
        if len(candidate) > 240:
            continue
        candidates.add(sanitize_url(candidate))
        if len(candidates) >= 200:
            break
    return tuple(sorted(candidates))


def _read_response(
    request: Request,
    *,
    timeout_seconds: float,
    opener: OpenUrl,
    max_bytes: int | None = None,
) -> tuple[int | None, str | None, bytes | None, str | None]:
    status: int | None = None
    content_type: str | None = None
    body: bytes | None = None
    error: str | None = None
    try:
        with opener(
            request,
            timeout=timeout_seconds,
            context=ssl.create_default_context(),
        ) as response:
            status = int(response.status)
            content_type = response.headers.get_content_type()
            body = response.read(max_bytes + 1) if max_bytes is not None else response.read()
            if max_bytes is not None and len(body) > max_bytes:
                return status, content_type, None, f"response exceeded {max_bytes} bytes"
    except HTTPError as exc:
        status = exc.code
        content_type = exc.headers.get_content_type() if exc.headers else None
        body = exc.read(max_bytes + 1) if max_bytes is not None else exc.read()
        if max_bytes is not None and len(body) > max_bytes:
            body = None
        error = f"HTTP {exc.code}: {exc.reason}"
    except URLError as exc:
        error = f"network error: {exc.reason}"
    return status, content_type, body, error


def _capture_asset(
    *,
    registry: SourceRegistry,
    archive: RawArchive,
    parent_capture: RawCapture,
    page_kind: str,
    asset_kind: str,
    url: str,
    timeout_seconds: float,
    opener: OpenUrl,
) -> BuildAssetCapture:
    request = Request(
        url,
        headers={
            "Accept": "application/javascript,text/javascript,*/*;q=0.1",
            "User-Agent": "CoA-Raid-Intelligence-Workbench/0.1 armory-asset-capture",
        },
        method="GET",
    )
    status, content_type, body, error = _read_response(
        request,
        timeout_seconds=timeout_seconds,
        opener=opener,
        max_bytes=_MAX_ASSET_BYTES,
    )
    if body is None:
        return BuildAssetCapture(url, asset_kind, status, content_type, None, (), error)
    capture = archive.capture_bytes(
        body,
        source_code=registry.source_code,
        endpoint_code="build_page_asset",
        request_key=request_key_from_url("GET", url),
        fetched_at=datetime.now(timezone.utc),
        http_status=status,
        content_type=content_type,
        request_url=url,
        metadata={
            "capture_mode": "autonomous_build_asset",
            "asset_kind": asset_kind,
            "discovered_from_page_kind": page_kind,
            "parent_payload_hash": parent_capture.payload_hash,
            "request_header_names": sorted(request.headers),
        },
    )
    return BuildAssetCapture(
        url=url,
        asset_kind=asset_kind,
        status=status,
        content_type=content_type,
        capture=capture,
        api_route_candidates=_api_route_candidates(body),
        error=error,
    )


def _capture_one_page(
    *,
    registry: SourceRegistry,
    archive: RawArchive,
    page_kind: str,
    url: str,
    timeout_seconds: float,
    opener: OpenUrl,
    asset_cache: dict[str, BuildAssetCapture],
) -> BuildPageCapture:
    if urlsplit(url).hostname != urlsplit(registry.base_url).hostname:
        raise ValueError("build page URL escaped the configured source host")
    request = Request(
        url,
        headers={
            "Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.1",
            "User-Agent": "CoA-Raid-Intelligence-Workbench/0.1 armory-capture",
        },
        method="GET",
    )
    status, content_type, body, error = _read_response(
        request,
        timeout_seconds=timeout_seconds,
        opener=opener,
    )
    if body is None:
        return BuildPageCapture(page_kind, url, status, content_type, None, (), (), error)

    observed_at = datetime.now(timezone.utc)
    page_capture = archive.capture_bytes(
        body,
        source_code=registry.source_code,
        endpoint_code=f"{page_kind}_html",
        request_key=request_key_from_url("GET", url),
        fetched_at=observed_at,
        http_status=status,
        content_type=content_type,
        request_url=url,
        metadata={
            "capture_mode": "autonomous_build_page",
            "page_kind": page_kind,
            "request_header_names": sorted(request.headers),
        },
    )
    parser = _parse_html(body)
    embedded: list[EmbeddedJsonCapture] = []
    for script_index, attrs, json_body in _json_scripts(parser):
        script_capture = archive.capture_bytes(
            json_body,
            source_code=registry.source_code,
            endpoint_code=f"{page_kind}_embedded_json",
            request_key=f"{page_capture.request_key}:script:{script_index}",
            fetched_at=observed_at,
            http_status=status,
            content_type="application/json",
            request_url=url,
            metadata={
                "capture_mode": "embedded_json",
                "parent_payload_hash": page_capture.payload_hash,
                "page_kind": page_kind,
                "script_index": script_index,
                "script_id": attrs.get("id"),
                "script_type": attrs.get("type"),
            },
        )
        embedded.append(
            EmbeddedJsonCapture(
                script_index=script_index,
                script_id=attrs.get("id"),
                script_type=attrs.get("type"),
                capture=script_capture,
            )
        )

    assets: list[BuildAssetCapture] = []
    for asset_kind, asset_url in _asset_urls(
        parser,
        page_url=url,
        base_url=registry.base_url,
    ):
        asset = asset_cache.get(asset_url)
        if asset is None:
            asset = _capture_asset(
                registry=registry,
                archive=archive,
                parent_capture=page_capture,
                page_kind=page_kind,
                asset_kind=asset_kind,
                url=asset_url,
                timeout_seconds=timeout_seconds,
                opener=opener,
            )
            asset_cache[asset_url] = asset
        assets.append(asset)

    return BuildPageCapture(
        page_kind=page_kind,
        url=url,
        status=status,
        content_type=content_type,
        capture=page_capture,
        embedded_json=tuple(embedded),
        assets=tuple(assets),
        error=error,
    )


def capture_character_build_pages(
    registry: SourceRegistry,
    archive: RawArchive,
    *,
    character: str,
    realm: str,
    phase: int = 0,
    location: str = "World Bosses",
    difficulty: str = "normal",
    spec: str | None = None,
    timeout_seconds: float = 30.0,
    opener: OpenUrl = urlopen,
) -> tuple[BuildPageCapture, BuildPageCapture]:
    character_url = build_character_url(
        registry.base_url,
        character=character,
        realm=realm,
        phase=phase,
        location=location,
        difficulty=difficulty,
        spec=spec,
    )
    armory_url = build_armory_url(registry.base_url, character=character, realm=realm)
    asset_cache: dict[str, BuildAssetCapture] = {}
    return (
        _capture_one_page(
            registry=registry,
            archive=archive,
            page_kind="character_build",
            url=character_url,
            timeout_seconds=timeout_seconds,
            opener=opener,
            asset_cache=asset_cache,
        ),
        _capture_one_page(
            registry=registry,
            archive=archive,
            page_kind="armory",
            url=armory_url,
            timeout_seconds=timeout_seconds,
            opener=opener,
            asset_cache=asset_cache,
        ),
    )


def build_page_capture_to_dict(result: BuildPageCapture) -> dict[str, Any]:
    return {
        "page_kind": result.page_kind,
        "url": result.url,
        "status": result.status,
        "content_type": result.content_type,
        "capture": capture_to_dict(result.capture) if result.capture else None,
        "embedded_json": [
            {
                "script_index": item.script_index,
                "script_id": item.script_id,
                "script_type": item.script_type,
                "capture": capture_to_dict(item.capture),
            }
            for item in result.embedded_json
        ],
        "assets": [
            {
                "url": item.url,
                "asset_kind": item.asset_kind,
                "status": item.status,
                "content_type": item.content_type,
                "capture": capture_to_dict(item.capture) if item.capture else None,
                "api_route_candidates": list(item.api_route_candidates),
                "error": item.error,
            }
            for item in result.assets
        ],
        "error": result.error,
    }
