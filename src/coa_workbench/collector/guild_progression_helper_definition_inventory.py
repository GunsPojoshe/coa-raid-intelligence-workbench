from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Mapping

from .guild_progression_callsite_contract import (
    array_value,
    canonical_lf,
    document_hashes,
    expect,
    generated_at,
    load_asset,
    load_json,
    object_value,
    property_names,
    require_checks,
    sha256,
    sha256_value,
    validate_recovery,
    write_json,
)
from .guild_progression_helper_definition_index import definition_candidates

KIND = "guild_progression_helper_definition_inventory"
PRIVATE_KIND = f"{KIND}_private"
VERSION = "guild-progression-helper-definition-inventory-v1"
ROUTE = "/api/guilds/progression"
_CALLSITE_KIND = "guild_progression_helper_callsite_inventory"
_CALLSITE_PRIVATE_KIND = f"{_CALLSITE_KIND}_private"
_CALLSITE_VERSION = "guild-progression-helper-callsite-inventory-v1"
_REVIEW_KIND = "guild_progression_helper_callsite_review"
_REVIEW_VERSION = "guild-progression-helper-callsite-review-v1"
_CALLEE_PATTERN = re.compile(
    r"[A-Za-z_$][A-Za-z0-9_$]*(?:\.[A-Za-z_$][A-Za-z0-9_$]*)*"
)
_FORBIDDEN_PUBLIC_FIELDS = {
    "alias_target",
    "asset_url",
    "callee",
    "context",
    "private_query",
    "raw_callee",
    "raw_definition",
    "raw_payload",
    "raw_records",
    "request_url",
    "source_guild_id",
    "span",
    "symbol",
}
_FALSE_GATES = {
    "ready_for_bounded_progression_route_probe": False,
    "guild_api_route_semantics_verified": False,
    "pagination_semantics_verified": False,
    "termination_semantics_verified": False,
    "completeness_verified": False,
    "ready_for_full_guild_crawl": False,
    "planner_scoring_allowed": False,
}


def _validate_callsite_review(review: Mapping[str, Any]) -> None:
    expect(
        review,
        {
            "schema_version": 1,
            "review_kind": _REVIEW_KIND,
            "review_version": _REVIEW_VERSION,
        },
        "call-site review",
    )
    require_checks(review.get("integrity_checks"), 36, "call-site review integrity checks")
    summary = object_value(review.get("summary"), "call-site review summary")
    expect(
        summary,
        {
            "all_integrity_checks_passed": True,
            "integrity_check_count": 36,
            "guild_progression_helper_callsite_reviewed": True,
            "method_candidate_unambiguous": True,
            "http_method_candidate": "POST",
            "helper_identity_resolved": False,
            "request_payload_mapping_resolved": False,
            "request_shape_sufficient_for_bounded_probe": False,
            "ready_for_guild_progression_helper_definition_inventory": True,
            **_FALSE_GATES,
            "contains_raw_callee": False,
            "contains_raw_context": False,
            "contains_source_scalar_values": False,
        },
        "call-site review summary",
    )
    if property_names(review) & _FORBIDDEN_PUBLIC_FIELDS:
        raise ValueError("call-site review contains forbidden public fields")


def _validate_public_callsite(value: Mapping[str, Any]) -> None:
    expect(
        value,
        {
            "schema_version": 1,
            "inventory_kind": _CALLSITE_KIND,
            "inventory_version": _CALLSITE_VERSION,
        },
        "public call-site inventory",
    )
    require_checks(value.get("integrity_checks"), 32, "public call-site checks")
    summary = object_value(value.get("summary"), "public call-site summary")
    expect(
        summary,
        {
            "all_integrity_checks_passed": True,
            "integrity_check_count": 32,
            "route_occurrence_count": 1,
            "call_candidate_count": 1,
            "direct_invocation_candidate_count": 1,
            "method_candidate_count": 1,
            "method_candidate_unambiguous": True,
            "ready_for_guild_progression_helper_callsite_review": True,
            **_FALSE_GATES,
            "contains_raw_context": False,
            "contains_raw_callee": False,
            "contains_source_scalar_values": False,
            "network_requests_performed": False,
        },
        "public call-site summary",
    )
    if property_names(value) & _FORBIDDEN_PUBLIC_FIELDS:
        raise ValueError("public call-site inventory contains forbidden public fields")


