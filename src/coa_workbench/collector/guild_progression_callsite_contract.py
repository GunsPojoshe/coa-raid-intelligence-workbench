from __future__ import annotations

import gzip
import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

KIND = "guild_progression_helper_callsite_inventory"
PRIVATE_KIND = f"{KIND}_private"
VERSION = "guild-progression-helper-callsite-inventory-v1"
ROUTE = "/api/guilds/progression"
REVIEW_KIND = "guild_progression_usage_context_review"
REVIEW_VERSION = "guild-progression-usage-context-review-v1"
RECOVERY_KIND = "guild_identity_asset_profiled_recovery"
PRIVATE_RECOVERY_KIND = f"{RECOVERY_KIND}_private"
RECOVERY_VERSION = "guild-identity-asset-profiled-recovery-v1"
METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"}
MARKERS = {"body", "data", "headers", "method", "params", "query", "searchParams", "url"}
FORBIDDEN_PUBLIC_FIELDS = {
    "asset_url",
    "callee",
    "context",
    "private_query",
    "raw_payload",
    "raw_records",
    "request_url",
    "source_guild_id",
    "symbol",
}


def generated_at() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def canonical_lf(value: bytes) -> bytes:
    return value.replace(b"\r\n", b"\n")


def document_hashes(value: bytes) -> set[str]:
    lf = canonical_lf(value)
    return {sha256(value), sha256(lf), sha256(lf.replace(b"\n", b"\r\n"))}


