from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

_REVIEW_KIND = "guild_progression_usage_context_review"
_REVIEW_VERSION = "guild-progression-usage-context-review-v1"
_INVENTORY_KIND = "guild_progression_usage_context_inventory"
_INVENTORY_VERSION = "guild-progression-usage-context-inventory-v1"
_RECOVERY_KIND = "guild_identity_asset_profiled_recovery"
_RECOVERY_VERSION = "guild-identity-asset-profiled-recovery-v1"
_ROUTE = "/api/guilds/progression"
_SUMMARY_FALSE_GATES = (
    "guild_api_route_semantics_verified",
    "pagination_semantics_verified",
    "termination_semantics_verified",
    "completeness_verified",
    "ready_for_full_guild_crawl",
    "planner_scoring_allowed",
)
_BOUNDARY_FALSE_GATES = (
    "guild_api_route_semantics_verified",
    "pagination_semantics_verified",
    "termination_semantics_verified",
    "completeness_verified",
    "automatic_full_guild_crawl_allowed",
    "ready_for_full_guild_crawl",
    "ready_for_multi_report_character_graph",
    "ready_for_performance_model",
    "ready_for_bis25_scoring",
    "planner_scoring_allowed",
)
_FORBIDDEN_PUBLIC_FIELDS = {
    "asset_url",
    "call_target",
    "context",
    "private_query",
    "raw_payload",
    "raw_records",
    "request_url",
    "source_guild_id",
}


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