def _extract_callee(
    public_inventory: Mapping[str, Any],
    private_inventory: Mapping[str, Any],
) -> tuple[str, str]:
    expect(
        private_inventory,
        {
            "schema_version": 1,
            "inventory_kind": _CALLSITE_PRIVATE_KIND,
            "inventory_version": _CALLSITE_VERSION,
            "route": ROUTE,
        },
        "private call-site inventory",
    )
    public_occurrences = array_value(public_inventory.get("occurrences"), "public occurrences")
    private_occurrences = array_value(private_inventory.get("occurrences"), "private occurrences")
    if len(public_occurrences) != 1 or len(private_occurrences) != 1:
        raise ValueError("expected one public/private call-site occurrence")
    public_calls = array_value(
        object_value(public_occurrences[0], "public occurrence").get("call_candidates"),
        "public calls",
    )
    private_calls = array_value(
        object_value(private_occurrences[0], "private occurrence").get("call_candidates"),
        "private calls",
    )
    if len(public_calls) != 1 or len(private_calls) != 1:
        raise ValueError("expected one public/private helper call")
    public_call = object_value(public_calls[0], "public helper call")
    private_call = object_value(private_calls[0], "private helper call")
    expect(
        public_call,
        {
            "callee_class": "generic_helper_call",
            "method_candidates": ["POST"],
            "method_evidence": ["method_property_literal"],
            "route_direct_argument_candidate": True,
            "contains_raw_callee": False,
            "contains_raw_call_text": False,
        },
        "public helper call",
    )
    if private_call.get("class") != "generic_helper_call":
        raise ValueError("private helper call class mismatch")
    callee = private_call.get("callee")
    if not isinstance(callee, str) or not _CALLEE_PATTERN.fullmatch(callee):
        raise ValueError("private helper callee is missing or malformed")
    callee_hash = sha256_value(public_call.get("callee_sha256"), "public callee SHA-256")
    if sha256(callee.encode()) != callee_hash:
        raise ValueError("private helper callee hash mismatch")
    return callee, callee_hash


def _checks() -> dict[str, bool]:
    names = (
        "callsite_review_contract_verified callsite_review_integrity_checks_verified "
        "callsite_review_probe_blocked_boundary_verified public_callsite_contract_verified "
        "public_callsite_integrity_checks_verified public_callsite_privacy_boundary_verified "
        "callsite_review_public_inventory_binding_verified private_callsite_sha256_verified "
        "private_callsite_contract_verified public_private_occurrence_alignment_verified "
        "public_private_call_alignment_verified private_callee_hash_verified "
        "generic_helper_classification_verified post_method_candidate_verified "
        "public_profiled_recovery_verified private_profiled_recovery_sha256_verified "
        "asset_payload_sha256_verified asset_payload_path_confined_to_raw_root "
        "helper_symbol_scan_bounded helper_definition_scan_bounded definition_span_bounded "
        "raw_helper_definition_kept_private raw_alias_target_kept_private "
        "public_receipt_contains_no_raw_callee public_receipt_contains_no_raw_definition "
        "public_receipt_contains_no_alias_target public_receipt_scalar_boundary_preserved "
        "network_requests_performed_false route_probe_remains_disabled "
        "route_semantics_not_overclaimed pagination_not_overclaimed "
        "termination_not_overclaimed completeness_not_overclaimed "
        "full_crawl_remains_disabled planner_scoring_remains_disabled "
        "helper_definition_review_selected_as_next_gate"
    ).split()
    checks = {name: True for name in names}
    if len(checks) != 36:
        raise RuntimeError("helper-definition integrity-check contract drift")
    return checks


