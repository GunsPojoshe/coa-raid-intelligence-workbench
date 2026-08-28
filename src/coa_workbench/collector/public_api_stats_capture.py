from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Mapping
from urllib.parse import urlencode, urljoin

from .http_profile import HttpRequestProfile, SameOriginHttpSession
from .http_read import read_response_resilient
from .raw_archive import RawArchive, RawCapture, request_key_from_url
from .source_registry import SourceRegistry

OpenUrl = Callable[..., Any]
PUBLIC_API_HTTP_PROFILE_VERSION = "coa-public-api-http-v1"
PUBLIC_API_HTTP_PROFILE = HttpRequestProfile(
    version=PUBLIC_API_HTTP_PROFILE_VERSION,
    headers=(
        ("Accept", "application/json"),
        ("User-Agent", "coa-raid-intelligence-workbench/0.1"),
    ),
)
PUBLIC_API_STATS_ENDPOINTS = (
    "public_api_phases",
    "public_api_bosses",
    "public_api_statistics",
)
_MAX_JSON_BYTES = 32 * 1024 * 1024
_ENUMS = {
    "difficulty": {"normal", "heroic", "mythic", "ascended", "all"},
    "metric": {"avg_dps", "avg_hps", "avg_dtps"},
    "damageMode": {"standard", "boss-only", "trash"},
    "role": {"tank", "dps", "tanks-and-dps", "support"},
}


@dataclass(frozen=True, slots=True)
class PublicApiStatsCapture:
    endpoint_code: str
    route_template: str
    query_keys: tuple[str, ...]
    http_profile_version: str
    status: int | None
    content_type: str | None
    capture: RawCapture | None
    top_level_kind: str | None
    top_level_keys: tuple[str, ...]
    error: str | None

    @property
    def complete(self) -> bool:
        return (
            self.capture is not None
            and self.error is None
            and self.status is not None
            and 200 <= self.status < 300
        )


