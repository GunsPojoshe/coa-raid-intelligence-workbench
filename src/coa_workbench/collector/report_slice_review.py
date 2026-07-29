from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .har_inventory import inspect_archived_payload
from .report_slice_capture import OBSERVED_REPORT_SLICE_ROUTE_SHAPES

_REVIEW_SCHEMA_VERSION = 1
_CAPTURE_SCHEMA_VERSION = 1
_CAPTURE_KIND = "observed_report_slice"
_EXPECTED_ENDPOINTS = {
    "report_detail": "/api/reports/{template}",
    "encounter_detail": "/api/reports/{template}/encounters/{template}",
    "combatants_info": (
        "/api/reports/{template}/encounters/{template}/combatants-info"
    ),
}


def _generated_at() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _load_object(path: Path, description: str) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{description} must contain a JSON object")
    return payload


def _required_object(value: object, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"report slice field {field_name} must be an object")
    return value


def _required_string(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"report slice field {field_name} must be a non-empty string")
    return value


def _required_integer(value: object, field_name: str, *, minimum: int = 0) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < minimum:
        raise ValueError(
            f"report slice field {field_name} must be an integer greater than or equal to "
            f"{minimum}"
        )
    return value


def _required_boolean(value: object, field_name: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"report slice field {field_name} must be a boolean")
    return value


def _required_string_list(value: object, field_name: str) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise ValueError(f"report slice field {field_name} must be an array of strings")
    return value


def _required_sha256(value: object, field_name: str) -> str:
    prepared = _required_string(value, field_name).casefold()
    if len(prepared) != 64 or any(char not in "0123456789abcdef" for char in prepared):
        raise ValueError(f"report slice field {field_name} must be a SHA-256 digest")
    return prepared


def _validate_route_inventory(path: Path, expected_hash: str) -> dict[str, Any]:
    body = path.read_bytes()
    calculated_hash = hashlib.sha256(body).hexdigest()
    if calculated_hash != expected_hash:
        raise ValueError("report slice route inventory hash mismatch")

    inventory = json.loads(body)
    if not isinstance(inventory, dict):
        raise ValueError("report slice route inventory must contain an object")
    if inventory.get("schema_version") != 1:
        raise ValueError("unsupported report slice route inventory schema version")
    if inventory.get("inventory_kind") != "archived_spa_api_route_inventory":
        raise ValueError("unexpected report slice route inventory kind")

    summary = _required_object(inventory.get("summary"), "route_inventory.summary")
    if _required_boolean(
        summary.get("all_archives_verified"),
        "route_inventory.summary.all_archives_verified",
    ) is not True:
        raise ValueError("report slice route inventory archives are not verified")
    if _required_boolean(
        summary.get("contains_source_record_scalar_values"),
        "route_inventory.summary.contains_source_record_scalar_values",
    ) is not False:
        raise ValueError("report slice route inventory privacy gate failed")
    if _required_boolean(
        summary.get("network_requests_performed"),
        "route_inventory.summary.network_requests_performed",
    ) is not False:
        raise ValueError("report slice route inventory was not archive-only")
    if _required_boolean(
        summary.get("semantic_verification_required"),
        "route_inventory.summary.semantic_verification_required",
    ) is not True:
        raise ValueError("report slice route inventory semantic boundary is missing")

    rows = inventory.get("routes")
    if not isinstance(rows, list):
        raise ValueError("report slice route inventory routes must be an array")
    observed: set[str] = set()
    for row in rows:
        route = _required_object(row, "route_inventory.routes[]")
        if route.get("semantic_status") != "unverified_candidate":
            raise ValueError("report slice route inventory contains promoted route semantics")
        observed.add(_required_string(route.get("route_shape"), "route_shape"))

    missing = sorted(set(OBSERVED_REPORT_SLICE_ROUTE_SHAPES) - observed)
    if missing:
        raise ValueError(f"report slice route inventory is missing routes: {missing}")
    return inventory


