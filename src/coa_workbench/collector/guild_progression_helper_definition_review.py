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
    integer_value,
    load_json,
    object_value,
    property_names,
    require_checks,
    sha256,
    sha256_value,
    write_json,
)

REVIEW_KIND = "guild_progression_helper_definition_review"
REVIEW_VERSION = "guild-progression-helper-definition-review-v1"
INVENTORY_KIND = "guild_progression_helper_definition_inventory"
PRIVATE_INVENTORY_KIND = f"{INVENTORY_KIND}_private"
INVENTORY_VERSION = "guild-progression-helper-definition-inventory-v1"
CALLSITE_REVIEW_KIND = "guild_progression_helper_callsite_review"
CALLSITE_REVIEW_VERSION = "guild-progression-helper-callsite-review-v1"
ROUTE = "/api/guilds/progression"

_DIRECT_TRANSPORT_MARKERS = {"fetch", "XMLHttpRequest"}
_REQUEST_SHAPE_MARKERS = {
    "body",
    "data",
    "headers",
    "method",
    "params",
    "query",
    "searchParams",
    "url",
    "JSON.stringify",
    "Content-Type",
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
_FORBIDDEN_PUBLIC_FIELDS = {
    "alias_target",
    "asset_url",
    "callee",
    "context",
    "end",
    "private_excerpt",
    "private_query",
    "raw_callee",
    "raw_definition",
    "raw_payload",
    "raw_records",
    "request_url",
    "source_guild_id",
    "span",
    "start",
    "symbol",
}
_IDENTIFIER = r"[A-Za-z_$][A-Za-z0-9_$]*"
_CALLEE_PATTERN = re.compile(rf"{_IDENTIFIER}(?:\.{_IDENTIFIER})*")


def _markers(value: str) -> list[str]:
    observed: list[str] = []
    for marker in sorted(_REQUEST_SHAPE_MARKERS | _DIRECT_TRANSPORT_MARKERS):
        if marker in {"JSON.stringify", "Content-Type", "XMLHttpRequest"}:
            present = marker in value
        else:
            present = bool(re.search(rf"\b{re.escape(marker)}\b", value))
        if present:
            observed.append(marker)
    return observed


def _validate_callsite_review(review: Mapping[str, Any]) -> None:
    expect(
        review,
        {
            "schema_version": 1,
            "review_kind": CALLSITE_REVIEW_KIND,
            "review_version": CALLSITE_REVIEW_VERSION,
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
            "actual_helper_invocation_candidate_observed": True,
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


def _validate_public_inventory(
    inventory: Mapping[str, Any],
    inventory_body: bytes,
    callsite_review_path: Path,
    callsite_review_body: bytes,
    private_inventory_path: Path,
    private_inventory_body: bytes,
) -> tuple[dict[str, Any], dict[str, Any]]:
    expect(
        inventory,
        {
            "schema_version": 1,
            "inventory_kind": INVENTORY_KIND,
            "inventory_version": INVENTORY_VERSION,
            "source_callsite_review_name": callsite_review_path.name,
            "source_private_inventory_name": private_inventory_path.name,
        },
        "public helper-definition inventory",
    )
    require_checks(
        inventory.get("integrity_checks"),
        36,
        "public helper-definition inventory integrity checks",
    )
    if property_names(inventory) & _FORBIDDEN_PUBLIC_FIELDS:
        raise ValueError("public helper-definition inventory contains forbidden fields")

    declared_callsite = sha256_value(
        inventory.get("source_callsite_review_sha256"),
        "public inventory call-site review SHA-256",
    )
    if declared_callsite not in document_hashes(callsite_review_body):
        raise ValueError("public inventory call-site review SHA-256 mismatch")
    declared_private = sha256_value(
        inventory.get("source_private_inventory_sha256"),
        "public inventory private inventory SHA-256",
    )
    if declared_private != sha256(private_inventory_body):
        raise ValueError("private helper-definition inventory SHA-256 mismatch")

    target = object_value(inventory.get("target"), "public inventory target")
    expect(
        target,
        {
            "guild_label": "Argentum",
            "route_template": ROUTE,
            "callee_published": False,
            "asset_url_published": False,
            "source_guild_id_published": False,
            "raw_definition_published": False,
            "alias_target_published": False,
            "source_scalar_values_published": False,
        },
        "public inventory target",
    )
    sha256_value(target.get("callee_sha256"), "public inventory callee SHA-256")

    request = object_value(inventory.get("request_contract"), "public inventory request contract")
    expect(
        request,
        {
            "network_requests_performed": False,
            "raw_archive_only": True,
            "max_symbol_occurrences": 500,
            "max_definition_candidates": 50,
            "max_definition_span_chars": 131072,
            "private_context_chars_per_side": 4096,
        },
        "public inventory request contract",
    )

    expected_evidence = {
        "full_chain_occurrence_count_observed": 2,
        "full_chain_occurrence_scan_truncated": False,
        "terminal_symbol_occurrence_count_observed": 31,
        "terminal_symbol_occurrence_scan_truncated": False,
        "definition_candidate_count": 1,
        "definition_candidate_scan_truncated": False,
        "definition_kinds": ["method_definition"],
        "binding_scopes": ["terminal_symbol"],
        "alias_candidate_count": 0,
        "marker_classes": [],
        "helper_definition_candidate_observed": True,
        "contains_raw_callee": False,
        "contains_raw_definition": False,
        "contains_alias_target": False,
        "contains_source_scalar_values": False,
    }
    cross = object_value(inventory.get("cross_definition_evidence"), "cross-definition evidence")
    expect(cross, expected_evidence, "cross-definition evidence")

    summary = object_value(inventory.get("summary"), "public inventory summary")
    expect(
        summary,
        {
            "all_integrity_checks_passed": True,
            "integrity_check_count": 36,
            **expected_evidence,
            "ready_for_guild_progression_helper_definition_review": True,
            "guild_progression_helper_identity_resolved": False,
            "guild_progression_request_payload_mapping_resolved": False,
            "guild_progression_request_shape_verified": False,
            **_FALSE_GATES,
            "network_requests_performed": False,
        },
        "public inventory summary",
    )
    candidates = array_value(inventory.get("definition_candidates"), "public definition candidates")
    if len(candidates) != 1:
        raise ValueError("expected exactly one public helper-definition candidate")
    candidate = object_value(candidates[0], "public definition candidate")
    expect(
        candidate,
        {
            "candidate_index": 1,
            "definition_kind": "method_definition",
            "binding_scope": "terminal_symbol",
            "definition_character_count": 40,
            "parameter_count": 1,
            "async_candidate": False,
            "marker_classes": [],
            "alias_target_sha256": None,
            "contains_raw_callee": False,
            "contains_raw_definition": False,
            "contains_alias_target": False,
            "contains_source_scalar_values": False,
        },
        "public definition candidate",
    )
    sha256_value(candidate.get("definition_span_sha256"), "public definition span SHA-256")
    sha256_value(candidate.get("definition_prefix_sha256"), "public definition prefix SHA-256")
    return candidate, target


def _validate_private_inventory(
    private_inventory: Mapping[str, Any],
    public_candidate: Mapping[str, Any],
    target: Mapping[str, Any],
) -> tuple[dict[str, Any], str, str]:
    expect(
        private_inventory,
        {
            "schema_version": 1,
            "inventory_kind": PRIVATE_INVENTORY_KIND,
            "inventory_version": INVENTORY_VERSION,
            "route": ROUTE,
        },
        "private helper-definition inventory",
    )
    callee = private_inventory.get("callee")
    if not isinstance(callee, str) or not _CALLEE_PATTERN.fullmatch(callee):
        raise ValueError("private helper callee is missing or malformed")
    callee_hash = sha256_value(private_inventory.get("callee_sha256"), "private callee SHA-256")
    if sha256(callee.encode()) != callee_hash:
        raise ValueError("private callee SHA-256 mismatch")
    if callee_hash != target.get("callee_sha256"):
        raise ValueError("public/private callee SHA-256 mismatch")

    private_summary = object_value(private_inventory.get("summary"), "private inventory summary")
    expect(
        private_summary,
        {
            "full_chain_occurrence_count_observed": 2,
            "full_chain_occurrence_scan_truncated": False,
            "terminal_symbol_occurrence_count_observed": 31,
            "terminal_symbol_occurrence_scan_truncated": False,
            "definition_candidate_count": 1,
            "definition_candidate_scan_truncated": False,
            "definition_kinds": ["method_definition"],
            "binding_scopes": ["terminal_symbol"],
            "alias_candidate_count": 0,
            "marker_classes": [],
            "contains_source_scalar_values": True,
            "network_requests_performed": False,
        },
        "private inventory summary",
    )
    candidates = array_value(
        private_inventory.get("definition_candidates"),
        "private definition candidates",
    )
    if len(candidates) != 1:
        raise ValueError("expected exactly one private helper-definition candidate")
    private_candidate = object_value(candidates[0], "private definition candidate")

    aligned_fields = (
        ("candidate_index", "candidate index"),
        ("kind", "definition kind", "definition_kind"),
        ("binding_scope", "binding scope"),
        ("span_sha256", "definition span SHA-256", "definition_span_sha256"),
        ("character_count", "definition character count", "definition_character_count"),
        ("prefix_sha256", "definition prefix SHA-256", "definition_prefix_sha256"),
        ("parameter_count", "parameter count"),
        ("async_candidate", "async flag"),
        ("marker_classes", "marker classes"),
        ("alias_target_sha256", "alias target SHA-256"),
    )
    for field_group in aligned_fields:
        private_field = field_group[0]
        label = field_group[1]
        public_field = field_group[2] if len(field_group) == 3 else private_field
        if private_candidate.get(private_field) != public_candidate.get(public_field):
            raise ValueError(f"public/private candidate mismatch: {label}")

    span = private_candidate.get("span")
    if not isinstance(span, str):
        raise ValueError("private definition span is missing")
    if sha256(span.encode()) != public_candidate.get("definition_span_sha256"):
        raise ValueError("private definition span SHA-256 mismatch")
    if len(span) != integer_value(
        public_candidate.get("definition_character_count"),
        "public definition character count",
    ):
        raise ValueError("private definition character count mismatch")

    excerpt = private_candidate.get("private_excerpt")
    if not isinstance(excerpt, str) or span not in excerpt:
        raise ValueError("private excerpt does not preserve the definition span")
    if private_candidate.get("alias_target") is not None:
        raise ValueError("unexpected private alias target for the reviewed candidate")

    observed_markers = _markers(span)
    if observed_markers != public_candidate.get("marker_classes"):
        raise ValueError("private definition marker classes mismatch")
    terminal = callee.rsplit(".", 1)[-1]
    method_pattern = re.compile(rf"\b{re.escape(terminal)}\s*\([^;{{}}]*\)\s*\{{")
    if not method_pattern.search(span):
        raise ValueError("private candidate does not contain the expected method signature")
    return private_candidate, callee, span


def _checks() -> dict[str, bool]:
    names = (
        "callsite_review_contract_verified callsite_review_integrity_checks_verified "
        "callsite_review_privacy_boundary_verified public_inventory_contract_verified "
        "public_inventory_integrity_checks_verified public_inventory_privacy_boundary_verified "
        "public_inventory_callsite_name_verified public_inventory_callsite_sha256_verified "
        "public_inventory_private_name_verified public_inventory_private_sha256_verified "
        "private_inventory_contract_verified private_inventory_route_verified "
        "private_inventory_callee_hash_verified public_private_candidate_count_verified "
        "public_private_candidate_index_verified public_private_definition_kind_verified "
        "public_private_binding_scope_verified public_private_span_sha256_verified "
        "public_private_prefix_sha256_verified public_private_character_count_verified "
        "public_private_parameter_count_verified public_private_async_flag_verified "
        "public_private_marker_classes_verified public_private_alias_hash_verified "
        "raw_span_sha256_verified raw_span_character_count_verified "
        "method_definition_signature_verified private_excerpt_contains_definition_verified "
        "candidate_scan_not_truncated full_chain_scan_not_truncated "
        "terminal_symbol_scan_not_truncated alias_chain_not_observed "
        "transport_semantics_not_observed helper_identity_not_inferred "
        "request_payload_mapping_not_inferred request_shape_not_inferred "
        "network_requests_performed_false route_probe_remains_disabled "
        "route_semantics_not_overclaimed collection_semantics_not_overclaimed "
        "full_crawl_and_scoring_remain_disabled "
        "helper_reference_inventory_selected_as_next_gate"
    ).split()
    checks = {name: True for name in names}
    if len(checks) != 42:
        raise RuntimeError("helper-definition review integrity-check contract drift")
    return checks


def review_guild_progression_helper_definition(
    *,
    inventory_path: Path,
    private_inventory_path: Path,
    callsite_review_path: Path,
    receipt_output_path: Path,
) -> dict[str, Any]:
    """Review the exact private helper-definition candidate without enabling a probe."""
    inventory, inventory_body = load_json(inventory_path, "public helper-definition inventory")
    private_inventory, private_inventory_body = load_json(
        private_inventory_path,
        "private helper-definition inventory",
    )
    callsite_review, callsite_review_body = load_json(callsite_review_path, "call-site review")
    _validate_callsite_review(callsite_review)
    public_candidate, target = _validate_public_inventory(
        inventory,
        inventory_body,
        callsite_review_path,
        callsite_review_body,
        private_inventory_path,
        private_inventory_body,
    )
    private_candidate, callee, span = _validate_private_inventory(
        private_inventory,
        public_candidate,
        target,
    )

    marker_classes = list(public_candidate["marker_classes"])
    direct_transport_markers = sorted(set(marker_classes) & _DIRECT_TRANSPORT_MARKERS)
    request_shape_markers = sorted(set(marker_classes) & _REQUEST_SHAPE_MARKERS)
    terminal = callee.rsplit(".", 1)[-1]
    excerpt = str(private_candidate["private_excerpt"])
    blockers = [
        "terminal_symbol_only_definition",
        "transport_semantics_not_observed",
        "receiver_or_alias_ownership_unresolved",
        "request_payload_mapping_unresolved",
    ]
    candidate_review = {
        "candidate_index": public_candidate["candidate_index"],
        "definition_kind": public_candidate["definition_kind"],
        "binding_scope": public_candidate["binding_scope"],
        "definition_span_sha256": public_candidate["definition_span_sha256"],
        "definition_prefix_sha256": public_candidate["definition_prefix_sha256"],
        "definition_character_count": public_candidate["definition_character_count"],
        "parameter_count": public_candidate["parameter_count"],
        "async_candidate": public_candidate["async_candidate"],
        "marker_classes": marker_classes,
        "alias_target_sha256": public_candidate["alias_target_sha256"],
        "public_private_alignment_verified": True,
        "terminal_method_signature_observed": True,
        "definition_preserved_in_private_excerpt": True,
        "callee_observed_in_private_excerpt": callee in excerpt,
        "terminal_symbol_observed_in_private_excerpt": terminal in excerpt,
        "route_observed_in_private_excerpt": ROUTE in excerpt.replace("\\/", "/"),
        "direct_transport_markers": direct_transport_markers,
        "request_shape_markers": request_shape_markers,
        "direct_transport_semantics_observed": False,
        "request_shape_semantics_observed": False,
        "alias_chain_observed": False,
        "full_chain_binding_observed": False,
        "helper_identity_evidence_sufficient": False,
        "request_payload_mapping_evidence_sufficient": False,
        "review_disposition": "unresolved_terminal_method_without_transport_semantics",
        "contains_raw_callee": False,
        "contains_raw_definition": False,
        "contains_private_excerpt": False,
        "contains_alias_target": False,
        "contains_source_scalar_values": False,
    }
    checks = _checks()
    review = {
        "schema_version": 1,
        "review_kind": REVIEW_KIND,
        "review_version": REVIEW_VERSION,
        "generated_at": generated_at(),
        "source_inventory_name": inventory_path.name,
        "source_inventory_sha256": sha256(canonical_lf(inventory_body)),
        "source_private_inventory_name": private_inventory_path.name,
        "source_private_inventory_sha256": sha256(private_inventory_body),
        "source_callsite_review_name": callsite_review_path.name,
        "source_callsite_review_sha256": sha256(canonical_lf(callsite_review_body)),
        "source_binding_review": {
            "public_inventory_document_identity_preserved": True,
            "private_inventory_document_identity_preserved": True,
            "callsite_review_sha256_verified_across_lf_crlf": True,
            "public_private_candidate_alignment_verified": True,
        },
        "helper_definition_review": {
            "route_template": ROUTE,
            "candidate_count": 1,
            "definition_kinds": ["method_definition"],
            "binding_scopes": ["terminal_symbol"],
            "alias_candidate_count": 0,
            "marker_classes": [],
            "full_chain_occurrence_count_observed": 2,
            "terminal_symbol_occurrence_count_observed": 31,
            "all_inventory_scans_complete": True,
            "terminal_symbol_only_candidate_observed": True,
            "direct_transport_semantics_observed": False,
            "request_shape_semantics_observed": False,
            "helper_definition_candidate_reviewed": True,
            "helper_identity_resolved": False,
            "request_payload_mapping_resolved": False,
            "request_shape_sufficient_for_bounded_probe": False,
            "ready_for_guild_progression_helper_reference_inventory": True,
            "route_semantics_verified": False,
            "contains_raw_callee": False,
            "contains_raw_definition": False,
            "contains_private_excerpt": False,
            "contains_alias_target": False,
            "contains_source_scalar_values": False,
            "blockers": blockers,
        },
        "candidate_reviews": [candidate_review],
        "integrity_checks": checks,
        "summary": {
            "all_integrity_checks_passed": True,
            "integrity_check_count": len(checks),
            "guild_progression_helper_definition_reviewed": True,
            "definition_candidate_count": 1,
            "definition_candidate_disposition": (
                "unresolved_terminal_method_without_transport_semantics"
            ),
            "helper_identity_resolved": False,
            "request_payload_mapping_resolved": False,
            "request_shape_sufficient_for_bounded_probe": False,
            "ready_for_guild_progression_helper_reference_inventory": True,
            **_FALSE_GATES,
            "contains_raw_callee": False,
            "contains_raw_definition": False,
            "contains_private_excerpt": False,
            "contains_alias_target": False,
            "contains_source_scalar_values": False,
            "network_requests_performed": False,
        },
        "decision_boundary": {
            "status": "guild_progression_helper_definition_reviewed_probe_blocked",
            "guild_progression_route_candidate_observed": True,
            "guild_progression_usage_context_reviewed": True,
            "guild_progression_helper_callsite_reviewed": True,
            "guild_progression_method_candidate_unambiguous": True,
            "guild_progression_http_method_candidate": "POST",
            "guild_progression_helper_definition_inventory_observed": True,
            "guild_progression_helper_definition_reviewed": True,
            "guild_progression_helper_identity_resolved": False,
            "guild_progression_request_payload_mapping_resolved": False,
            "guild_progression_request_shape_verified": False,
            "ready_for_guild_progression_helper_reference_inventory": True,
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
    if property_names(review) & _FORBIDDEN_PUBLIC_FIELDS:
        raise ValueError("public helper-definition review contains forbidden fields")
    write_json(receipt_output_path, review)
    return review


__all__ = ["review_guild_progression_helper_definition"]