def _prepared_api_key(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("API key must be supplied through a local environment variable")
    prepared = value.strip()
    if "\r" in prepared or "\n" in prepared:
        raise ValueError("API key cannot contain line breaks")
    return prepared


def _prepared_query(
    endpoint_code: str,
    allowed_keys: tuple[str, ...],
    values: Mapping[str, Any] | None,
) -> tuple[tuple[str, str], ...]:
    raw = dict(values or {})
    unknown = sorted(set(raw) - set(allowed_keys))
    if unknown:
        raise ValueError(f"unreviewed public API query keys: {unknown}")

    prepared: list[tuple[str, str]] = []
    for key in allowed_keys:
        value = raw.get(key)
        if value is None:
            continue
        if isinstance(value, bool):
            rendered = "true" if value else "false"
        elif isinstance(value, (str, int)) and not isinstance(value, bool):
            rendered = str(value).strip()
        else:
            raise ValueError(f"public API query value for {key!r} has unsupported type")
        if not rendered:
            raise ValueError(f"public API query value for {key!r} cannot be empty")
        if key in _ENUMS and rendered not in _ENUMS[key]:
            raise ValueError(f"public API query value for {key!r} is outside the documented enum")
        if key in {"phase", "bossId", "weekNumber"}:
            try:
                numeric = int(rendered)
            except ValueError as exc:
                raise ValueError(f"public API query value for {key!r} must be an integer") from exc
            if key == "phase" and numeric < 1:
                raise ValueError("public API phase must be at least 1")
        prepared.append((key, rendered))

    prepared_keys = {key for key, _value in prepared}
    if endpoint_code == "public_api_statistics" and "phase" not in prepared_keys:
        raise ValueError("public_api_statistics requires the documented phase query parameter")
    return tuple(prepared)


def _top_level_shape(payload: Any) -> tuple[str, tuple[str, ...]]:
    if isinstance(payload, dict):
        return "object", tuple(sorted(str(key) for key in payload))
    if isinstance(payload, list):
        return "array", ()
    if payload is None:
        return "null", ()
    if isinstance(payload, bool):
        return "boolean", ()
    if isinstance(payload, (int, float)):
        return "number", ()
    return "string", ()


def capture_public_api_stats(
    registry: SourceRegistry,
    archive: RawArchive,
    *,
    endpoint_code: str,
    api_key: str,
    query: Mapping[str, Any] | None = None,
    timeout_seconds: float = 20.0,
    retry_count: int = 0,
    opener: OpenUrl | Any | None = None,
    session: SameOriginHttpSession | None = None,
) -> PublicApiStatsCapture:
    if endpoint_code not in PUBLIC_API_STATS_ENDPOINTS:
        raise ValueError("only self-serve stats:read endpoints are allowed by this collector")
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be greater than zero")
    if retry_count < 0 or retry_count > 1:
        raise ValueError("retry_count must be between 0 and 1")
    if session is not None and opener is not None:
        raise ValueError("pass either session or opener, not both")

    route = registry.route(endpoint_code, require_production=True)
    if route.method != "GET" or route.access_scope != "stats:read" or route.experimental:
        raise ValueError("route is not a reviewed self-serve stats:read GET endpoint")
    if not route.route_template:
        raise ValueError("public API route template is unavailable")

    key = _prepared_api_key(api_key)
    prepared_query = _prepared_query(endpoint_code, route.parameter_keys, query)
    base = f"{registry.base_url.rstrip('/')}/"
    url = urljoin(base, route.route_template.lstrip("/"))
    if prepared_query:
        url = f"{url}?{urlencode(prepared_query)}"

    active_session = session or SameOriginHttpSession(
        registry.base_url,
        profile=PUBLIC_API_HTTP_PROFILE,
        opener=opener,
    )
    request = active_session.build_request(url)
    request.add_header("Authorization", f"Bearer {key}")
    status, content_type, body, transport_error = read_response_resilient(
        request,
        timeout_seconds=timeout_seconds,
        opener=active_session.open,
        max_bytes=_MAX_JSON_BYTES,
        retry_count=retry_count,
    )

    if body is None or transport_error is not None:
        return PublicApiStatsCapture(
            endpoint_code=endpoint_code,
            route_template=route.route_template,
            query_keys=tuple(key for key, _value in prepared_query),
            http_profile_version=active_session.profile.version,
            status=status,
            content_type=content_type,
            capture=None,
            top_level_kind=None,
            top_level_keys=(),
            error=transport_error or "response body was unavailable",
        )

    capture = archive.capture_bytes(
        body,
        source_code=registry.source_code,
        endpoint_code=endpoint_code,
        request_key=request_key_from_url("GET", url),
        fetched_at=datetime.now(timezone.utc),
        http_status=status,
        content_type=content_type,
        request_url=url,
        metadata={
            "capture_mode": "official_public_api_stats",
            "access_scope": "stats:read",
            "query_keys": [key for key, _value in prepared_query],
            "private_query_values": {key: value for key, value in prepared_query},
            "credential_header_name": "Authorization",
            **active_session.safe_request_metadata(request),
        },
    )

    try:
        payload = json.loads(body)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return PublicApiStatsCapture(
            endpoint_code=endpoint_code,
            route_template=route.route_template,
            query_keys=tuple(key for key, _value in prepared_query),
            http_profile_version=active_session.profile.version,
            status=status,
            content_type=content_type,
            capture=capture,
            top_level_kind=None,
            top_level_keys=(),
            error="response was not valid JSON",
        )

    top_level_kind, top_level_keys = _top_level_shape(payload)
    return PublicApiStatsCapture(
        endpoint_code=endpoint_code,
        route_template=route.route_template,
        query_keys=tuple(key for key, _value in prepared_query),
        http_profile_version=active_session.profile.version,
        status=status,
        content_type=content_type,
        capture=capture,
        top_level_kind=top_level_kind,
        top_level_keys=top_level_keys,
        error=None,
    )


def public_api_stats_capture_to_dict(result: PublicApiStatsCapture) -> dict[str, Any]:
    capture = result.capture
    return {
        "schema_version": 1,
        "capture_kind": "official_public_api_stats",
        "request": {
            "endpoint_code": result.endpoint_code,
            "route_template": result.route_template,
            "query_keys": list(result.query_keys),
            "access_scope": "stats:read",
            "credential_header_name": "Authorization",
            "http_profile_version": result.http_profile_version,
        },
        "response": {
            "status": result.status,
            "content_type": result.content_type,
            "top_level_kind": result.top_level_kind,
            "top_level_keys": list(result.top_level_keys),
            "archived": capture is not None,
            "bytes_uncompressed": capture.bytes_uncompressed if capture is not None else None,
            "schema_fingerprint_observed": bool(
                capture is not None and capture.schema_fingerprint is not None
            ),
            "duplicate_payload": capture.duplicate_payload if capture is not None else None,
            "duplicate_observation": (
                capture.duplicate_observation if capture is not None else None
            ),
            "error": result.error,
        },
        "summary": {
            "complete": result.complete,
            "contains_api_key": False,
            "contains_query_values": False,
            "contains_source_scalar_values": False,
            "raw_capture_ids_included": False,
            "events_read_used": False,
            "planner_scoring_allowed": False,
        },
    }


__all__ = [
    "PUBLIC_API_HTTP_PROFILE",
    "PUBLIC_API_HTTP_PROFILE_VERSION",
    "PUBLIC_API_STATS_ENDPOINTS",
    "PublicApiStatsCapture",
    "capture_public_api_stats",
    "public_api_stats_capture_to_dict",
]