def _write(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    body = (json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_bytes(body)
    temporary.replace(path)


def _object(value: object, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    return value


def _array(value: object, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"{label} must be an array")
    return value


def _integer(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{label} must be an integer")
    return value


def _hash(value: object, label: str) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise ValueError(f"{label} must be SHA-256")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{label} must be hexadecimal") from exc
    return value


def _string_array(value: object, label: str) -> list[str]:
    rows = _array(value, label)
    if any(not isinstance(row, str) or not row for row in rows):
        raise ValueError(f"{label} must contain non-empty strings")
    if rows != sorted(set(rows)):
        raise ValueError(f"{label} must be sorted and unique")
    return rows


def _expect(source: Mapping[str, Any], expected: Mapping[str, object], label: str) -> None:
    for field, value in expected.items():
        if source.get(field) != value:
            raise ValueError(f"{label} mismatch: {field}")


def _expect_false_gates(
    source: Mapping[str, Any],
    fields: tuple[str, ...],
    label: str,
) -> None:
    _expect(source, {field: False for field in fields}, label)


def _property_names(value: object) -> set[str]:
    if isinstance(value, dict):
        names = set(value)
        for child in value.values():
            names.update(_property_names(child))
        return names
    if isinstance(value, list):
        names: set[str] = set()
        for child in value:
            names.update(_property_names(child))
        return names
    return set()


def _validate_recovery(recovery: Mapping[str, Any]) -> None:
    _expect(
        recovery,
        {
            "schema_version": 1,
            "recovery_kind": _RECOVERY_KIND,
            "recovery_version": _RECOVERY_VERSION,
        },
        "profiled recovery",
    )
    target = _object(recovery.get("target"), "profiled recovery target")
    _expect(
        target,
        {
            "guild_label": "Argentum",
            "asset_url_published": False,
            "source_guild_id_published": False,
        },
        "profiled recovery target",
    )
    routes = _object(recovery.get("route_inventory"), "profiled recovery route inventory")
    shapes = _string_array(routes.get("guild_api_route_shapes"), "profiled recovery route shapes")
    if _ROUTE not in shapes:
        raise ValueError("profiled recovery does not contain progression route candidate")
    checks = _object(recovery.get("integrity_checks"), "profiled recovery integrity_checks")
    if len(checks) != 15 or any(value is not True for value in checks.values()):
        raise ValueError("profiled recovery integrity checks failed")
    summary = _object(recovery.get("summary"), "profiled recovery summary")
    _expect(
        summary,
        {
            "all_integrity_checks_passed": True,
            "asset_download_completed": True,
            "contains_source_scalar_values": False,
            "guild_api_route_candidate_count": 3,
            "integrity_check_count": 15,
        },
        "profiled recovery summary",
    )
    boundary = _object(recovery.get("decision_boundary"), "profiled recovery boundary")
    _expect(
        boundary,
        {
            "guild_api_route_candidates_observed": True,
            "guild_api_route_semantics_verified": False,
            "ready_for_guild_api_route_review": True,
            "ready_for_full_guild_crawl": False,
            "planner_scoring_allowed": False,
        },
        "profiled recovery boundary",
    )


def _validate_contexts(
    inventory: Mapping[str, Any],
    cross: Mapping[str, Any],
) -> tuple[list[dict[str, Any]], set[str], set[str], set[str]]:
    rows = [
        _object(row, "usage context")
        for row in _array(inventory.get("usage_contexts"), "usage_contexts")
    ]
    occurrence_count = _integer(cross.get("occurrence_count"), "occurrence_count")
    if occurrence_count < 1 or occurrence_count > 20 or len(rows) != occurrence_count:
        raise ValueError("usage context occurrence count mismatch")

    methods: set[str] = set()
    styles: set[str] = set()
    markers: set[str] = set()
    expected_indexes = list(range(1, occurrence_count + 1))
    actual_indexes: list[int] = []
    for row in rows:
        index = _integer(row.get("occurrence_index"), "usage_context.occurrence_index")
        actual_indexes.append(index)
        _hash(row.get("context_sha256"), "usage_context.context_sha256")
        character_count = _integer(
            row.get("context_character_count"),
            "usage_context.context_character_count",
        )
        if character_count < 1 or character_count > 8192:
            raise ValueError("usage context character count is out of bounds")
        _expect(
            row,
            {
                "contains_raw_context": False,
                "contains_source_scalar_values": False,
            },
            "usage context privacy boundary",
        )
        row_methods = _string_array(row.get("method_candidates"), "usage context methods")
        row_styles = _string_array(row.get("call_styles"), "usage context call styles")
        row_markers = _string_array(
            row.get("query_construction_markers"),
            "usage context query markers",
        )
        methods.update(row_methods)
        styles.update(row_styles)
        markers.update(row_markers)
    if actual_indexes != expected_indexes:
        raise ValueError("usage context indexes must be contiguous")
    return rows, methods, styles, markers


def review_guild_progression_usage_context(
    *,
    inventory_path: Path,
    profiled_recovery_path: Path,
    receipt_output_path: Path,
) -> dict[str, Any]:
    """Review scalar-free SPA usage evidence without guessing route semantics."""
    inventory, inventory_body = _load(inventory_path, "guild progression usage inventory")
    recovery, recovery_body = _load(profiled_recovery_path, "profiled asset recovery")
    _validate_recovery(recovery)

    _expect(
        inventory,
        {
            "schema_version": 1,
            "inventory_kind": _INVENTORY_KIND,
            "inventory_version": _INVENTORY_VERSION,
            "source_public_recovery_name": profiled_recovery_path.name,
        },
        "usage inventory",
    )
    declared_recovery_hash = _hash(
        inventory.get("source_public_recovery_sha256"),
        "inventory.source_public_recovery_sha256",
    )
    if declared_recovery_hash not in _document_hashes(recovery_body):
        raise ValueError("usage inventory profiled recovery SHA-256 mismatch")

    target = _object(inventory.get("target"), "usage inventory target")
    _expect(
        target,
        {
            "guild_label": "Argentum",
            "route_template": _ROUTE,
            "asset_url_published": False,
            "source_guild_id_published": False,
            "raw_context_published": False,
            "source_scalar_values_published": False,
        },
        "usage inventory target",
    )
    request = _object(inventory.get("request_contract"), "usage inventory request contract")
    _expect(
        request,
        {
            "network_requests_performed": False,
            "raw_archive_only": True,
        },
        "usage inventory request contract",
    )
    max_occurrences = _integer(request.get("max_occurrences"), "request max_occurrences")
    if max_occurrences < 1 or max_occurrences > 100:
        raise ValueError("request max_occurrences is out of bounds")
    context_chars = _integer(request.get("context_chars_per_side"), "request context chars")
    if context_chars < 128 or context_chars > 4096:
        raise ValueError("request context chars is out of bounds")

    checks_in = _object(inventory.get("integrity_checks"), "usage inventory integrity_checks")
    if len(checks_in) != 23 or any(value is not True for value in checks_in.values()):
        raise ValueError("usage inventory integrity checks failed")
    if _property_names(inventory) & _FORBIDDEN_PUBLIC_FIELDS:
        raise ValueError("usage inventory contains forbidden public fields")

    cross = _object(inventory.get("cross_occurrence_evidence"), "cross occurrence evidence")
    rows, methods, styles, markers = _validate_contexts(inventory, cross)
    aggregate_methods = _string_array(cross.get("method_candidates"), "aggregate methods")
    aggregate_styles = _string_array(cross.get("call_style_candidates"), "aggregate call styles")
    aggregate_markers = _string_array(
        cross.get("query_construction_markers"),
        "aggregate query markers",
    )
    if aggregate_methods != sorted(methods):
        raise ValueError("aggregate method candidates do not match contexts")
    if aggregate_styles != sorted(styles):
        raise ValueError("aggregate call styles do not match contexts")
    if aggregate_markers != sorted(markers):
        raise ValueError("aggregate query markers do not match contexts")
    method_unambiguous = len(methods) == 1 and all(
        len(_array(row.get("method_candidates"), "usage context methods")) == 1
        for row in rows
    )
    if cross.get("method_candidate_count") != len(methods):
        raise ValueError("aggregate method candidate count mismatch")
    if cross.get("method_candidate_unambiguous") is not method_unambiguous:
        raise ValueError("aggregate method ambiguity mismatch")
    query_candidate_unambiguous = not markers
    if cross.get("query_shape_candidate_unambiguous") is not query_candidate_unambiguous:
        raise ValueError("aggregate query-shape ambiguity mismatch")
    _expect(
        cross,
        {
            "contains_raw_context": False,
            "contains_source_scalar_values": False,
        },
        "cross occurrence privacy boundary",
    )

    summary_in = _object(inventory.get("summary"), "usage inventory summary")
    _expect(
        summary_in,
        {
            "all_integrity_checks_passed": True,
            "integrity_check_count": 23,
            "network_requests_performed": False,
            "contains_raw_context": False,
            "contains_source_scalar_values": False,
            "route_occurrence_count": len(rows),
            "method_candidate_count": len(methods),
            "method_candidate_unambiguous": method_unambiguous,
            "query_shape_candidate_unambiguous": query_candidate_unambiguous,
            "ready_for_guild_progression_usage_review": True,
            "ready_for_bounded_progression_route_probe": False,
        },
        "usage inventory summary",
    )
    _expect_false_gates(summary_in, _SUMMARY_FALSE_GATES, "usage inventory summary")

    boundary_in = _object(inventory.get("decision_boundary"), "usage inventory boundary")
    _expect(
        boundary_in,
        {
            "status": "guild_progression_usage_context_observed",
            "guild_progression_route_candidate_observed": True,
            "guild_progression_usage_context_observed": True,
            "ready_for_guild_progression_usage_review": True,
            "ready_for_bounded_progression_route_probe": False,
        },
        "usage inventory boundary",
    )
    _expect_false_gates(boundary_in, _BOUNDARY_FALSE_GATES, "usage inventory boundary")

    invocation_styles = {"fetch_call", "member_http_method_call", "generic_helper_call"}
    actual_invocation_observed = bool(styles & invocation_styles)
    literal_reference_only = styles == {"literal_reference"}
    request_shape_sufficient_for_probe = (
        method_unambiguous and query_candidate_unambiguous and actual_invocation_observed
    )
    blockers: list[str] = []
    if not method_unambiguous:
        blockers.append("http_method_unresolved")
    if literal_reference_only:
        blockers.append("literal_reference_without_call_site")
    if not actual_invocation_observed:
        blockers.append("invocation_shape_unresolved")
    if not query_candidate_unambiguous:
        blockers.append("query_construction_ambiguous")

    checks = {
        "profiled_recovery_contract_verified": True,
        "profiled_recovery_integrity_checks_verified": True,
        "profiled_recovery_privacy_boundary_verified": True,
        "progression_route_candidate_bound_to_recovery": True,
        "inventory_contract_verified": True,
        "inventory_recovery_name_verified": True,
        "inventory_recovery_sha256_verified": True,
        "inventory_integrity_checks_verified": True,
        "inventory_privacy_boundary_verified": True,
        "raw_archive_only_contract_verified": True,
        "network_requests_performed_false": True,
        "route_occurrence_observed": len(rows) >= 1,
        "route_occurrence_count_bounded": len(rows) <= max_occurrences,
        "usage_context_indexes_contiguous": True,
        "usage_context_hashes_verified": True,
        "usage_context_raw_text_not_published": True,
        "usage_context_source_scalars_not_published": True,
        "aggregate_method_candidates_verified": aggregate_methods == sorted(methods),
        "aggregate_call_styles_verified": aggregate_styles == sorted(styles),
        "aggregate_query_markers_verified": aggregate_markers == sorted(markers),
        "method_ambiguity_preserved": cross.get("method_candidate_unambiguous")
        is method_unambiguous,
        "query_candidate_ambiguity_preserved": cross.get(
            "query_shape_candidate_unambiguous"
        )
        is query_candidate_unambiguous,
        "usage_context_reviewed_without_semantic_promotion": True,
        "unresolved_method_blocks_probe": method_unambiguous
        or not request_shape_sufficient_for_probe,
        "literal_reference_does_not_imply_http_method": not literal_reference_only
        or not method_unambiguous,
        "route_semantics_not_overclaimed": True,
        "pagination_not_overclaimed": True,
        "termination_not_overclaimed": True,
        "completeness_not_overclaimed": True,
        "full_crawl_and_scoring_remain_disabled": True,
    }
    if len(checks) != 30 or any(value is not True for value in checks.values()):
        failed = sorted(name for name, value in checks.items() if value is not True)
        raise ValueError(f"usage review integrity checks failed: {failed}")

    review = {
        "schema_version": 1,
        "review_kind": _REVIEW_KIND,
        "review_version": _REVIEW_VERSION,
        "generated_at": _generated_at(),
        "source_inventory_name": inventory_path.name,
        "source_inventory_sha256": _sha256(inventory_body),
        "source_inventory_canonical_lf_sha256": _sha256(_canonical_lf(inventory_body)),
        "source_public_recovery_name": profiled_recovery_path.name,
        "source_public_recovery_sha256": _sha256(recovery_body),
        "source_binding_review": {
            "inventory_document_identity_preserved": True,
            "profiled_recovery_name_verified": True,
            "profiled_recovery_sha256_verified_across_lf_crlf": True,
        },
        "usage_review": {
            "route_template": _ROUTE,
            "occurrence_count": len(rows),
            "call_style_candidates": aggregate_styles,
            "method_candidates": aggregate_methods,
            "method_candidate_unambiguous": method_unambiguous,
            "method_resolution_status": "resolved" if method_unambiguous else "unresolved",
            "query_construction_markers": aggregate_markers,
            "query_shape_candidate_unambiguous": query_candidate_unambiguous,
            "actual_invocation_observed": actual_invocation_observed,
            "literal_reference_only": literal_reference_only,
            "request_shape_sufficient_for_bounded_probe": request_shape_sufficient_for_probe,
            "usage_context_reviewed": True,
            "route_semantics_verified": False,
            "contains_raw_context": False,
            "contains_source_scalar_values": False,
            "blockers": blockers,
        },
        "integrity_checks": checks,
        "summary": {
            "all_integrity_checks_passed": True,
            "integrity_check_count": len(checks),
            "guild_progression_usage_context_reviewed": True,
            "method_candidate_unambiguous": method_unambiguous,
            "actual_invocation_observed": actual_invocation_observed,
            "request_shape_sufficient_for_bounded_probe": request_shape_sufficient_for_probe,
            "ready_for_bounded_progression_route_probe": request_shape_sufficient_for_probe,
            "guild_api_route_semantics_verified": False,
            "pagination_semantics_verified": False,
            "termination_semantics_verified": False,
            "completeness_verified": False,
            "ready_for_full_guild_crawl": False,
            "planner_scoring_allowed": False,
            "contains_raw_context": False,
            "contains_source_scalar_values": False,
        },
        "decision_boundary": {
            "status": (
                "guild_progression_usage_reviewed_probe_ready"
                if request_shape_sufficient_for_probe
                else "guild_progression_usage_reviewed_probe_blocked"
            ),
            "guild_progression_route_candidate_observed": True,
            "guild_progression_usage_context_observed": True,
            "guild_progression_usage_context_reviewed": True,
            "guild_progression_method_candidate_unambiguous": method_unambiguous,
            "guild_progression_request_shape_verified": False,
            "ready_for_bounded_progression_route_probe": request_shape_sufficient_for_probe,
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
    _write(receipt_output_path, review)
    return review