def load_json(path: Path, label: str) -> tuple[dict[str, Any], bytes]:
    try:
        body = path.read_bytes()
        value = json.loads(body)
    except OSError as exc:
        raise ValueError(f"unable to read {label}: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"{label} is not valid JSON: {path}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{label} must contain a JSON object")
    return value, body


def write_json(path: Path, value: Mapping[str, Any]) -> bytes:
    path.parent.mkdir(parents=True, exist_ok=True)
    body = (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_bytes(body)
    temporary.replace(path)
    return body


def object_value(value: object, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    return value


def array_value(value: object, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"{label} must be an array")
    return value


def integer_value(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{label} must be an integer")
    return value


def sha256_value(value: object, label: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value):
        raise ValueError(f"{label} must be SHA-256")
    return value


def expect(source: Mapping[str, Any], expected: Mapping[str, object], label: str) -> None:
    for field, value in expected.items():
        if source.get(field) != value:
            raise ValueError(f"{label} mismatch: {field}")


def property_names(value: object) -> set[str]:
    if isinstance(value, dict):
        names = set(value)
        for child in value.values():
            names.update(property_names(child))
        return names
    if isinstance(value, list):
        names: set[str] = set()
        for child in value:
            names.update(property_names(child))
        return names
    return set()


def require_checks(value: object, expected_count: int, label: str) -> None:
    checks = object_value(value, label)
    if len(checks) != expected_count or any(item is not True for item in checks.values()):
        raise ValueError(f"{label} failed")


def validate_usage_review(review: Mapping[str, Any]) -> None:
    expect(
        review,
        {"schema_version": 1, "review_kind": REVIEW_KIND, "review_version": REVIEW_VERSION},
        "usage review",
    )
    usage = object_value(review.get("usage_review"), "usage review evidence")
    expect(
        usage,
        {
            "route_template": ROUTE,
            "occurrence_count": 1,
            "call_style_candidates": ["literal_reference"],
            "method_candidates": [],
            "method_candidate_unambiguous": False,
            "method_resolution_status": "unresolved",
            "actual_invocation_observed": False,
            "literal_reference_only": True,
            "request_shape_sufficient_for_bounded_probe": False,
            "usage_context_reviewed": True,
            "route_semantics_verified": False,
            "contains_raw_context": False,
            "contains_source_scalar_values": False,
        },
        "usage review evidence",
    )
    required_blockers = {
        "http_method_unresolved",
        "literal_reference_without_call_site",
        "invocation_shape_unresolved",
    }
    blockers = array_value(usage.get("blockers"), "usage review blockers")
    if set(blockers) != required_blockers:
        raise ValueError("usage review blockers mismatch")
    require_checks(review.get("integrity_checks"), 30, "usage review integrity checks")
    summary = object_value(review.get("summary"), "usage review summary")
    expect(
        summary,
        {
            "all_integrity_checks_passed": True,
            "integrity_check_count": 30,
            "guild_progression_usage_context_reviewed": True,
            "method_candidate_unambiguous": False,
            "actual_invocation_observed": False,
            "request_shape_sufficient_for_bounded_probe": False,
            "ready_for_bounded_progression_route_probe": False,
            "guild_api_route_semantics_verified": False,
            "pagination_semantics_verified": False,
            "termination_semantics_verified": False,
            "completeness_verified": False,
            "ready_for_full_guild_crawl": False,
            "planner_scoring_allowed": False,
            "contains_raw_context": False,
            "contains_source_scalar_values": False,
        },
        "usage review summary",
    )
    boundary = object_value(review.get("decision_boundary"), "usage review boundary")
    expect(
        boundary,
        {
            "status": "guild_progression_usage_reviewed_probe_blocked",
            "guild_progression_route_candidate_observed": True,
            "guild_progression_usage_context_observed": True,
            "guild_progression_usage_context_reviewed": True,
            "guild_progression_method_candidate_unambiguous": False,
            "guild_progression_request_shape_verified": False,
            "ready_for_bounded_progression_route_probe": False,
            "guild_api_route_semantics_verified": False,
            "pagination_semantics_verified": False,
            "termination_semantics_verified": False,
            "completeness_verified": False,
            "automatic_full_guild_crawl_allowed": False,
            "ready_for_full_guild_crawl": False,
            "ready_for_multi_report_character_graph": False,
            "ready_for_performance_model": False,
            "ready_for_bis25_scoring": False,
            "planner_scoring_allowed": False,
        },
        "usage review boundary",
    )
    if property_names(review) & FORBIDDEN_PUBLIC_FIELDS:
        raise ValueError("usage review contains forbidden public fields")


def validate_recovery(
    public: Mapping[str, Any],
    private: Mapping[str, Any],
    private_body: bytes,
    guild_label: str,
) -> str:
    expect(
        public,
        {
            "schema_version": 1,
            "recovery_kind": RECOVERY_KIND,
            "recovery_version": RECOVERY_VERSION,
        },
        "public recovery",
    )
    expect(
        object_value(public.get("target"), "public recovery target"),
        {
            "guild_label": guild_label,
            "asset_url_published": False,
            "source_guild_id_published": False,
        },
        "public recovery target",
    )
    expect(
        object_value(public.get("summary"), "public recovery summary"),
        {
            "all_integrity_checks_passed": True,
            "asset_download_completed": True,
            "contains_source_scalar_values": False,
            "guild_api_route_candidate_count": 3,
        },
        "public recovery summary",
    )
    require_checks(public.get("integrity_checks"), 15, "public recovery integrity checks")
    routes = object_value(public.get("route_inventory"), "public recovery route inventory")
    route_shapes = array_value(routes.get("guild_api_route_shapes"), "public recovery routes")
    if ROUTE not in route_shapes:
        raise ValueError("public recovery does not contain progression route candidate")
    expected_private = sha256_value(
        public.get("source_private_recovery_sha256"),
        "public recovery private SHA-256",
    )
    if expected_private not in document_hashes(private_body):
        raise ValueError("private profiled recovery SHA-256 mismatch")
    expect(
        private,
        {
            "schema_version": 1,
            "recovery_kind": PRIVATE_RECOVERY_KIND,
            "recovery_version": RECOVERY_VERSION,
            "target_guild_label": guild_label,
        },
        "private recovery",
    )
    expect(
        object_value(private.get("summary"), "private recovery summary"),
        {"asset_download_completed": True, "contains_source_scalar_values": True},
        "private recovery summary",
    )
    candidates = [
        str(item).replace("\\/", "/")
        for item in array_value(private.get("api_route_candidates"), "private routes")
    ]
    if ROUTE not in candidates:
        raise ValueError("private recovery does not contain progression route candidate")
    return sha256_value(private.get("asset_capture_payload_hash"), "asset payload SHA-256")


def load_asset(raw_root: Path, payload_hash: str) -> tuple[bytes, Path]:
    manifests = sorted(raw_root.glob(f"**/{payload_hash}.content.json"))
    if len(manifests) != 1:
        raise ValueError("expected exactly one raw content manifest for recovered asset")
    manifest, _ = load_json(manifests[0], "recovered asset manifest")
    expect(
        manifest,
        {
            "schema_version": 1,
            "endpoint_code": "guild_identity_asset_recovery",
            "payload_hash": payload_hash,
            "compression": "gzip",
        },
        "recovered asset manifest",
    )
    relative = manifest.get("payload_path")
    if not isinstance(relative, str) or not relative:
        raise ValueError("recovered asset payload_path is missing")
    root = raw_root.resolve()
    payload_path = (root / relative).resolve()
    if (
        not payload_path.is_relative_to(root)
        or not payload_path.is_file()
        or not payload_path.name.endswith(".gz")
    ):
        raise ValueError("asset payload must be a gzip file below raw-root")
    try:
        body = gzip.decompress(payload_path.read_bytes())
    except (OSError, EOFError) as exc:
        raise ValueError("unable to decompress recovered asset") from exc
    if sha256(body) != payload_hash:
        raise ValueError("recovered asset payload SHA-256 mismatch")
    expected_bytes = integer_value(manifest.get("bytes_uncompressed"), "asset byte count")
    if len(body) != expected_bytes:
        raise ValueError("recovered asset byte count mismatch")
    return body, manifests[0]
