from __future__ import annotations

import gzip
import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

_INVENTORY_KIND = "guild_progression_usage_context_inventory"
_INVENTORY_PRIVATE_KIND = "guild_progression_usage_context_inventory_private"
_INVENTORY_VERSION = "guild-progression-usage-context-inventory-v1"
_PUBLIC_RECOVERY_KIND = "guild_identity_asset_profiled_recovery"
_PRIVATE_RECOVERY_KIND = "guild_identity_asset_profiled_recovery_private"
_RECOVERY_VERSION = "guild-identity-asset-profiled-recovery-v1"
_ROUTE = "/api/guilds/progression"
_DEFAULT_CONTEXT_CHARS = 384
_DEFAULT_MAX_OCCURRENCES = 20
_METHODS = ("GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS")
_METHOD_LITERAL = re.compile(
    r"\bmethod\s*:\s*['\"](GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)['\"]",
    re.IGNORECASE,
)
_MEMBER_METHOD = re.compile(
    r"\.\s*(get|post|put|patch|delete|head|options)\s*\([^()]{0,240}$",
    re.IGNORECASE,
)
_FETCH_CALL = re.compile(r"\bfetch\s*\([^()]{0,240}$", re.IGNORECASE)
_CALL_TARGET = re.compile(
    r"([A-Za-z_$][A-Za-z0-9_$]*(?:\.[A-Za-z_$][A-Za-z0-9_$]*)*)\s*\([^()]{0,240}$"
)


def _generated_at() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _canonical_lf(value: bytes) -> bytes:
    return value.replace(b"\r\n", b"\n")


def _document_hashes(value: bytes) -> set[str]:
    lf = _canonical_lf(value)
    crlf = lf.replace(b"\n", b"\r\n")
    return {_sha256(value), _sha256(lf), _sha256(crlf)}


def _load(path: Path, label: str) -> tuple[dict[str, Any], bytes]:
    try:
        body = path.read_bytes()
        payload = json.loads(body)
    except OSError as exc:
        raise ValueError(f"unable to read {label}: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"{label} is not valid JSON: {path}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"{label} must contain a JSON object")
    return payload, body


