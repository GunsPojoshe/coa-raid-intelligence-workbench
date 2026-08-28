from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Callable, Mapping
from urllib.parse import urlencode, urljoin

from .http_profile import SameOriginHttpSession
from .http_read import read_response_resilient
from .public_api_stats_capture import PUBLIC_API_HTTP_PROFILE
from .source_registry import SourceRegistry

OpenUrl = Callable[..., Any]
PUBLIC_API_CAPABILITY_PROBE_VERSION = "official-public-api-capability-v1"
_MAX_RESPONSE_BYTES = 2 * 1024 * 1024
_KNOWN_ERROR_CODES = frozenset(
    {
        "missing_api_key",
        "invalid_api_key",
        "insufficient_scope",
        "rate_limit_exceeded",
        "daily_quota_exceeded",
        "invalid_parameter",
        "not_found",
        "service_unavailable",
    }
)


@dataclass(frozen=True, slots=True)
class PublicApiEndpointCapability:
    status: int | None
    json_valid: bool
    response_shape_valid: bool
    outcome: str
    error_code: str | None
    transport_error_present: bool


@dataclass(frozen=True, slots=True)
class PublicApiCapabilityProbe:
    stats_read: PublicApiEndpointCapability
    events_read: PublicApiEndpointCapability
    network_request_count: int

    @property
    def events_read_available(self) -> bool:
        return self.events_read.outcome == "available"

    @property
    def access_request_required(self) -> bool:
        return (
            self.stats_read.outcome == "available"
            and self.events_read.outcome == "insufficient_scope"
        )


def _prepare_api_key(value: str) -> str:
    prepared = value.strip() if isinstance(value, str) else ""
    if not prepared:
        raise ValueError("API key must be supplied through the private key loader")
    if "\r" in prepared or "\n" in prepared:
        raise ValueError("API key cannot contain line breaks")
    return prepared


def _json_payload(body: bytes | None) -> tuple[Mapping[str, Any] | None, bool]:
    if body is None:
        return None, False
    try:
        payload = json.loads(body)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None, False
    if not isinstance(payload, dict):
        return None, True
    return payload, True


def _safe_error_code(payload: Mapping[str, Any] | None) -> str | None:
    if payload is None:
        return None
    raw = payload.get("error")
    if not isinstance(raw, str):
        return None
    prepared = raw.strip()
    if prepared in _KNOWN_ERROR_CODES:
        return prepared
    return "other"


def _classify_endpoint(
    *,
    status: int | None,
    body: bytes | None,
    transport_error: str | None,
    expected_array_key: str,
    require_pagination: bool,
) -> PublicApiEndpointCapability:
    payload, json_valid = _json_payload(body)
    error_code = _safe_error_code(payload)
    shape_valid = bool(
        payload is not None
        and payload.get("success") is True
        and isinstance(payload.get(expected_array_key), list)
        and (not require_pagination or isinstance(payload.get("pagination"), dict))
    )

    if status is None:
        outcome = "transport_error"
    elif status == 200:
        if not json_valid:
            outcome = "invalid_json"
        elif not shape_valid:
            outcome = "unexpected_response_shape"
        else:
            outcome = "available"
    elif status == 401:
        outcome = "unauthorized"
    elif status == 403 and error_code == "insufficient_scope":
        outcome = "insufficient_scope"
    elif status == 403:
        outcome = "forbidden"
    elif status == 429:
        outcome = "rate_limited"
    elif status >= 500:
        outcome = "service_unavailable"
    else:
        outcome = "unexpected_http_status"

    return PublicApiEndpointCapability(
        status=status,
        json_valid=json_valid,
        response_shape_valid=shape_valid,
        outcome=outcome,
        error_code=error_code,
        transport_error_present=transport_error is not None and status is None,
    )


def _request_capability(
    session: SameOriginHttpSession,
    *,
    url: str,
    api_key: str,
    expected_array_key: str,
    require_pagination: bool,
    timeout_seconds: float,
    retry_count: int,
) -> PublicApiEndpointCapability:
    request = session.build_request(url)
    request.add_header("Authorization", f"Bearer {api_key}")
    status, _content_type, body, transport_error = read_response_resilient(
        request,
        timeout_seconds=timeout_seconds,
        opener=session.open,
        max_bytes=_MAX_RESPONSE_BYTES,
        retry_count=retry_count,
    )
    return _classify_endpoint(
        status=status,
        body=body,
        transport_error=transport_error,
        expected_array_key=expected_array_key,
        require_pagination=require_pagination,
    )