def _review_endpoint(endpoint: dict[str, Any], *, raw_root: Path) -> dict[str, Any]:
    endpoint_kind = _required_string(endpoint.get("endpoint_kind"), "endpoint_kind")
    if endpoint_kind not in _EXPECTED_ENDPOINTS:
        raise ValueError(f"unsupported report slice endpoint kind: {endpoint_kind}")

    route_template = _required_string(endpoint.get("route_template"), "route_template")
    if route_template != _EXPECTED_ENDPOINTS[endpoint_kind]:
        raise ValueError(f"report slice route mismatch for {endpoint_kind}")
    if not _required_boolean(endpoint.get("complete"), "complete"):
        raise ValueError(f"report slice endpoint {endpoint_kind} is incomplete")
    if endpoint.get("error") is not None:
        raise ValueError(f"report slice endpoint {endpoint_kind} contains an error")

    status = _required_integer(endpoint.get("status"), "status", minimum=100)
    if status < 200 or status >= 300:
        raise ValueError(f"report slice endpoint {endpoint_kind} status is unsuccessful")
    content_type = _required_string(endpoint.get("content_type"), "content_type")
    if "json" not in content_type.casefold():
        raise ValueError(f"report slice endpoint {endpoint_kind} is not JSON")
    top_level_kind = _required_string(endpoint.get("top_level_kind"), "top_level_kind")
    top_level_keys = _required_string_list(endpoint.get("top_level_keys"), "top_level_keys")
    capture = _required_object(endpoint.get("capture"), "capture")
    payload_hash = _required_sha256(capture.get("payload_hash"), "capture.payload_hash")
    fingerprint = _required_sha256(
        capture.get("schema_fingerprint"),
        "capture.schema_fingerprint",
    )
    expected_bytes = _required_integer(
        capture.get("bytes_uncompressed"),
        "capture.bytes_uncompressed",
        minimum=1,
    )
    capture_status = _required_integer(
        capture.get("http_status"),
        "capture.http_status",
        minimum=100,
    )
    capture_content_type = _required_string(
        capture.get("content_type"),
        "capture.content_type",
    )

    inspection = inspect_archived_payload(payload_hash, raw_root=raw_root)
    comparisons = {
        "payload_hash": inspection["payload_hash"] == payload_hash,
        "schema_fingerprint": inspection["schema_fingerprint"] == fingerprint,
        "bytes_uncompressed": inspection["bytes_uncompressed"] == expected_bytes,
        "top_level_kind": inspection["top_level_kind"] == top_level_kind,
        "top_level_keys": inspection["top_level_keys"] == top_level_keys,
        "http_status": capture_status == status,
        "content_type": capture_content_type == content_type,
    }
    failed = sorted(name for name, matches in comparisons.items() if not matches)
    if failed:
        raise ValueError(
            f"report slice archive verification failed for {endpoint_kind}: "
            + ", ".join(failed)
        )

    return {
        "endpoint_kind": endpoint_kind,
        "route_template": route_template,
        "http_status": status,
        "content_type": content_type,
        "payload_hash": payload_hash,
        "schema_fingerprint": fingerprint,
        "bytes_uncompressed": expected_bytes,
        "payload_path": inspection["payload_path"],
        "top_level_kind": inspection["top_level_kind"],
        "top_level_keys": inspection["top_level_keys"],
        "candidate_collections": inspection["candidate_collections"],
        "archive_verification": comparisons,
    }