def _write(path: Path, payload: Mapping[str, Any]) -> bytes:
    path.parent.mkdir(parents=True, exist_ok=True)
    body = (json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_bytes(body)
    temporary.replace(path)
    return body


def _object(value: object, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    return value


def _array(value: object, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"{label} must be an array")
    return value


def _hash(value: object, label: str) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise ValueError(f"{label} must be SHA-256")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{label} must be hexadecimal") from exc
    return value


def _expect(source: Mapping[str, Any], expected: Mapping[str, object], label: str) -> None:
    for field, value in expected.items():
        if source.get(field) != value:
            raise ValueError(f"{label} mismatch: {field}")


def _validate_recovery(
    public: Mapping[str, Any],
    private: Mapping[str, Any],
    *,
    private_body: bytes,
    expected_guild_label: str,
) -> str:
    _expect(
        public,
        {
            "schema_version": 1,
            "recovery_kind": _PUBLIC_RECOVERY_KIND,
            "recovery_version": _RECOVERY_VERSION,
        },
        "public profiled recovery",
    )
    target = _object(public.get("target"), "public recovery target")
    _expect(
        target,
        {
            "guild_label": expected_guild_label,
            "asset_url_published": False,
            "source_guild_id_published": False,
        },
        "public recovery target",
    )
    summary = _object(public.get("summary"), "public recovery summary")
    _expect(
        summary,
        {
            "all_integrity_checks_passed": True,
            "asset_download_completed": True,
            "contains_source_scalar_values": False,
            "guild_api_route_candidate_count": 3,
        },
        "public recovery summary",
    )
    checks = _object(public.get("integrity_checks"), "public recovery integrity_checks")
    if len(checks) != 15 or any(value is not True for value in checks.values()):
        raise ValueError("public profiled recovery integrity checks failed")
    routes = _object(public.get("route_inventory"), "public recovery route_inventory")
    shapes = _array(routes.get("guild_api_route_shapes"), "public recovery route shapes")
    if _ROUTE not in shapes:
        raise ValueError("public recovery does not contain the progression route candidate")
    boundary = _object(public.get("decision_boundary"), "public recovery boundary")
    _expect(
        boundary,
        {
            "guild_api_route_candidates_observed": True,
            "guild_api_route_semantics_verified": False,
            "ready_for_guild_api_route_review": True,
            "ready_for_full_guild_crawl": False,
            "planner_scoring_allowed": False,
        },
        "public recovery boundary",
    )

    expected_private_hash = _hash(
        public.get("source_private_recovery_sha256"),
        "public recovery source_private_recovery_sha256",
    )
    if expected_private_hash not in _document_hashes(private_body):
        raise ValueError("private profiled recovery SHA-256 mismatch")
    _expect(
        private,
        {
            "schema_version": 1,
            "recovery_kind": _PRIVATE_RECOVERY_KIND,
            "recovery_version": _RECOVERY_VERSION,
            "target_guild_label": expected_guild_label,
        },
        "private profiled recovery",
    )
    private_summary = _object(private.get("summary"), "private recovery summary")
    _expect(
        private_summary,
        {
            "asset_download_completed": True,
            "contains_source_scalar_values": True,
        },
        "private recovery summary",
    )
    candidates = _array(private.get("api_route_candidates"), "private recovery candidates")
    normalized = [str(value).replace("\\/", "/") for value in candidates]
    if _ROUTE not in normalized:
        raise ValueError("private recovery does not contain the progression route candidate")
    return _hash(private.get("asset_capture_payload_hash"), "asset capture payload hash")


def _safe_payload_path(raw_root: Path, relative_path: str) -> Path:
    root = raw_root.resolve()
    candidate = (root / relative_path).resolve()
    if not candidate.is_relative_to(root):
        raise ValueError("asset payload path escaped raw-root")
    if not candidate.is_file() or not candidate.name.endswith(".gz"):
        raise ValueError("asset payload must be a gzip file below raw-root")
    return candidate


def _load_asset(raw_root: Path, payload_hash: str) -> tuple[bytes, Path]:
    manifests = sorted(raw_root.glob(f"**/{payload_hash}.content.json"))
    if len(manifests) != 1:
        raise ValueError("expected exactly one raw content manifest for recovered asset")
    manifest, _ = _load(manifests[0], "recovered asset content manifest")
    _expect(
        manifest,
        {
            "schema_version": 1,
            "endpoint_code": "guild_identity_asset_recovery",
            "payload_hash": payload_hash,
            "compression": "gzip",
        },
        "recovered asset content manifest",
    )
    payload_path_value = manifest.get("payload_path")
    if not isinstance(payload_path_value, str) or not payload_path_value:
        raise ValueError("recovered asset payload_path is missing")
    payload_path = _safe_payload_path(raw_root, payload_path_value)
    try:
        body = gzip.decompress(payload_path.read_bytes())
    except (OSError, EOFError) as exc:
        raise ValueError("unable to decompress recovered asset") from exc
    if _sha256(body) != payload_hash:
        raise ValueError("recovered asset payload SHA-256 mismatch")
    expected_size = manifest.get("bytes_uncompressed")
    if isinstance(expected_size, bool) or not isinstance(expected_size, int):
        raise ValueError("recovered asset byte count is invalid")
    if len(body) != expected_size:
        raise ValueError("recovered asset byte count mismatch")
    return body, manifests[0]


def _classify_context(prefix: str, suffix: str, context: str) -> dict[str, Any]:
    methods = {match.upper() for match in _METHOD_LITERAL.findall(context)}
    styles: set[str] = set()
    member_match = _MEMBER_METHOD.search(prefix)
    if member_match:
        method = member_match.group(1).upper()
        if method in _METHODS:
            methods.add(method)
        styles.add("member_http_method_call")
    fetch_observed = _FETCH_CALL.search(prefix) is not None
    if fetch_observed:
        styles.add("fetch_call")
        if not methods:
            methods.add("GET")
    call_match = _CALL_TARGET.search(prefix)
    call_target = call_match.group(1) if call_match else None
    if call_target and not styles:
        styles.add("generic_helper_call")
    if not styles:
        styles.add("literal_reference")

    markers: set[str] = set()
    lowered = context.casefold()
    if "urlsearchparams" in lowered:
        markers.add("url_search_params")
    if re.search(r"\bparams\s*:", context, re.IGNORECASE):
        markers.add("params_object")
    if re.search(r"\bsearchparams\b", context, re.IGNORECASE):
        markers.add("search_params_identifier")
    if suffix.lstrip().startswith("?"):
        markers.add("literal_query_suffix")
    if re.search(r"^[^;\n]{0,80}\+", suffix):
        markers.add("string_concatenation_after_route")
    if re.search(r"\+[^;\n]{0,80}$", prefix):
        markers.add("string_concatenation_before_route")

    return {
        "call_styles": sorted(styles),
        "call_target": call_target,
        "method_candidates": sorted(methods),
        "query_construction_markers": sorted(markers),
        "dynamic_route_construction_observed": bool(markers),
    }


def inventory_guild_progression_usage_context(
    *,
    public_recovery_path: Path,
    private_recovery_path: Path,
    raw_root: Path,
    private_output_path: Path,
    receipt_output_path: Path,
    expected_guild_label: str = "Argentum",
    context_chars: int = _DEFAULT_CONTEXT_CHARS,
    max_occurrences: int = _DEFAULT_MAX_OCCURRENCES,
) -> dict[str, Any]:
    """Inventory SPA usage context without performing network requests or semantic promotion."""
    if context_chars < 128 or context_chars > 4096:
        raise ValueError("context_chars must be between 128 and 4096")
    if max_occurrences < 1 or max_occurrences > 100:
        raise ValueError("max_occurrences must be between 1 and 100")

    public, public_body = _load(public_recovery_path, "public profiled asset recovery")
    private, private_body = _load(private_recovery_path, "private profiled asset recovery")
    payload_hash = _validate_recovery(
        public,
        private,
        private_body=private_body,
        expected_guild_label=expected_guild_label,
    )
    asset_body, manifest_path = _load_asset(raw_root, payload_hash)
    normalized_text = asset_body.decode("utf-8", errors="ignore").replace("\\/", "/")
    positions: list[int] = []
    start = 0
    while True:
        position = normalized_text.find(_ROUTE, start)
        if position < 0:
            break
        positions.append(position)
        if len(positions) > max_occurrences:
            raise ValueError("progression route occurrence count exceeds bounded maximum")
        start = position + len(_ROUTE)
    if not positions:
        raise ValueError("progression route candidate was not found in recovered asset bytes")

    private_rows: list[dict[str, Any]] = []
    public_rows: list[dict[str, Any]] = []
    aggregate_methods: set[str] = set()
    aggregate_styles: set[str] = set()
    aggregate_markers: set[str] = set()
    for index, position in enumerate(positions, start=1):
        left = max(0, position - context_chars)
        right = min(len(normalized_text), position + len(_ROUTE) + context_chars)
        context = normalized_text[left:right]
        route_offset = position - left
        prefix = context[:route_offset]
        suffix = context[route_offset + len(_ROUTE) :]
        classification = _classify_context(prefix, suffix, context)
        aggregate_methods.update(classification["method_candidates"])
        aggregate_styles.update(classification["call_styles"])
        aggregate_markers.update(classification["query_construction_markers"])
        context_hash = _sha256(context.encode("utf-8"))
        private_rows.append(
            {
                "occurrence_index": index,
                "normalized_character_offset": position,
                "context": context,
                "context_sha256": context_hash,
                **classification,
            }
        )
        public_rows.append(
            {
                "occurrence_index": index,
                "context_sha256": context_hash,
                "context_character_count": len(context),
                "call_styles": classification["call_styles"],
                "method_candidates": classification["method_candidates"],
                "query_construction_markers": classification[
                    "query_construction_markers"
                ],
                "dynamic_route_construction_observed": classification[
                    "dynamic_route_construction_observed"
                ],
                "contains_raw_context": False,
                "contains_source_scalar_values": False,
            }
        )

    method_unambiguous = len(aggregate_methods) == 1 and all(
        len(row["method_candidates"]) == 1 for row in public_rows
    )
    query_shape_unambiguous = not aggregate_markers
    checks = {
        "public_profiled_recovery_verified": True,
        "public_recovery_integrity_checks_verified": True,
        "public_recovery_privacy_boundary_verified": True,
        "private_profiled_recovery_sha256_verified": True,
        "private_recovery_scalar_boundary_verified": True,
        "progression_route_candidate_bound_to_recovery": True,
        "asset_content_manifest_unique": True,
        "asset_content_manifest_verified": True,
        "asset_payload_path_confined_to_raw_root": True,
        "asset_payload_sha256_verified": True,
        "asset_uncompressed_byte_count_verified": True,
        "route_occurrence_count_bounded": True,
        "route_occurrence_observed": True,
        "raw_usage_context_kept_private": True,
        "public_receipt_contains_no_raw_context": True,
        "public_receipt_scalar_boundary_preserved": True,
        "network_requests_performed_false": True,
        "route_semantics_not_overclaimed": True,
        "pagination_not_overclaimed": True,
        "termination_not_overclaimed": True,
        "completeness_not_overclaimed": True,
        "full_crawl_remains_disabled": True,
        "planner_scoring_remains_disabled": True,
    }
    private_payload = {
        "schema_version": 1,
        "inventory_kind": _INVENTORY_PRIVATE_KIND,
        "inventory_version": _INVENTORY_VERSION,
        "generated_at": _generated_at(),
        "source_public_recovery_name": public_recovery_path.name,
        "source_public_recovery_sha256": _sha256(_canonical_lf(public_body)),
        "source_private_recovery_name": private_recovery_path.name,
        "source_private_recovery_sha256": _sha256(private_body),
        "asset_payload_hash": payload_hash,
        "asset_content_manifest_path": str(manifest_path),
        "route": _ROUTE,
        "occurrences": private_rows,
        "summary": {
            "occurrence_count": len(private_rows),
            "method_candidates": sorted(aggregate_methods),
            "call_style_candidates": sorted(aggregate_styles),
            "query_construction_markers": sorted(aggregate_markers),
            "contains_source_scalar_values": True,
            "network_requests_performed": False,
        },
    }
    private_inventory_body = _write(private_output_path, private_payload)

    receipt = {
        "schema_version": 1,
        "inventory_kind": _INVENTORY_KIND,
        "inventory_version": _INVENTORY_VERSION,
        "generated_at": _generated_at(),
        "source_public_recovery_name": public_recovery_path.name,
        "source_public_recovery_sha256": _sha256(_canonical_lf(public_body)),
        "source_private_recovery_name": private_recovery_path.name,
        "source_private_recovery_sha256": _sha256(private_body),
        "source_private_inventory_name": private_output_path.name,
        "source_private_inventory_sha256": _sha256(private_inventory_body),
        "target": {
            "guild_label": expected_guild_label,
            "route_template": _ROUTE,
            "asset_url_published": False,
            "source_guild_id_published": False,
            "raw_context_published": False,
            "source_scalar_values_published": False,
        },
        "request_contract": {
            "network_requests_performed": False,
            "raw_archive_only": True,
            "context_chars_per_side": context_chars,
            "max_occurrences": max_occurrences,
        },
        "usage_contexts": public_rows,
        "cross_occurrence_evidence": {
            "occurrence_count": len(public_rows),
            "method_candidates": sorted(aggregate_methods),
            "method_candidate_count": len(aggregate_methods),
            "method_candidate_unambiguous": method_unambiguous,
            "call_style_candidates": sorted(aggregate_styles),
            "query_construction_markers": sorted(aggregate_markers),
            "query_shape_candidate_unambiguous": query_shape_unambiguous,
            "contains_raw_context": False,
            "contains_source_scalar_values": False,
        },
        "integrity_checks": checks,
        "summary": {
            "all_integrity_checks_passed": all(checks.values()),
            "integrity_check_count": len(checks),
            "route_occurrence_count": len(public_rows),
            "method_candidate_count": len(aggregate_methods),
            "method_candidate_unambiguous": method_unambiguous,
            "query_shape_candidate_unambiguous": query_shape_unambiguous,
            "ready_for_guild_progression_usage_review": True,
            "ready_for_bounded_progression_route_probe": False,
            "guild_api_route_semantics_verified": False,
            "pagination_semantics_verified": False,
            "termination_semantics_verified": False,
            "completeness_verified": False,
            "ready_for_full_guild_crawl": False,
            "planner_scoring_allowed": False,
            "contains_raw_context": False,
            "contains_source_scalar_values": False,
            "network_requests_performed": False,
        },
        "decision_boundary": {
            "status": "guild_progression_usage_context_observed",
            "guild_progression_route_candidate_observed": True,
            "guild_progression_usage_context_observed": True,
            "ready_for_guild_progression_usage_review": True,
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
    }
    _write(receipt_output_path, receipt)
    return receipt


__all__ = ["inventory_guild_progression_usage_context"]
