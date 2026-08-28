from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urljoin

from .http_profile import SameOriginHttpSession
from .http_read import read_response_resilient
from .raw_archive import RawArchive, RawCapture, request_key_from_url
from .source_registry import SourceRegistry

OpenUrl = Callable[..., Any]
ProgressCallback = Callable[["ObservedReportSliceCaptureResult"], None]

REPORT_DETAIL_ROUTE_SHAPE = "/api/reports/{template}"
ENCOUNTER_DETAIL_ROUTE_SHAPE = "/api/reports/{template}/encounters/{template}"
COMBATANTS_INFO_ROUTE_SHAPE = (
    "/api/reports/{template}/encounters/{template}/combatants-info"
)
OBSERVED_REPORT_SLICE_ROUTE_SHAPES = (
    REPORT_DETAIL_ROUTE_SHAPE,
    ENCOUNTER_DETAIL_ROUTE_SHAPE,
    COMBATANTS_INFO_ROUTE_SHAPE,
)
_MAX_JSON_BYTES_DEFAULT = 32 * 1024 * 1024


@dataclass(frozen=True, slots=True)
class ReportSliceEndpointCapture:
    endpoint_kind: str
    route_template: str
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


@dataclass(frozen=True, slots=True)
class ObservedReportSliceCaptureResult:
    route_inventory_hash: str
    route_inventory_verified: bool
    http_profile_version: str
    expected_endpoint_count: int
    endpoints: tuple[ReportSliceEndpointCapture, ...]

    @property
    def all_complete(self) -> bool:
        return (
            len(self.endpoints) == self.expected_endpoint_count
            and all(endpoint.complete for endpoint in self.endpoints)
        )


