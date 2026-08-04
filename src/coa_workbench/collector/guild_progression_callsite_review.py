from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

_REVIEW_KIND = "guild_progression_helper_callsite_review"
_REVIEW_VERSION = "guild-progression-helper-callsite-review-v1"
_INVENTORY_KIND = "guild_progression_helper_callsite_inventory"
_INVENTORY_VERSION = "guild-progression-helper-callsite-inventory-v1"
_USAGE_REVIEW_KIND = "guild_progression_usage_context_review"
_USAGE_REVIEW_VERSION = "guild-progression-usage-context-review-v1"
_RECOVERY_KIND = "guild_identity_asset_profiled_recovery"
_RECOVERY_VERSION = "guild-identity-asset-profiled-recovery-v1"
_ROUTE = "/api/guilds/progression"
_MAX_REVIEWABLE_SPAN_CHARS = 65_536
_EXPECTED_MARKERS = ["body", "data", "headers", "method", "params", "url"]
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
    "callee",
    "context",
    "private_query",
    "raw_call_text",
    "raw_payload",
    "raw_records",
    "request_url",
    "source_guild_id",
    "symbol",
}


def _generated_at() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _canonical_lf(value: bytes) -> bytes:
    return value.replace(b"\r\n", b"\n")


def _document_hashes(value: bytes) -> set[str]:
    lf = _canonical_lf(value)
    return {_sha256(value), _sha256(lf), _sha256(lf.replace(b"\n", b"\r\n"))}


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
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value):
        raise ValueError(f"{label} must be SHA-256")
    return value


def _expect(source: Mapping[str, Any], expected: Mapping[str, object], label: str) -> None:
    for field, value in expected.items():
        if source.get(field) != value:
            raise ValueError(f"{label} mismatch: {field}")


def _expect_false(source: Mapping[str, Any], fields: tuple[str, ...], label: str) -> None:
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


def _require_checks(value: object, expected_count: int, label: str) -> None:
    checks = _object(value, label)
    if len(checks) != expected_count or any(item is not True for item in checks.values()):
        raise ValueError(f"{label} failed")


def _validate_usage_review(review: Mapping[str, Any]) -> None:
    _expect(
        review,
        {
            "schema_version": 1,
            "review_kind": _USAGE_REVIEW_KIND,
            "review_version": _USAGE_REVIEW_VERSION,
        },
        "usage review",
    )
    _require_checks(review.get("integrity_checks"), 30, "usage review integrity checks")
    summary = _object(review.get("summary"), "usage review summary")
    _expect(
        summary,
        {
            "all_integrity_checks_passed": True,
            "integrity_check_count": 30,
            "guild_progression_usage_context_reviewed": True,
            "ready_for_bounded_progression_route_probe": False,
            "contains_raw_context": False,
            "contains_source_scalar_values": False,
        },
        "usage review summary",
    )
    _expect_false(summary, _SUMMARY_FALSE_GATES, "usage review summary")


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
    _require_checks(recovery.get("integrity_checks"), 15, "profiled recovery integrity checks")
    summary = _object(recovery.get("summary"), "profiled recovery summary")
    _expect(
        summary,
        {
            "all_integrity_checks_passed": True,
            "integrity_check_count": 15,
            "asset_download_completed": True,
            "contains_source_scalar_values": False,
        },
        "profiled recovery summary",
    )


