from __future__ import annotations

import json
import ssl
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from html.parser import HTMLParser
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode, urljoin, urlsplit
from urllib.request import Request, urlopen

from .raw_archive import RawArchive, RawCapture, capture_to_dict, request_key_from_url
from .source_registry import SourceRegistry

OpenUrl = Callable[..., Any]


@dataclass(frozen=True, slots=True)
class EmbeddedJsonCapture:
    script_index: int
    script_id: str | None
    script_type: str | None
    capture: RawCapture


@dataclass(frozen=True, slots=True)
class BuildPageCapture:
    page_kind: str
    url: str
    status: int | None
    content_type: str | None
    capture: RawCapture | None
    embedded_json: tuple[EmbeddedJsonCapture, ...]
    error: str | None


class _JsonScriptParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self._inside_script = False
        self._attrs: dict[str, str | None] = {}
        self._parts: list[str] = []
        self.scripts: list[tuple[dict[str, str | None], str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.casefold() != "script" or self._inside_script:
            return
        self._inside_script = True
        self._attrs = {str(key).casefold(): value for key, value in attrs}
        self._parts = []

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


def _json_scripts(body: bytes) -> list[tuple[int, dict[str, str | None], bytes]]:
    try:
        text = body.decode("utf-8")
    except UnicodeDecodeError:
        return []
    parser = _JsonScriptParser()
    parser.feed(text)
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


def _capture_one_page(
    *,
    registry: SourceRegistry,
    archive: RawArchive,
    page_kind: str,
    url: str,
    timeout_seconds: float,
    opener: OpenUrl,
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
            body = response.read()
    except HTTPError as exc:
        status = exc.code
        content_type = exc.headers.get_content_type() if exc.headers else None
        body = exc.read()
        error = f"HTTP {exc.code}: {exc.reason}"
    except URLError as exc:
        error = f"network error: {exc.reason}"

    if body is None:
        return BuildPageCapture(page_kind, url, status, content_type, None, (), error)

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
    embedded: list[EmbeddedJsonCapture] = []
    for script_index, attrs, json_body in _json_scripts(body):
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
    return BuildPageCapture(
        page_kind=page_kind,
        url=url,
        status=status,
        content_type=content_type,
        capture=page_capture,
        embedded_json=tuple(embedded),
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
    return (
        _capture_one_page(
            registry=registry,
            archive=archive,
            page_kind="character_build",
            url=character_url,
            timeout_seconds=timeout_seconds,
            opener=opener,
        ),
        _capture_one_page(
            registry=registry,
            archive=archive,
            page_kind="armory",
            url=armory_url,
            timeout_seconds=timeout_seconds,
            opener=opener,
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
        "error": result.error,
    }