def _required_positive_integer(value: int, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{name} must be a positive integer")
    return value


def _load_verified_route_inventory(path: Path) -> tuple[str, dict[str, Any]]:
    body = path.read_bytes()
    payload = json.loads(body)
    if not isinstance(payload, dict):
        raise ValueError("SPA route inventory must contain a JSON object")
    if payload.get("schema_version") != 1:
        raise ValueError("unsupported SPA route inventory schema version")
    if payload.get("inventory_kind") != "archived_spa_api_route_inventory":
        raise ValueError("unexpected SPA route inventory kind")

    summary = payload.get("summary")
    if not isinstance(summary, dict):
        raise ValueError("SPA route inventory summary must be an object")
    if summary.get("all_archives_verified") is not True:
        raise ValueError("SPA route inventory archives are not verified")
    if summary.get("contains_source_record_scalar_values") is not False:
        raise ValueError("SPA route inventory privacy gate is not satisfied")
    if summary.get("network_requests_performed") is not False:
        raise ValueError("SPA route inventory must come from archived assets only")
    if summary.get("semantic_verification_required") is not True:
        raise ValueError("SPA route inventory semantic boundary is missing")

    route_rows = payload.get("routes")
    if not isinstance(route_rows, list):
        raise ValueError("SPA route inventory routes must be an array")
    observed: set[str] = set()
    for row in route_rows:
        if not isinstance(row, dict):
            raise ValueError("SPA route inventory route row must be an object")
        route_shape = row.get("route_shape")
        if not isinstance(route_shape, str) or not route_shape:
            raise ValueError("SPA route inventory route_shape must be a string")
        if row.get("semantic_status") != "unverified_candidate":
            raise ValueError("SPA route inventory route has an unexpected semantic status")
        archive_count = row.get("archive_count")
        if not isinstance(archive_count, int) or isinstance(archive_count, bool) or archive_count < 1:
            raise ValueError("SPA route inventory archive_count must be positive")
        observed.add(route_shape)

    missing = sorted(set(OBSERVED_REPORT_SLICE_ROUTE_SHAPES) - observed)
    if missing:
        raise ValueError(f"SPA route inventory is missing required observed routes: {missing}")
    return hashlib.sha256(body).hexdigest(), payload


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


def _endpoint_specs(report_id: int, encounter_id: int) -> tuple[tuple[str, str, str, str], ...]:
    return (
        (
            "report_detail",
            REPORT_DETAIL_ROUTE_SHAPE,
            f"/api/reports/{report_id}",
            "report_detail_observed",
        ),
        (
            "encounter_detail",
            ENCOUNTER_DETAIL_ROUTE_SHAPE,
            f"/api/reports/{report_id}/encounters/{encounter_id}",
            "encounter_detail_observed",
        ),
        (
            "combatants_info",
            COMBATANTS_INFO_ROUTE_SHAPE,
            f"/api/reports/{report_id}/encounters/{encounter_id}/combatants-info",
            "encounter_combatants_info_observed",
        ),
    )


def capture_observed_report_slice(
    registry: SourceRegistry,
    archive: RawArchive,
    *,
    route_inventory_path: Path,
    report_id: int,
    encounter_id: int,
    timeout_seconds: float = 30.0,
    retry_count: int = 1,
    max_json_bytes: int = _MAX_JSON_BYTES_DEFAULT,
    opener: OpenUrl | Any | None = None,
    session: SameOriginHttpSession | None = None,
    on_progress: ProgressCallback | None = None,
) -> ObservedReportSliceCaptureResult:
    """Capture only route shapes previously observed in an exact archived SPA inventory."""
    prepared_report_id = _required_positive_integer(report_id, "report_id")
    prepared_encounter_id = _required_positive_integer(encounter_id, "encounter_id")
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be greater than zero")
    if retry_count < 0 or retry_count > 1:
        raise ValueError("retry_count must be between 0 and 1")
    if max_json_bytes < 1 or max_json_bytes > _MAX_JSON_BYTES_DEFAULT:
        raise ValueError(
            f"max_json_bytes must be between 1 and {_MAX_JSON_BYTES_DEFAULT}"
        )
    if session is not None and opener is not None:
        raise ValueError("pass either session or opener, not both")

    route_inventory_hash, _inventory = _load_verified_route_inventory(route_inventory_path)
    active_session = session or SameOriginHttpSession(registry.base_url, opener=opener)
    endpoint_results: list[ReportSliceEndpointCapture] = []
    expected_endpoint_count = len(OBSERVED_REPORT_SLICE_ROUTE_SHAPES)

    for endpoint_kind, route_template, route, endpoint_code in _endpoint_specs(
        prepared_report_id,
        prepared_encounter_id,
    ):
        url = urljoin(f"{registry.base_url.rstrip('/')}/", route.lstrip("/"))
        request = active_session.build_request(url)
        status, content_type, body, transport_error = read_response_resilient(
            request,
            timeout_seconds=timeout_seconds,
            opener=active_session.open,
            max_bytes=max_json_bytes,
            retry_count=retry_count,
        )

        if body is None or transport_error is not None:
            endpoint_result = ReportSliceEndpointCapture(
                endpoint_kind=endpoint_kind,
                route_template=route_template,
                status=status,
                content_type=content_type,
                capture=None,
                top_level_kind=None,
                top_level_keys=(),
                error=transport_error or "response body was unavailable",
            )
        else:
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
                    "capture_mode": "observed_report_slice",
                    "endpoint_kind": endpoint_kind,
                    "route_template": route_template,
                    "route_inventory_hash": route_inventory_hash,
                    **active_session.safe_request_metadata(request),
                },
            )
            try:
                payload = json.loads(body)
            except (UnicodeDecodeError, json.JSONDecodeError):
                endpoint_result = ReportSliceEndpointCapture(
                    endpoint_kind=endpoint_kind,
                    route_template=route_template,
                    status=status,
                    content_type=content_type,
                    capture=capture,
                    top_level_kind=None,
                    top_level_keys=(),
                    error="response was not valid JSON",
                )
            else:
                top_level_kind, top_level_keys = _top_level_shape(payload)
                endpoint_result = ReportSliceEndpointCapture(
                    endpoint_kind=endpoint_kind,
                    route_template=route_template,
                    status=status,
                    content_type=content_type,
                    capture=capture,
                    top_level_kind=top_level_kind,
                    top_level_keys=top_level_keys,
                    error=None,
                )

        endpoint_results.append(endpoint_result)
        partial = ObservedReportSliceCaptureResult(
            route_inventory_hash=route_inventory_hash,
            route_inventory_verified=True,
            http_profile_version=active_session.profile.version,
            expected_endpoint_count=expected_endpoint_count,
            endpoints=tuple(endpoint_results),
        )
        if on_progress is not None:
            on_progress(partial)

    return ObservedReportSliceCaptureResult(
        route_inventory_hash=route_inventory_hash,
        route_inventory_verified=True,
        http_profile_version=active_session.profile.version,
        expected_endpoint_count=expected_endpoint_count,
        endpoints=tuple(endpoint_results),
    )


def observed_report_slice_capture_to_dict(
    result: ObservedReportSliceCaptureResult,
) -> dict[str, Any]:
    """Render structural capture facts without report, encounter, or payload scalar values."""
    endpoints = [
        {
            "endpoint_kind": endpoint.endpoint_kind,
            "route_template": endpoint.route_template,
            "status": endpoint.status,
            "content_type": endpoint.content_type,
            "top_level_kind": endpoint.top_level_kind,
            "top_level_keys": list(endpoint.top_level_keys),
            "capture": _capture_summary(endpoint.capture),
            "complete": endpoint.complete,
            "error": endpoint.error,
        }
        for endpoint in result.endpoints
    ]
    return {
        "schema_version": 1,
        "capture_kind": "observed_report_slice",
        "provenance": {
            "route_inventory_hash": result.route_inventory_hash,
            "route_inventory_verified": result.route_inventory_verified,
            "route_shapes": list(OBSERVED_REPORT_SLICE_ROUTE_SHAPES),
            "http_profile_version": result.http_profile_version,
        },
        "endpoints": endpoints,
        "summary": {
            "expected_endpoint_count": result.expected_endpoint_count,
            "attempted_endpoint_count": len(result.endpoints),
            "complete_endpoint_count": sum(endpoint.complete for endpoint in result.endpoints),
            "all_complete": result.all_complete,
            "contains_source_scalar_values": False,
            "semantic_verification_required": True,
            "normalization_allowed": False,
        },
    }