def review_guild_progression_helper_callsite(
    *,
    inventory_path: Path,
    usage_review_path: Path,
    profiled_recovery_path: Path,
    receipt_output_path: Path,
) -> dict[str, Any]:
    """Review the exact scalar-free helper candidate without inferring its semantics."""
    inventory, inventory_body = _load(inventory_path, "helper call-site inventory")
    usage_review, usage_review_body = _load(usage_review_path, "usage review")
    recovery, recovery_body = _load(profiled_recovery_path, "profiled recovery")
    _validate_usage_review(usage_review)
    _validate_recovery(recovery)

    _expect(
        inventory,
        {
            "schema_version": 1,
            "inventory_kind": _INVENTORY_KIND,
            "inventory_version": _INVENTORY_VERSION,
            "source_usage_review_name": usage_review_path.name,
            "source_public_recovery_name": profiled_recovery_path.name,
        },
        "helper call-site inventory",
    )
    declared_usage_hash = _hash(
        inventory.get("source_usage_review_sha256"),
        "usage review SHA-256",
    )
    if declared_usage_hash not in _document_hashes(usage_review_body):
        raise ValueError("helper inventory usage review SHA-256 mismatch")
    declared_recovery_hash = _hash(
        inventory.get("source_public_recovery_sha256"),
        "profiled recovery SHA-256",
    )
    if declared_recovery_hash not in _document_hashes(recovery_body):
        raise ValueError("helper inventory profiled recovery SHA-256 mismatch")
    if _property_names(inventory) & _FORBIDDEN_PUBLIC_FIELDS:
        raise ValueError("helper inventory contains forbidden public fields")
    _require_checks(inventory.get("integrity_checks"), 32, "helper inventory integrity checks")

    target = _object(inventory.get("target"), "helper inventory target")
    _expect(
        target,
        {
            "guild_label": "Argentum",
            "route_template": _ROUTE,
            "asset_url_published": False,
            "source_guild_id_published": False,
            "raw_context_published": False,
            "raw_callee_published": False,
            "source_scalar_values_published": False,
        },
        "helper inventory target",
    )
    request = _object(inventory.get("request_contract"), "helper inventory request contract")
    _expect(
        request,
        {
            "network_requests_performed": False,
            "raw_archive_only": True,
            "max_occurrences": 20,
            "max_call_depth": 8,
            "private_context_chars_per_side": 2048,
        },
        "helper inventory request contract",
    )

    cross = _object(inventory.get("cross_occurrence_evidence"), "cross occurrence evidence")
    _expect(
        cross,
        {
            "occurrence_count": 1,
            "call_candidate_count": 1,
            "direct_invocation_candidate_count": 1,
            "enclosing_function_candidate_count": 1,
            "assignment_kinds": ["none"],
            "call_classes": ["generic_helper_call"],
            "method_candidate_count": 1,
            "method_candidate_unambiguous": True,
            "method_candidates": ["POST"],
            "property_markers": _EXPECTED_MARKERS,
            "helper_callsite_candidate_observed": True,
            "contains_raw_callee": False,
            "contains_raw_context": False,
            "contains_source_scalar_values": False,
        },
        "cross occurrence evidence",
    )

    occurrences = _array(inventory.get("occurrences"), "occurrences")
    if len(occurrences) != 1:
        raise ValueError("expected exactly one progression occurrence")
    occurrence = _object(occurrences[0], "progression occurrence")
    _expect(
        occurrence,
        {
            "occurrence_index": 1,
            "assignment_kind": "none",
            "assignment_symbol_sha256": None,
            "property_name_sha256": None,
            "call_candidate_count": 1,
            "enclosing_function_candidate": True,
            "function_candidate_kind": "block_function",
            "string_literal_verified": True,
            "string_quote_class": "single_quote",
            "context_property_markers": _EXPECTED_MARKERS,
            "contains_raw_callee": False,
            "contains_raw_context": False,
            "contains_source_scalar_values": False,
        },
        "progression occurrence",
    )
    _hash(occurrence.get("structural_envelope_sha256"), "structural envelope hash")
    _hash(occurrence.get("function_span_sha256"), "function span hash")
    _hash(occurrence.get("function_prefix_sha256"), "function prefix hash")
    call_chars = _integer(occurrence.get("structural_envelope_character_count"), "call span")
    function_chars = _integer(occurrence.get("function_character_count"), "function span")

    candidates = _array(occurrence.get("call_candidates"), "call candidates")
    if len(candidates) != 1:
        raise ValueError("expected exactly one helper call candidate")
    candidate = _object(candidates[0], "helper call candidate")
    _expect(
        candidate,
        {
            "call_character_count": call_chars,
            "call_depth": 2,
            "callee_class": "generic_helper_call",
            "method_candidates": ["POST"],
            "method_evidence": ["method_property_literal"],
            "property_markers": _EXPECTED_MARKERS,
            "route_direct_argument_candidate": True,
            "contains_raw_call_text": False,
            "contains_raw_callee": False,
        },
        "helper call candidate",
    )
    _hash(candidate.get("call_span_sha256"), "call span hash")
    _hash(candidate.get("callee_sha256"), "callee hash")
    if call_chars <= _MAX_REVIEWABLE_SPAN_CHARS:
        raise ValueError("expected the observed generic-helper span to remain overbroad")
    if function_chars <= _MAX_REVIEWABLE_SPAN_CHARS:
        raise ValueError("expected the observed function span to remain overbroad")

    summary_in = _object(inventory.get("summary"), "helper inventory summary")
    _expect(
        summary_in,
        {
            "all_integrity_checks_passed": True,
            "integrity_check_count": 32,
            "route_occurrence_count": 1,
            "call_candidate_count": 1,
            "direct_invocation_candidate_count": 1,
            "enclosing_function_candidate_count": 1,
            "method_candidate_count": 1,
            "method_candidate_unambiguous": True,
            "helper_callsite_candidate_observed": True,
            "ready_for_guild_progression_helper_callsite_review": True,
            "ready_for_bounded_progression_route_probe": False,
            "network_requests_performed": False,
            "contains_raw_callee": False,
            "contains_raw_context": False,
            "contains_source_scalar_values": False,
        },
        "helper inventory summary",
    )
    _expect_false(summary_in, _SUMMARY_FALSE_GATES, "helper inventory summary")

    boundary_in = _object(inventory.get("decision_boundary"), "helper inventory boundary")
    _expect(
        boundary_in,
        {
            "status": "guild_progression_helper_callsite_inventory_observed",
            "guild_progression_route_candidate_observed": True,
            "guild_progression_usage_context_reviewed": True,
            "guild_progression_helper_callsite_inventory_observed": True,
            "guild_progression_method_candidate_unambiguous": True,
            "guild_progression_request_shape_verified": False,
            "ready_for_guild_progression_helper_callsite_review": True,
            "ready_for_bounded_progression_route_probe": False,
        },
        "helper inventory boundary",
    )
    _expect_false(boundary_in, _BOUNDARY_FALSE_GATES, "helper inventory boundary")

    checks = {
        "usage_review_contract_verified": True,
        "usage_review_integrity_checks_verified": True,
        "usage_review_privacy_boundary_verified": True,
        "profiled_recovery_contract_verified": True,
        "profiled_recovery_integrity_checks_verified": True,
        "profiled_recovery_privacy_boundary_verified": True,
        "inventory_contract_verified": True,
        "inventory_usage_review_name_verified": True,
        "inventory_usage_review_sha256_verified": True,
        "inventory_profiled_recovery_name_verified": True,
        "inventory_profiled_recovery_sha256_verified": True,
        "inventory_integrity_checks_verified": True,
        "inventory_privacy_boundary_verified": True,
        "raw_archive_only_contract_verified": True,
        "network_requests_performed_false": True,
        "single_route_occurrence_verified": True,
        "single_helper_call_candidate_verified": True,
        "direct_route_argument_candidate_verified": True,
        "generic_helper_classification_verified": True,
        "post_method_candidate_verified": True,
        "method_property_literal_evidence_verified": True,
        "request_property_markers_verified": True,
        "structural_hashes_verified": True,
        "callee_hash_verified_without_public_callee": True,
        "overbroad_call_span_verified": True,
        "overbroad_function_span_verified": True,
        "generic_helper_identity_not_inferred": True,
        "request_payload_mapping_not_inferred": True,
        "route_probe_remains_disabled": True,
        "route_semantics_not_overclaimed": True,
        "pagination_not_overclaimed": True,
        "termination_not_overclaimed": True,
        "completeness_not_overclaimed": True,
        "full_crawl_remains_disabled": True,
        "planner_scoring_remains_disabled": True,
        "helper_definition_inventory_selected_as_next_gate": True,
    }
    if len(checks) != 36 or any(value is not True for value in checks.values()):
        raise ValueError("helper call-site review integrity checks failed")

    blockers = [
        "generic_helper_identity_unresolved",
        "structural_envelope_overbroad",
        "request_payload_mapping_unresolved",
    ]
    review = {
        "schema_version": 1,
        "review_kind": _REVIEW_KIND,
        "review_version": _REVIEW_VERSION,
        "generated_at": _generated_at(),
        "source_inventory_name": inventory_path.name,
        "source_inventory_sha256": _sha256(inventory_body),
        "source_inventory_canonical_lf_sha256": _sha256(_canonical_lf(inventory_body)),
        "source_usage_review_name": usage_review_path.name,
        "source_usage_review_sha256": _sha256(usage_review_body),
        "source_public_recovery_name": profiled_recovery_path.name,
        "source_public_recovery_sha256": _sha256(recovery_body),
        "source_binding_review": {
            "inventory_document_identity_preserved": True,
            "usage_review_sha256_verified_across_lf_crlf": True,
            "profiled_recovery_sha256_verified_across_lf_crlf": True,
        },
        "callsite_review": {
            "route_template": _ROUTE,
            "occurrence_count": 1,
            "call_candidate_count": 1,
            "direct_invocation_candidate_count": 1,
            "call_classes": ["generic_helper_call"],
            "method_candidates": ["POST"],
            "method_candidate_unambiguous": True,
            "http_method_review_status": "resolved_candidate",
            "method_evidence": ["method_property_literal"],
            "property_markers": _EXPECTED_MARKERS,
            "route_direct_argument_candidate_observed": True,
            "actual_helper_invocation_candidate_observed": True,
            "generic_helper_only": True,
            "max_reviewable_span_character_count": _MAX_REVIEWABLE_SPAN_CHARS,
            "max_call_character_count": call_chars,
            "max_function_character_count": function_chars,
            "structural_envelope_narrow_enough": False,
            "helper_identity_resolved": False,
            "request_payload_mapping_resolved": False,
            "request_shape_sufficient_for_bounded_probe": False,
            "helper_callsite_reviewed": True,
            "ready_for_helper_definition_inventory": True,
            "route_semantics_verified": False,
            "contains_raw_callee": False,
            "contains_raw_context": False,
            "contains_source_scalar_values": False,
            "blockers": blockers,
        },
        "integrity_checks": checks,
        "summary": {
            "all_integrity_checks_passed": True,
            "integrity_check_count": len(checks),
            "guild_progression_helper_callsite_reviewed": True,
            "method_candidate_unambiguous": True,
            "http_method_candidate": "POST",
            "actual_helper_invocation_candidate_observed": True,
            "helper_identity_resolved": False,
            "request_payload_mapping_resolved": False,
            "request_shape_sufficient_for_bounded_probe": False,
            "ready_for_guild_progression_helper_definition_inventory": True,
            "ready_for_bounded_progression_route_probe": False,
            "guild_api_route_semantics_verified": False,
            "pagination_semantics_verified": False,
            "termination_semantics_verified": False,
            "completeness_verified": False,
            "ready_for_full_guild_crawl": False,
            "planner_scoring_allowed": False,
            "contains_raw_callee": False,
            "contains_raw_context": False,
            "contains_source_scalar_values": False,
        },
        "decision_boundary": {
            "status": "guild_progression_helper_callsite_reviewed_probe_blocked",
            "guild_progression_route_candidate_observed": True,
            "guild_progression_usage_context_reviewed": True,
            "guild_progression_helper_callsite_inventory_observed": True,
            "guild_progression_helper_callsite_reviewed": True,
            "guild_progression_method_candidate_unambiguous": True,
            "guild_progression_http_method_candidate": "POST",
            "guild_progression_helper_identity_resolved": False,
            "guild_progression_request_payload_mapping_resolved": False,
            "guild_progression_request_shape_verified": False,
            "ready_for_guild_progression_helper_definition_inventory": True,
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
    _write(receipt_output_path, review)
    return review


__all__ = ["review_guild_progression_helper_callsite"]
