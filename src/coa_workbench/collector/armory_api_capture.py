from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable
from urllib.parse import quote, urlencode, urljoin
from urllib.request import Request, urlopen

from .http_read import read_response_resilient
from .raw_archive import (
    RawArchive,
    RawCapture,
    capture_to_dict,
    request_key_from_url,
    sanitize_url,
)
from .source_registry import SourceRegistry

OpenUrl = Callable[..., Any]
_MAX_JSON_BYTES = 32 * 1024 * 1024


@dataclass(frozen=True, slots=True)
class ArmoryApiObservation:
    observation_kind: str
    url: str
    status: int | None
    content_type: str | None
    capture: RawCapture | None
    top_level_keys: tuple[str, ...]
    error: str | None


@dataclass(frozen=True, slots=True)
class ArmoryApiCaptureResult:
    character_id: int | str | None
    character_class: str | None
    has_armory: bool | None
    identity_source: str | None
    observations: tuple[ArmoryApiObservation, ...]


def _api_url(base_url: str, path: str, query: list[tuple[str, str]] | None = None) -> str:
    url = urljoin(f"{base_url.rstrip('/')}/", path.lstrip("/"))
    if query:
        url += "?" + urlencode(query)
    return url


def _capture_json_observation(
    *,
    registry: SourceRegistry,
    archive: RawArchive,
    observation_kind: str,
    url: str,
    timeout_seconds: float,
    opener: OpenUrl,
) -> tuple[ArmoryApiObservation, Any | None]:
    request = Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "CoA-Raid-Intelligence-Workbench/0.1 armory-api-capture",
        },
        method="GET",
    )
    status, content_type, body, network_error = read_response_resilient(
        request,
        timeout_seconds=timeout_seconds,
        opener=opener,
        max_bytes=_MAX_JSON_BYTES,
    )
    if body is None:
        return (
            ArmoryApiObservation(
                observation_kind=observation_kind,
                url=sanitize_url(url),
                status=status,
                content_type=content_type,
                capture=None,
                top_level_keys=(),
                error=network_error or "response body was unavailable",
            ),
            None,
        )

    capture = archive.capture_bytes(
        body,
        source_code=registry.source_code,
        endpoint_code=f"armory_api_{observation_kind}",
        request_key=request_key_from_url("GET", url),
        fetched_at=datetime.now(timezone.utc),
        http_status=status,
        content_type=content_type,
        request_url=url,
        metadata={
            "capture_mode": "autonomous_armory_api",
            "observation_kind": observation_kind,
            "request_header_names": sorted(request.headers),
        },
    )

    parsed: Any | None = None
    parse_error: str | None = None
    try:
        parsed = json.loads(body)
    except (UnicodeDecodeError, json.JSONDecodeError):
        parse_error = "response was not valid JSON"

    top_level_keys = (
        tuple(sorted(str(key) for key in parsed)) if isinstance(parsed, dict) else ()
    )
    error = network_error or parse_error
    return (
        ArmoryApiObservation(
            observation_kind=observation_kind,
            url=sanitize_url(url),
            status=status,
            content_type=content_type,
            capture=capture,
            top_level_keys=top_level_keys,
            error=error,
        ),
        parsed,
    )


def _character_identity(payload: Any) -> tuple[int | str | None, str | None, bool | None]:
    if not isinstance(payload, dict):
        return None, None, None
    character = payload.get("character")
    character_id: int | str | None = None
    character_class: str | None = None
    if isinstance(character, dict):
        candidate_id = character.get("id")
        if isinstance(candidate_id, (int, str)) and not isinstance(candidate_id, bool):
            character_id = candidate_id
        candidate_class = character.get("class")
        if isinstance(candidate_class, str) and candidate_class.strip():
            character_class = candidate_class.strip()
    has_armory_value = payload.get("has_armory")
    has_armory = has_armory_value if isinstance(has_armory_value, bool) else None
    return character_id, character_class, has_armory


def _search_identity(
    payload: Any,
    *,
    character: str,
    realm: str,
) -> tuple[int | str | None, str | None]:
    if not isinstance(payload, dict):
        return None, None
    rows = payload.get("characters")
    if not isinstance(rows, list):
        return None, None

    expected_name = character.casefold()
    expected_realm = realm.casefold()
    matches: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        name = row.get("name")
        row_realm = row.get("realm")
        if not isinstance(name, str) or name.casefold() != expected_name:
            continue
        if not isinstance(row_realm, str) or row_realm.casefold() != expected_realm:
            continue
        matches.append(row)

    if len(matches) != 1:
        return None, None
    match = matches[0]
    candidate_id = match.get("id")
    if not isinstance(candidate_id, (int, str)) or isinstance(candidate_id, bool):
        return None, None
    candidate_class = match.get("class")
    character_class = (
        candidate_class.strip()
        if isinstance(candidate_class, str) and candidate_class.strip()
        else None
    )
    return candidate_id, character_class