def review_observed_report_slice_capture(
    capture_path: Path,
    *,
    route_inventory_path: Path,
    raw_root: Path,
) -> dict[str, Any]:
    """Verify exact report-slice archives and expose scalar-free structural facts."""
    manifest = _load_object(capture_path, "report slice capture")
    if manifest.get("schema_version") != _CAPTURE_SCHEMA_VERSION:
        raise ValueError("unsupported report slice capture schema version")
    if manifest.get("capture_kind") != _CAPTURE_KIND:
        raise ValueError("unsupported report slice capture kind")

    provenance = _required_object(manifest.get("provenance"), "provenance")
    if _required_boolean(
        provenance.get("route_inventory_verified"),
        "provenance.route_inventory_verified",
    ) is not True:
        raise ValueError("report slice route inventory was not verified")
    route_inventory_hash = _required_sha256(
        provenance.get("route_inventory_hash"),
        "provenance.route_inventory_hash",
    )
    route_shapes = _required_string_list(
        provenance.get("route_shapes"),
        "provenance.route_shapes",
    )
    if route_shapes != list(OBSERVED_REPORT_SLICE_ROUTE_SHAPES):
        raise ValueError("report slice route shape set does not match the capture contract")
    http_profile_version = _required_string(
        provenance.get("http_profile_version"),
        "provenance.http_profile_version",
    )
    _validate_route_inventory(route_inventory_path, route_inventory_hash)

    summary = _required_object(manifest.get("summary"), "summary")
    expected_count = _required_integer(
        summary.get("expected_endpoint_count"),
        "summary.expected_endpoint_count",
        minimum=1,
    )
    attempted_count = _required_integer(
        summary.get("attempted_endpoint_count"),
        "summary.attempted_endpoint_count",
        minimum=0,
    )
    complete_count = _required_integer(
        summary.get("complete_endpoint_count"),
        "summary.complete_endpoint_count",
        minimum=0,
    )
    if expected_count != len(_EXPECTED_ENDPOINTS):
        raise ValueError("report slice expected endpoint count is unsupported")
    if attempted_count != expected_count or complete_count != expected_count:
        raise ValueError("report slice endpoint counts are incomplete")
    if _required_boolean(summary.get("all_complete"), "summary.all_complete") is not True:
        raise ValueError("report slice capture is not complete")
    if _required_boolean(
        summary.get("contains_source_scalar_values"),
        "summary.contains_source_scalar_values",
    ) is not False:
        raise ValueError("report slice compact manifest contains source scalar values")
    if _required_boolean(
        summary.get("semantic_verification_required"),
        "summary.semantic_verification_required",
    ) is not True:
        raise ValueError("report slice semantic review boundary is missing")
    if _required_boolean(
        summary.get("normalization_allowed"),
        "summary.normalization_allowed",
    ) is not False:
        raise ValueError("report slice normalization was enabled before review")

    endpoint_values = manifest.get("endpoints")
    if not isinstance(endpoint_values, list):
        raise ValueError("report slice endpoints must be an array")
    if len(endpoint_values) != expected_count:
        raise ValueError("report slice endpoint array count does not match summary")

    reviewed = [
        _review_endpoint(_required_object(item, "endpoints[]"), raw_root=raw_root)
        for item in endpoint_values
    ]
    kinds = [item["endpoint_kind"] for item in reviewed]
    if len(set(kinds)) != len(kinds) or set(kinds) != set(_EXPECTED_ENDPOINTS):
        raise ValueError("report slice endpoint kinds are missing or duplicated")

    candidate_collection_count = sum(
        len(endpoint["candidate_collections"]) for endpoint in reviewed
    )
    return {
        "schema_version": _REVIEW_SCHEMA_VERSION,
        "review_kind": "observed_report_slice_structural_review",
        "generated_at": _generated_at(),
        "source_capture_name": capture_path.name,
        "provenance": {
            "route_inventory_hash": route_inventory_hash,
            "route_inventory_verified": True,
            "route_shapes": route_shapes,
            "http_profile_version": http_profile_version,
        },
        "endpoints": reviewed,
        "summary": {
            "raw_archive_count": len(reviewed),
            "candidate_collection_count": candidate_collection_count,
            "all_archives_consistent": True,
            "contains_source_scalar_values": False,
            "semantic_verification_required": True,
            "normalization_allowed": False,
        },
    }