def inventory_guild_progression_helper_definition(
    *,
    callsite_review_path: Path,
    public_callsite_path: Path,
    private_callsite_path: Path,
    public_recovery_path: Path,
    private_recovery_path: Path,
    raw_root: Path,
    private_output_path: Path,
    receipt_output_path: Path,
    expected_guild_label: str = "Argentum",
    max_symbol_occurrences: int = 500,
    max_definition_candidates: int = 50,
    max_definition_span_chars: int = 131072,
    private_context_chars: int = 4096,
) -> dict[str, Any]:
    if not 512 <= private_context_chars <= 32768:
        raise ValueError("private_context_chars must be between 512 and 32768")
    review, review_body = load_json(callsite_review_path, "call-site review")
    public_callsite, public_callsite_body = load_json(public_callsite_path, "public call-site")
    private_callsite, private_callsite_body = load_json(private_callsite_path, "private call-site")
    public_recovery, public_recovery_body = load_json(public_recovery_path, "public recovery")
    private_recovery, private_recovery_body = load_json(private_recovery_path, "private recovery")
    _validate_callsite_review(review)
    _validate_public_callsite(public_callsite)

    declared_public = sha256_value(
        review.get("source_inventory_sha256"),
        "review inventory SHA-256",
    )
    if declared_public not in document_hashes(public_callsite_body):
        raise ValueError("call-site review public inventory SHA-256 mismatch")
    declared_private = sha256_value(
        public_callsite.get("source_private_inventory_sha256"),
        "public call-site private inventory SHA-256",
    )
    if declared_private not in document_hashes(private_callsite_body):
        raise ValueError("private call-site inventory SHA-256 mismatch")
    callee, callee_hash = _extract_callee(public_callsite, private_callsite)

    payload_hash = validate_recovery(
        public_recovery,
        private_recovery,
        private_recovery_body,
        expected_guild_label,
    )
    private_payload_hash = sha256_value(
        private_callsite.get("asset_payload_hash"),
        "private call-site asset SHA-256",
    )
    if private_payload_hash != payload_hash:
        raise ValueError("private call-site asset payload mismatch")
    asset_body, manifest_path = load_asset(raw_root, payload_hash)
    text = asset_body.decode("utf-8", errors="ignore").replace("\\/", "/")
    private_rows, evidence = definition_candidates(
        text,
        callee,
        max_symbol_occurrences=max_symbol_occurrences,
        max_candidates=max_definition_candidates,
        max_span_chars=max_definition_span_chars,
    )

    private_candidates = []
    public_candidates = []
    for index, row in enumerate(private_rows, 1):
        start, end = int(row["start"]), int(row["end"])
        excerpt_start = max(0, start - private_context_chars)
        excerpt_end = min(len(text), end + private_context_chars)
        private_candidates.append(
            {
                **row,
                "candidate_index": index,
                "private_excerpt": text[excerpt_start:excerpt_end],
                "private_excerpt_start": excerpt_start,
                "private_excerpt_end": excerpt_end,
            }
        )
        public_candidates.append(
            {
                "candidate_index": index,
                "definition_kind": row["kind"],
                "binding_scope": row["binding_scope"],
                "definition_span_sha256": row["span_sha256"],
                "definition_character_count": row["character_count"],
                "definition_prefix_sha256": row["prefix_sha256"],
                "parameter_count": row["parameter_count"],
                "async_candidate": row["async_candidate"],
                "marker_classes": row["marker_classes"],
                "alias_target_sha256": row["alias_target_sha256"],
                "contains_raw_callee": False,
                "contains_raw_definition": False,
                "contains_alias_target": False,
                "contains_source_scalar_values": False,
            }
        )

    private_payload = {
        "schema_version": 1,
        "inventory_kind": PRIVATE_KIND,
        "inventory_version": VERSION,
        "generated_at": generated_at(),
        "source_callsite_review_name": callsite_review_path.name,
        "source_callsite_review_sha256": sha256(review_body),
        "source_public_callsite_name": public_callsite_path.name,
        "source_public_callsite_sha256": sha256(public_callsite_body),
        "source_private_callsite_name": private_callsite_path.name,
        "source_private_callsite_sha256": sha256(private_callsite_body),
        "asset_payload_hash": payload_hash,
        "asset_content_manifest_path": str(manifest_path),
        "route": ROUTE,
        "callee": callee,
        "callee_sha256": callee_hash,
        "definition_candidates": private_candidates,
        "summary": {
            **evidence,
            "contains_source_scalar_values": True,
            "network_requests_performed": False,
        },
    }
    private_body_out = write_json(private_output_path, private_payload)

    checks = _checks()
    receipt = {
        "schema_version": 1,
        "inventory_kind": KIND,
        "inventory_version": VERSION,
        "generated_at": generated_at(),
        "source_callsite_review_name": callsite_review_path.name,
        "source_callsite_review_sha256": sha256(canonical_lf(review_body)),
        "source_public_callsite_name": public_callsite_path.name,
        "source_public_callsite_sha256": sha256(canonical_lf(public_callsite_body)),
        "source_private_callsite_name": private_callsite_path.name,
        "source_private_callsite_sha256": sha256(private_callsite_body),
        "source_public_recovery_name": public_recovery_path.name,
        "source_public_recovery_sha256": sha256(canonical_lf(public_recovery_body)),
        "source_private_recovery_name": private_recovery_path.name,
        "source_private_recovery_sha256": sha256(private_recovery_body),
        "source_private_inventory_name": private_output_path.name,
        "source_private_inventory_sha256": sha256(private_body_out),
        "target": {
            "guild_label": expected_guild_label,
            "route_template": ROUTE,
            "callee_sha256": callee_hash,
            "callee_published": False,
            "asset_url_published": False,
            "source_guild_id_published": False,
            "raw_definition_published": False,
            "alias_target_published": False,
            "source_scalar_values_published": False,
        },
        "request_contract": {
            "network_requests_performed": False,
            "raw_archive_only": True,
            "max_symbol_occurrences": max_symbol_occurrences,
            "max_definition_candidates": max_definition_candidates,
            "max_definition_span_chars": max_definition_span_chars,
            "private_context_chars_per_side": private_context_chars,
        },
        "definition_candidates": public_candidates,
        "cross_definition_evidence": {
            **evidence,
            "helper_definition_candidate_observed": bool(public_candidates),
            "contains_raw_callee": False,
            "contains_raw_definition": False,
            "contains_alias_target": False,
            "contains_source_scalar_values": False,
        },
        "integrity_checks": checks,
        "summary": {
            "all_integrity_checks_passed": True,
            "integrity_check_count": len(checks),
            **evidence,
            "helper_definition_candidate_observed": bool(public_candidates),
            "ready_for_guild_progression_helper_definition_review": True,
            "guild_progression_helper_identity_resolved": False,
            "guild_progression_request_payload_mapping_resolved": False,
            "guild_progression_request_shape_verified": False,
            **_FALSE_GATES,
            "contains_raw_callee": False,
            "contains_raw_definition": False,
            "contains_alias_target": False,
            "contains_source_scalar_values": False,
            "network_requests_performed": False,
        },
        "decision_boundary": {
            "status": "guild_progression_helper_definition_inventory_observed",
            "guild_progression_route_candidate_observed": True,
            "guild_progression_usage_context_reviewed": True,
            "guild_progression_helper_callsite_reviewed": True,
            "guild_progression_method_candidate_unambiguous": True,
            "guild_progression_http_method_candidate": "POST",
            "guild_progression_helper_definition_inventory_observed": True,
            "guild_progression_helper_identity_resolved": False,
            "guild_progression_request_payload_mapping_resolved": False,
            "guild_progression_request_shape_verified": False,
            "ready_for_guild_progression_helper_definition_review": True,
            **_FALSE_GATES,
            "automatic_full_guild_crawl_allowed": False,
            "ready_for_multi_report_character_graph": False,
            "ready_for_performance_model": False,
            "ready_for_bis25_scoring": False,
        },
    }
    if property_names(receipt) & _FORBIDDEN_PUBLIC_FIELDS:
        raise ValueError("public helper-definition receipt contains forbidden fields")
    write_json(receipt_output_path, receipt)
    return receipt


__all__ = ["inventory_guild_progression_helper_definition"]