def capture_armory_api(
    registry: SourceRegistry,
    archive: RawArchive,
    *,
    character: str,
    realm: str,
    timeout_seconds: float = 30.0,
    captures_limit: int = 100,
    opener: OpenUrl = urlopen,
) -> ArmoryApiCaptureResult:
    """Capture the public Armory JSON chain without assigning game semantics."""
    prepared_character = character.strip()
    prepared_realm = realm.strip()
    if not prepared_character:
        raise ValueError("character cannot be empty")
    if not prepared_realm:
        raise ValueError("realm cannot be empty")
    if captures_limit < 1 or captures_limit > 100:
        raise ValueError("captures_limit must be between 1 and 100")

    observations: list[ArmoryApiObservation] = []
    by_name_url = _api_url(
        registry.base_url,
        f"/api/armory/by-name/{quote(prepared_character, safe='')}",
        [("realm", prepared_realm)],
    )
    by_name, by_name_payload = _capture_json_observation(
        registry=registry,
        archive=archive,
        observation_kind="by_name",
        url=by_name_url,
        timeout_seconds=timeout_seconds,
        opener=opener,
    )
    observations.append(by_name)

    character_id, character_class, has_armory = _character_identity(by_name_payload)
    identity_source: str | None = "by_name" if character_id is not None else None

    if character_id is None and has_armory is not False:
        search_url = _api_url(
            registry.base_url,
            "/api/characters/search",
            [("q", prepared_character), ("limit", "20")],
        )
        search, search_payload = _capture_json_observation(
            registry=registry,
            archive=archive,
            observation_kind="character_search",
            url=search_url,
            timeout_seconds=timeout_seconds,
            opener=opener,
        )
        observations.append(search)
        character_id, character_class = _search_identity(
            search_payload,
            character=prepared_character,
            realm=prepared_realm,
        )
        if character_id is not None:
            identity_source = "character_search"

    if character_id is None or has_armory is False:
        return ArmoryApiCaptureResult(
            character_id=character_id,
            character_class=character_class,
            has_armory=has_armory,
            identity_source=identity_source,
            observations=tuple(observations),
        )

    encoded_id = quote(str(character_id), safe="")
    detail_url = _api_url(registry.base_url, f"/api/armory/character/{encoded_id}")
    captures_url = _api_url(
        registry.base_url,
        f"/api/armory/character/{encoded_id}/captures",
        [("limit", str(captures_limit))],
    )
    for observation_kind, url in (
        ("character", detail_url),
        ("captures", captures_url),
    ):
        observation, _payload = _capture_json_observation(
            registry=registry,
            archive=archive,
            observation_kind=observation_kind,
            url=url,
            timeout_seconds=timeout_seconds,
            opener=opener,
        )
        observations.append(observation)

    if character_class:
        class_slug = quote(character_class.casefold(), safe="")
        talent_grid_url = _api_url(
            registry.base_url,
            f"/api/armory/talent-grid/{class_slug}",
        )
        talent_grid, _payload = _capture_json_observation(
            registry=registry,
            archive=archive,
            observation_kind="talent_grid",
            url=talent_grid_url,
            timeout_seconds=timeout_seconds,
            opener=opener,
        )
        observations.append(talent_grid)

    return ArmoryApiCaptureResult(
        character_id=character_id,
        character_class=character_class,
        has_armory=has_armory,
        identity_source=identity_source,
        observations=tuple(observations),
    )


def armory_api_capture_to_dict(result: ArmoryApiCaptureResult) -> dict[str, Any]:
    return {
        "character_id": result.character_id,
        "character_class": result.character_class,
        "has_armory": result.has_armory,
        "identity_source": result.identity_source,
        "observations": [
            {
                "observation_kind": item.observation_kind,
                "url": item.url,
                "status": item.status,
                "content_type": item.content_type,
                "capture": capture_to_dict(item.capture) if item.capture else None,
                "top_level_keys": list(item.top_level_keys),
                "error": item.error,
            }
            for item in result.observations
        ],
    }