def probe_public_api_capabilities(
    registry: SourceRegistry,
    *,
    api_key: str,
    timeout_seconds: float = 20.0,
    retry_count: int = 0,
    opener: OpenUrl | Any | None = None,
    session: SameOriginHttpSession | None = None,
) -> PublicApiCapabilityProbe:
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be greater than zero")
    if retry_count < 0 or retry_count > 1:
        raise ValueError("retry_count must be between 0 and 1")
    if session is not None and opener is not None:
        raise ValueError("pass either session or opener, not both")

    key = _prepare_api_key(api_key)
    stats_route = registry.route("public_api_bosses", require_production=True)
    events_route = registry.route("public_api_reports")
    if stats_route.method != "GET" or stats_route.access_scope != "stats:read":
        raise ValueError("public_api_bosses is not the reviewed stats:read GET route")
    if (
        events_route.method != "GET"
        or events_route.access_scope != "events:read"
        or not events_route.experimental
        or not events_route.observatory_ready
    ):
        raise ValueError("public_api_reports is not the reviewed experimental events:read GET route")
    if not stats_route.route_template or not events_route.route_template:
        raise ValueError("official public API route template is unavailable")

    active_session = session or SameOriginHttpSession(
        registry.base_url,
        profile=PUBLIC_API_HTTP_PROFILE,
        opener=opener,
    )
    base = f"{registry.base_url.rstrip('/')}/"
    stats_url = urljoin(base, stats_route.route_template.lstrip("/"))
    events_url = urljoin(base, events_route.route_template.lstrip("/"))
    events_url = f"{events_url}?{urlencode((('limit', '1'),))}"

    stats_read = _request_capability(
        active_session,
        url=stats_url,
        api_key=key,
        expected_array_key="bosses",
        require_pagination=False,
        timeout_seconds=timeout_seconds,
        retry_count=retry_count,
    )
    events_read = _request_capability(
        active_session,
        url=events_url,
        api_key=key,
        expected_array_key="reports",
        require_pagination=True,
        timeout_seconds=timeout_seconds,
        retry_count=retry_count,
    )
    return PublicApiCapabilityProbe(
        stats_read=stats_read,
        events_read=events_read,
        network_request_count=2,
    )


def _endpoint_to_dict(value: PublicApiEndpointCapability) -> dict[str, Any]:
    return {
        "status": value.status,
        "json_valid": value.json_valid,
        "response_shape_valid": value.response_shape_valid,
        "outcome": value.outcome,
        "error_code": value.error_code,
        "transport_error_present": value.transport_error_present,
    }


def public_api_capability_probe_to_dict(result: PublicApiCapabilityProbe) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "review_kind": "official_public_api_capability_probe",
        "probe_version": PUBLIC_API_CAPABILITY_PROBE_VERSION,
        "network_request_count": result.network_request_count,
        "stats_read": _endpoint_to_dict(result.stats_read),
        "events_read": {
            **_endpoint_to_dict(result.events_read),
            "documented": True,
            "experimental": True,
            "availability_model": "on-request",
        },
        "summary": {
            "stats_read_available": result.stats_read.outcome == "available",
            "events_read_available": result.events_read_available,
            "events_read_access_request_required": result.access_request_required,
            "ready_for_official_event_pipeline": result.events_read_available,
            "direct_official_public_api_only": True,
            "browser_context_used": False,
            "browser_har_used": False,
            "raw_archive_written": False,
            "api_key_included": False,
            "report_ids_included": False,
            "report_titles_included": False,
            "encounter_ids_included": False,
            "player_names_included": False,
            "raw_event_values_included": False,
            "planner_scoring_allowed": False,
        },
        "public_release_safe": True,
    }


__all__ = [
    "PUBLIC_API_CAPABILITY_PROBE_VERSION",
    "PublicApiCapabilityProbe",
    "PublicApiEndpointCapability",
    "probe_public_api_capabilities",
    "public_api_capability_probe_to_dict",
]
