from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable
from urllib.parse import urlencode, urljoin

from .http_profile import SameOriginHttpSession
from .http_read import read_response_resilient
from .raw_archive import RawArchive, RawCapture, request_key_from_url, sanitize_url
from .source_registry import SourceRegistry

OpenUrl = Callable[..., Any]
REPORTS_PUBLIC_ROUTE = "/api/reports/public"
REPORT_DISCOVERY_SORT_BY = "created_at"
REPORT_DISCOVERY_SORT_ORDER = "desc"
REPORT_DISCOVERY_DEFAULT_LIMIT = 5
REPORT_DISCOVERY_MAX_LIMIT = 5
_MAX_JSON_BYTES = 8 * 1024 * 1024


@dataclass(frozen=True, slots=True)
class ReportDiscoveryCapture:
    local_category: str
    page: int
    limit: int
    sort_by: str
    sort_order: str
    http_profile_version: str
    route: str
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


def _prepared_local_category(value: str) -> str:
    prepared = value.strip()
    if not prepared:
        raise ValueError("local_category cannot be empty")
    if len(prepared) > 80:
        raise ValueError("local_category is too long")
    return prepared


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


def _capture_summary(capture: RawCapture | None) -> dict[str, Any] | None:
    if capture is None:
        return None
    return {
        "raw_id": capture.raw_id,
        "observation_id": capture.observation_id,
        "payload_hash": capture.payload_hash,
        "bytes_uncompressed": capture.bytes_uncompressed,
        "content_type": capture.content_type,
        "schema_fingerprint": capture.schema_fingerprint,
        "duplicate_payload": capture.duplicate_payload,
        "duplicate_observation": capture.duplicate_observation,
        "http_status": capture.http_status,
    }


def capture_public_report_discovery(
    registry: SourceRegistry,
    archive: RawArchive,
    *,
    local_category: str = "public_recent",
    page: int = 1,
    limit: int = REPORT_DISCOVERY_DEFAULT_LIMIT,
    sort_by: str = REPORT_DISCOVERY_SORT_BY,
    sort_order: str = REPORT_DISCOVERY_SORT_ORDER,
    timeout_seconds: float = 20.0,
    retry_count: int = 0,
    opener: OpenUrl | Any | None = None,
    session: SameOriginHttpSession | None = None,
) -> ReportDiscoveryCapture:
    """Capture one explicitly bounded public-report page without inferring report semantics."""
    prepared_category = _prepared_local_category(local_category)
    if page < 1:
        raise ValueError("page must be at least 1")
    if limit < 1 or limit > REPORT_DISCOVERY_MAX_LIMIT:
        raise ValueError(f"limit must be between 1 and {REPORT_DISCOVERY_MAX_LIMIT}")
    if sort_by != REPORT_DISCOVERY_SORT_BY:
        raise ValueError(f"sort_by must remain the observed value {REPORT_DISCOVERY_SORT_BY!r}")
    if sort_order != REPORT_DISCOVERY_SORT_ORDER:
        raise ValueError(
            f"sort_order must remain the observed value {REPORT_DISCOVERY_SORT_ORDER!r}"
        )
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be greater than zero")
    if retry_count < 0 or retry_count > 1:
        raise ValueError("retry_count must be between 0 and 1")
    if session is not None and opener is not None:
        raise ValueError("pass either session or opener, not both")

    active_session = session or SameOriginHttpSession(registry.base_url, opener=opener)
    query = urlencode(
        (
            ("page", str(page)),
            ("limit", str(limit)),
            ("sortBy", sort_by),
            ("sortOrder", sort_order),
        )
    )
    url = urljoin(f"{registry.base_url.rstrip('/')}/", REPORTS_PUBLIC_ROUTE.lstrip("/"))
    url = f"{url}?{query}"
    request = active_session.build_request(url)
    status, content_type, body, transport_error = read_response_resilient(
        request,
        timeout_seconds=timeout_seconds,
        opener=active_session.open,
        max_bytes=_MAX_JSON_BYTES,
        retry_count=retry_count,
    )

    if body is None or transport_error is not None:
        return ReportDiscoveryCapture(
            local_category=prepared_category,
            page=page,
            limit=limit,
            sort_by=sort_by,
            sort_order=sort_order,
            http_profile_version=active_session.profile.version,
            route=sanitize_url(url),
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
        endpoint_code="reports_public_discovery",
        request_key=request_key_from_url("GET", url),
        fetched_at=datetime.now(timezone.utc),
        http_status=status,
        content_type=content_type,
        request_url=url,
        metadata={
            "capture_mode": "bounded_report_discovery",
            "local_category": prepared_category,
            "page": page,
            "limit": limit,
            "sort_by": sort_by,
            "sort_order": sort_order,
            **active_session.safe_request_metadata(request),
        },
    )

    try:
        payload = json.loads(body)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return ReportDiscoveryCapture(
            local_category=prepared_category,
            page=page,
            limit=limit,
            sort_by=sort_by,
            sort_order=sort_order,
            http_profile_version=active_session.profile.version,
            route=sanitize_url(url),
            status=status,
            content_type=content_type,
            capture=capture,
            top_level_kind=None,
            top_level_keys=(),
            error="response was not valid JSON",
        )

    top_level_kind, top_level_keys = _top_level_shape(payload)
    return ReportDiscoveryCapture(
        local_category=prepared_category,
        page=page,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,
        http_profile_version=active_session.profile.version,
        route=sanitize_url(url),
        status=status,
        content_type=content_type,
        capture=capture,
        top_level_kind=top_level_kind,
        top_level_keys=top_level_keys,
        error=None,
    )


def report_discovery_capture_to_dict(result: ReportDiscoveryCapture) -> dict[str, Any]:
    """Render a compact structural result without source report scalar values."""
    return {
        "schema_version": 1,
        "capture_kind": "bounded_report_discovery",
        "local_category": result.local_category,
        "request": {
            "route_template": REPORTS_PUBLIC_ROUTE,
            "sanitized_route": result.route,
            "query_keys": ["page", "limit", "sortBy", "sortOrder"],
            "page": result.page,
            "limit": result.limit,
            "sort_by": result.sort_by,
            "sort_order": result.sort_order,
            "http_profile_version": result.http_profile_version,
        },
        "response": {
            "status": result.status,
            "content_type": result.content_type,
            "top_level_kind": result.top_level_kind,
            "top_level_keys": list(result.top_level_keys),
            "capture": _capture_summary(result.capture),
            "error": result.error,
        },
        "summary": {
            "complete": result.complete,
            "contains_source_scalar_values": False,
            "category_semantics_verified": False,
            "pagination_policy_verified": False,
        },
    }
