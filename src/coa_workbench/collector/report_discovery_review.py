from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlsplit

from .har_inventory import inspect_archived_payload
from .report_discovery import (
    REPORTS_PUBLIC_ROUTE,
    REPORT_DISCOVERY_MAX_LIMIT,
    REPORT_DISCOVERY_SORT_BY,
    REPORT_DISCOVERY_SORT_ORDER,
)

_REVIEW_SCHEMA_VERSION = 1
_CAPTURE_SCHEMA_VERSION = 1
_CAPTURE_KIND = "bounded_report_discovery"


def _generated_at() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _load_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("report discovery capture must contain a JSON object")
    return payload


def _required_object(value: object, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"report discovery field {field_name} must be an object")
    return value


def _required_string(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"report discovery field {field_name} must be a non-empty string")
    return value


def _required_integer(value: object, field_name: str, *, minimum: int = 0) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < minimum:
        raise ValueError(
            f"report discovery field {field_name} must be an integer greater than or equal to "
            f"{minimum}"
        )
    return value


def _required_boolean(value: object, field_name: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"report discovery field {field_name} must be a boolean")
    return value


def _required_string_list(value: object, field_name: str) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise ValueError(f"report discovery field {field_name} must be an array of strings")
    return value


def _validate_request(request: dict[str, Any]) -> dict[str, Any]:
    route_template = _required_string(request.get("route_template"), "request.route_template")
    if route_template != REPORTS_PUBLIC_ROUTE:
        raise ValueError("unsupported report discovery route template")

    sanitized_route = _required_string(request.get("sanitized_route"), "request.sanitized_route")
    route_parts = urlsplit(sanitized_route)
    if route_parts.path != REPORTS_PUBLIC_ROUTE:
        raise ValueError("report discovery sanitized route path does not match route template")

    expected_query_keys = ["page", "limit", "sortBy", "sortOrder"]
    query_keys = _required_string_list(request.get("query_keys"), "request.query_keys")
    if query_keys != expected_query_keys:
        raise ValueError("unsupported report discovery query key order")
    sanitized_query_keys = [key for key, _ in parse_qsl(route_parts.query, keep_blank_values=True)]
    if sanitized_query_keys != expected_query_keys:
        raise ValueError("report discovery sanitized route query keys do not match manifest")

    page = _required_integer(request.get("page"), "request.page", minimum=1)
    limit = _required_integer(request.get("limit"), "request.limit", minimum=1)
    if limit > REPORT_DISCOVERY_MAX_LIMIT:
        raise ValueError("report discovery limit exceeds reviewed maximum")

    sort_by = _required_string(request.get("sort_by"), "request.sort_by")
    sort_order = _required_string(request.get("sort_order"), "request.sort_order")
    if sort_by != REPORT_DISCOVERY_SORT_BY or sort_order != REPORT_DISCOVERY_SORT_ORDER:
        raise ValueError("unsupported report discovery sort values")

    return {
        "route_template": route_template,
        "sanitized_route": sanitized_route,
        "query_keys": query_keys,
        "page": page,
        "limit": limit,
        "sort_by": sort_by,
        "sort_order": sort_order,
        "http_profile_version": _required_string(
            request.get("http_profile_version"),
            "request.http_profile_version",
        ),
    }


def review_report_discovery_capture(
    capture_path: Path,
    *,
    raw_root: Path,
) -> dict[str, Any]:
    """Verify one bounded report archive and expose only scalar-free structural facts."""
    manifest = _load_object(capture_path)
    if manifest.get("schema_version") != _CAPTURE_SCHEMA_VERSION:
        raise ValueError("unsupported report discovery capture schema version")
    if manifest.get("capture_kind") != _CAPTURE_KIND:
        raise ValueError("unsupported report discovery capture kind")

    local_category = _required_string(manifest.get("local_category"), "local_category")
    request = _validate_request(_required_object(manifest.get("request"), "request"))
    response = _required_object(manifest.get("response"), "response")
    summary = _required_object(manifest.get("summary"), "summary")

    if not _required_boolean(summary.get("complete"), "summary.complete"):
        raise ValueError("report discovery capture is not complete")
    if _required_boolean(
        summary.get("contains_source_scalar_values"),
        "summary.contains_source_scalar_values",
    ):
        raise ValueError("report discovery compact manifest contains source scalar values")
    if _required_boolean(
        summary.get("category_semantics_verified"),
        "summary.category_semantics_verified",
    ):
        raise ValueError("report discovery category semantics cannot be pre-verified")
    if _required_boolean(
        summary.get("pagination_policy_verified"),
        "summary.pagination_policy_verified",
    ):
        raise ValueError("report discovery pagination policy cannot be pre-verified")

    status = _required_integer(response.get("status"), "response.status", minimum=100)
    if status < 200 or status >= 300:
        raise ValueError("report discovery response status is not successful")
    content_type = _required_string(response.get("content_type"), "response.content_type")
    capture = _required_object(response.get("capture"), "response.capture")

    payload_hash = _required_string(capture.get("payload_hash"), "response.capture.payload_hash")
    if len(payload_hash) != 64 or any(char not in "0123456789abcdefABCDEF" for char in payload_hash):
        raise ValueError("report discovery payload hash must be hexadecimal SHA-256")
    expected_fingerprint = _required_string(
        capture.get("schema_fingerprint"),
        "response.capture.schema_fingerprint",
    )
    expected_bytes = _required_integer(
        capture.get("bytes_uncompressed"),
        "response.capture.bytes_uncompressed",
        minimum=1,
    )
    capture_status = _required_integer(
        capture.get("http_status"),
        "response.capture.http_status",
        minimum=100,
    )
    capture_content_type = _required_string(
        capture.get("content_type"),
        "response.capture.content_type",
    )
    top_level_kind = _required_string(response.get("top_level_kind"), "response.top_level_kind")
    top_level_keys = _required_string_list(
        response.get("top_level_keys"),
        "response.top_level_keys",
    )

    inspection = inspect_archived_payload(payload_hash, raw_root=raw_root)
    comparisons = {
        "payload_hash": inspection["payload_hash"] == payload_hash,
        "schema_fingerprint": inspection["schema_fingerprint"] == expected_fingerprint,
        "bytes_uncompressed": inspection["bytes_uncompressed"] == expected_bytes,
        "top_level_kind": inspection["top_level_kind"] == top_level_kind,
        "top_level_keys": inspection["top_level_keys"] == top_level_keys,
        "http_status": capture_status == status,
        "content_type": capture_content_type == content_type,
    }
    failed = sorted(name for name, matches in comparisons.items() if not matches)
    if failed:
        raise ValueError("report discovery archive verification failed: " + ", ".join(failed))

    return {
        "schema_version": _REVIEW_SCHEMA_VERSION,
        "review_kind": "report_discovery_structural_review",
        "generated_at": _generated_at(),
        "source_capture_name": capture_path.name,
        "local_category": local_category,
        "request": request,
        "response": {
            "http_status": status,
            "content_type": content_type,
            "payload_hash": payload_hash,
            "schema_fingerprint": expected_fingerprint,
            "bytes_uncompressed": expected_bytes,
            "payload_path": inspection["payload_path"],
            "top_level_kind": inspection["top_level_kind"],
            "top_level_keys": inspection["top_level_keys"],
            "candidate_collections": inspection["candidate_collections"],
            "archive_verification": comparisons,
        },
        "summary": {
            "archive_verified": 1,
            "candidate_collection_count": len(inspection["candidate_collections"]),
            "all_consistent": True,
            "contains_source_scalar_values": False,
            "category_semantics_verified": False,
            "pagination_policy_verified": False,
        },
    }
