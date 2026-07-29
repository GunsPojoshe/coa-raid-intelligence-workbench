from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .har_inventory import inspect_archived_payload

_REVIEW_SCHEMA_VERSION = 1
_CAPTURE_MANIFEST_SCHEMA_VERSION = 1
_SUCCESS_STATES = {"captured", "reused"}


def _generated_at() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _load_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Armory capture manifest must contain a JSON object")
    return payload


def _required_string(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"Armory capture manifest field {field_name} must be a non-empty string")
    return value


def _required_integer(value: object, field_name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError(f"Armory capture manifest field {field_name} must be a non-negative integer")
    return value


def _review_endpoint(
    endpoint_kind: str,
    endpoint: object,
    *,
    raw_root: Path,
) -> dict[str, Any]:
    if not isinstance(endpoint, dict):
        raise ValueError(f"Armory endpoint {endpoint_kind} manifest entry must be an object")
    state = endpoint.get("state")
    if state not in _SUCCESS_STATES:
        raise ValueError(f"Armory endpoint {endpoint_kind} is not completely captured")
    capture = endpoint.get("capture")
    if not isinstance(capture, dict):
        raise ValueError(f"Armory endpoint {endpoint_kind} has no capture metadata")

    payload_hash = _required_string(capture.get("payload_hash"), "payload_hash")
    expected_fingerprint = _required_string(
        capture.get("schema_fingerprint"),
        "schema_fingerprint",
    )
    expected_bytes = _required_integer(capture.get("bytes_uncompressed"), "bytes_uncompressed")
    expected_payload_path = _required_string(capture.get("payload_path"), "payload_path")

    inspection = inspect_archived_payload(payload_hash, raw_root=raw_root)
    comparisons = {
        "payload_hash": inspection["payload_hash"] == payload_hash,
        "schema_fingerprint": inspection["schema_fingerprint"] == expected_fingerprint,
        "bytes_uncompressed": inspection["bytes_uncompressed"] == expected_bytes,
        "payload_path": inspection["payload_path"] == expected_payload_path,
    }
    failed = sorted(name for name, matches in comparisons.items() if not matches)
    if failed:
        raise ValueError(
            f"Armory endpoint {endpoint_kind} archive verification failed: {', '.join(failed)}"
        )

    route = endpoint.get("route")
    status = endpoint.get("status")
    content_type = endpoint.get("content_type")
    return {
        "endpoint_kind": endpoint_kind,
        "state": state,
        "route": route if isinstance(route, str) else None,
        "http_status": status if isinstance(status, int) and not isinstance(status, bool) else None,
        "content_type": content_type if isinstance(content_type, str) else None,
        "payload_hash": payload_hash,
        "schema_fingerprint": expected_fingerprint,
        "bytes_uncompressed": expected_bytes,
        "payload_path": expected_payload_path,
        "top_level_kind": inspection["top_level_kind"],
        "top_level_keys": inspection["top_level_keys"],
        "candidate_collections": inspection["candidate_collections"],
        "archive_verification": comparisons,
    }


def review_armory_capture_manifest(
    manifest_path: Path,
    *,
    raw_root: Path,
) -> dict[str, Any]:
    """Inspect archived Armory payload structure without exposing source values."""
    manifest = _load_object(manifest_path)
    if manifest.get("schema_version") != _CAPTURE_MANIFEST_SCHEMA_VERSION:
        raise ValueError("unsupported Armory capture manifest schema version")
    if manifest.get("capture_mode") != "endpoint_isolated_armory_api":
        raise ValueError("unsupported Armory capture mode")

    endpoint_order = manifest.get("endpoint_order")
    endpoints = manifest.get("endpoints")
    if not isinstance(endpoint_order, list) or not endpoint_order:
        raise ValueError("Armory capture manifest endpoint_order must be a non-empty array")
    if not isinstance(endpoints, dict):
        raise ValueError("Armory capture manifest endpoints must be an object")

    reviewed: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in endpoint_order:
        endpoint_kind = _required_string(item, "endpoint_order[]")
        if endpoint_kind in seen:
            raise ValueError("Armory capture manifest endpoint_order contains duplicates")
        seen.add(endpoint_kind)
        reviewed.append(
            _review_endpoint(
                endpoint_kind,
                endpoints.get(endpoint_kind),
                raw_root=raw_root,
            )
        )

    unlisted = sorted(str(key) for key in endpoints if str(key) not in seen)
    if unlisted:
        raise ValueError(
            "Armory capture manifest contains endpoints absent from endpoint_order: "
            + ", ".join(unlisted)
        )

    subject = manifest.get("subject")
    if not isinstance(subject, dict):
        raise ValueError("Armory capture manifest subject must be an object")
    prepared_subject = {
        "character_id": _required_string(subject.get("character_id"), "subject.character_id"),
        "class_slug": _required_string(subject.get("class_slug"), "subject.class_slug"),
    }
    profile_version = _required_string(
        manifest.get("http_profile_version"),
        "http_profile_version",
    )

    return {
        "schema_version": _REVIEW_SCHEMA_VERSION,
        "review_kind": "armory_structural_review",
        "generated_at": _generated_at(),
        "source_manifest_name": manifest_path.name,
        "http_profile_version": profile_version,
        "subject": prepared_subject,
        "endpoint_order": [item["endpoint_kind"] for item in reviewed],
        "endpoints": reviewed,
        "summary": {
            "endpoint_count": len(reviewed),
            "archive_verified": len(reviewed),
            "all_consistent": True,
        },
    }
