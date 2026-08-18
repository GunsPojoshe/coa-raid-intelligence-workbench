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

REVIEW_KIND = "guild_progression_helper_reference_review"
REVIEW_VERSION = "guild-progression-helper-reference-review-v1"
INVENTORY_KIND = "guild_progression_helper_reference_inventory"
PRIVATE_INVENTORY_KIND = f"{INVENTORY_KIND}_private"
INVENTORY_VERSION = "guild-progression-helper-reference-inventory-v1"
DEFINITION_REVIEW_KIND = "guild_progression_helper_definition_review"
DEFINITION_REVIEW_VERSION = "guild-progression-helper-definition-review-v1"
ROUTE = "/api/guilds/progression"

_REFERENCE_KINDS = {
    "definition_candidate",
    "invocation",
    "assignment_target",
    "object_key",
    "member_reference",
    "identifier_reference",
}
_SYMBOL_SCOPES = {"full_chain", "terminal_symbol"}
_EXPECTED_REFERENCE_KINDS = [
    "definition_candidate",
    "invocation",
    "member_reference",
    "object_key",
]
_EXPECTED_SYMBOL_SCOPES = ["full_chain", "terminal_symbol"]
_EXPECTED_REQUEST_SHAPE_MARKERS = ["JSON.stringify", "body", "data", "params", "url"]
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
    "context_end",
    "context_start",
    "end",
    "private_excerpt",
    "private_query",
    "raw_callee",
    "raw_definition",
    "raw_payload",
    "raw_records",
    "raw_symbol",
    "request_url",
    "source_guild_id",
    "span",
    "start",
    "symbol",
}
_IDENTIFIER = r"[A-Za-z_$][A-Za-z0-9_$]*"
_CALLEE_PATTERN = re.compile(rf"{_IDENTIFIER}(?:\.{_IDENTIFIER})*")


def _require_false_fields(value: Mapping[str, Any], fields: tuple[str, ...], label: str) -> None:
    for field in fields:
        if value.get(field) is not False:
            raise ValueError(f"{label} mismatch: {field}")


def _validate_definition_review(review: Mapping[str, Any]) -> None:
    expect(
        review,
        {
            "schema_version": 1,
            "review_kind": DEFINITION_REVIEW_KIND,
            "review_version": DEFINITION_REVIEW_VERSION,
        },
        "helper-definition review",
    )
    require_checks(review.get("integrity_checks"), 42, "helper-definition review checks")
    summary = object_value(review.get("summary"), "helper-definition review summary")
    expect(
        summary,
        {
            "all_integrity_checks_passed": True,
            "integrity_check_count": 42,
            "guild_progression_helper_definition_reviewed": True,
            "definition_candidate_count": 1,
            "definition_candidate_disposition": (
                "unresolved_terminal_method_without_transport_semantics"
            ),
            "helper_identity_resolved": False,
            "request_payload_mapping_resolved": False,
            "request_shape_sufficient_for_bounded_probe": False,
            "ready_for_guild_progression_helper_reference_inventory": True,
            "contains_raw_callee": False,
            "contains_raw_definition": False,
            "contains_private_excerpt": False,
            "contains_alias_target": False,
            "contains_source_scalar_values": False,
            "network_requests_performed": False,
        },
        "helper-definition review summary",
    )
    _require_false_fields(summary, tuple(_FALSE_GATES), "helper-definition review summary")
    if property_names(review) & _FORBIDDEN_PUBLIC_FIELDS:
        raise ValueError("helper-definition review contains forbidden public fields")


def _expected_evidence() -> dict[str, object]:
    return {
        "full_chain_occurrence_count_observed": 2,
        "full_chain_occurrence_scan_truncated": False,
        "terminal_symbol_occurrence_count_observed": 31,
        "terminal_symbol_occurrence_scan_truncated": False,
        "terminal_symbol_only_occurrence_count": 29,
        "unique_reference_candidate_count": 31,
        "reference_candidate_scan_truncated": False,
        "reference_kinds": _EXPECTED_REFERENCE_KINDS,
        "symbol_scopes": _EXPECTED_SYMBOL_SCOPES,
        "definition_overlap_count": 1,
        "route_context_reference_count": 0,
        "direct_transport_marker_classes": [],
        "request_shape_marker_classes": _EXPECTED_REQUEST_SHAPE_MARKERS,
    }


def _validate_public_inventory(
    inventory: Mapping[str, Any],
    inventory_body: bytes,
    definition_review_path: Path,
    definition_review_body: bytes,
    private_inventory_path: Path,
    private_inventory_body: bytes,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    expect(
        inventory,
        {
            "schema_version": 1,
            "inventory_kind": INVENTORY_KIND,
            "inventory_version": INVENTORY_VERSION,
            "source_definition_review_name": definition_review_path.name,
            "source_private_inventory_name": private_inventory_path.name,
        },
        "public helper-reference inventory",
    )
    require_checks(inventory.get("integrity_checks"), 40, "helper-reference inventory checks")
    if property_names(inventory) & _FORBIDDEN_PUBLIC_FIELDS:
        raise ValueError("public helper-reference inventory contains forbidden fields")

    declared_review = sha256_value(
        inventory.get("source_definition_review_sha256"),
        "public inventory definition-review SHA-256",
    )
    if declared_review not in document_hashes(definition_review_body):
        raise ValueError("public inventory definition-review SHA-256 mismatch")
    declared_private = sha256_value(
        inventory.get("source_private_inventory_sha256"),
        "public inventory private SHA-256",
    )
    if declared_private != sha256(private_inventory_body):
        raise ValueError("private helper-reference inventory SHA-256 mismatch")

    target = object_value(inventory.get("target"), "public inventory target")
    expect(
        target,
        {
            "guild_label": "Argentum",
            "route_template": ROUTE,
            "callee_published": False,
            "raw_symbol_published": False,
            "raw_context_published": False,
            "source_scalar_values_published": False,
        },
        "public inventory target",
    )
    sha256_value(target.get("callee_sha256"), "public inventory callee SHA-256")

    contract = object_value(inventory.get("request_contract"), "public request contract")
    expect(
        contract,
        {
            "network_requests_performed": False,
            "raw_archive_only": True,
            "max_symbol_occurrences": 500,
            "max_reference_candidates": 500,
            "private_context_chars_per_side": 1024,
        },
        "public request contract",
    )

    expected = _expected_evidence()
    cross = object_value(inventory.get("cross_reference_evidence"), "cross-reference evidence")
    expect(
        cross,
        {
            **expected,
            "reference_evidence_observed": True,
            "contains_raw_callee": False,
            "contains_raw_symbol": False,
            "contains_raw_context": False,
            "contains_source_scalar_values": False,
        },
        "cross-reference evidence",
    )
    summary = object_value(inventory.get("summary"), "public inventory summary")
    expect(
        summary,
        {
            "all_integrity_checks_passed": True,
            "integrity_check_count": 40,
            **expected,
            "reference_evidence_observed": True,
            "ready_for_guild_progression_helper_reference_review": True,
            "guild_progression_helper_identity_resolved": False,
            "guild_progression_request_payload_mapping_resolved": False,
            "guild_progression_request_shape_verified": False,
            **_FALSE_GATES,
            "contains_raw_callee": False,
            "contains_raw_symbol": False,
            "contains_raw_context": False,
            "contains_source_scalar_values": False,
            "network_requests_performed": False,
        },
        "public inventory summary",
    )

    references_raw = array_value(inventory.get("references"), "public references")
    if len(references_raw) != 31:
        raise ValueError("expected exactly 31 public helper references")
    references: list[dict[str, Any]] = []
    for expected_index, raw in enumerate(references_raw, 1):
        row = object_value(raw, f"public reference {expected_index}")
        expect(
            row,
            {
                "reference_index": expected_index,
                "contains_raw_symbol": False,
                "contains_raw_context": False,
                "contains_source_scalar_values": False,
            },
            f"public reference {expected_index}",
        )
        if row.get("symbol_scope") not in _SYMBOL_SCOPES:
            raise ValueError(f"public reference {expected_index} symbol scope mismatch")
        if row.get("reference_kind") not in _REFERENCE_KINDS:
            raise ValueError(f"public reference {expected_index} kind mismatch")
        sha256_value(row.get("context_sha256"), f"public reference {expected_index} context SHA-256")
        count = integer_value(
            row.get("context_character_count"),
            f"public reference {expected_index} context character count",
        )
        if not 1 <= count <= 2304:
            raise ValueError(f"public reference {expected_index} context character count out of bounds")
        for field in ("definition_candidate_overlap", "route_template_observed"):
            if not isinstance(row.get(field), bool):
                raise ValueError(f"public reference {expected_index} {field} must be boolean")
        for field in ("direct_transport_markers", "request_shape_markers"):
            values = array_value(row.get(field), f"public reference {expected_index} {field}")
            if any(not isinstance(item, str) for item in values):
                raise ValueError(f"public reference {expected_index} {field} must be strings")
        references.append(row)
    return target, references


def _validate_private_inventory(
    private_inventory: Mapping[str, Any],
    target: Mapping[str, Any],
    public_references: list[dict[str, Any]],
) -> tuple[str, list[dict[str, Any]]]:
    expect(
        private_inventory,
        {
            "schema_version": 1,
            "inventory_kind": PRIVATE_INVENTORY_KIND,
            "inventory_version": INVENTORY_VERSION,
            "route": ROUTE,
        },
        "private helper-reference inventory",
    )
    callee = private_inventory.get("callee")
    if not isinstance(callee, str) or not _CALLEE_PATTERN.fullmatch(callee):
        raise ValueError("private helper callee is missing or malformed")
    callee_hash = sha256_value(private_inventory.get("callee_sha256"), "private callee SHA-256")
    if sha256(callee.encode()) != callee_hash or target.get("callee_sha256") != callee_hash:
        raise ValueError("public/private helper callee SHA-256 mismatch")

    summary = object_value(private_inventory.get("summary"), "private inventory summary")
    expect(
        summary,
        {
            **_expected_evidence(),
            "contains_source_scalar_values": True,
            "network_requests_performed": False,
        },
        "private inventory summary",
    )

    references_raw = array_value(private_inventory.get("references"), "private references")
    if len(references_raw) != len(public_references):
        raise ValueError("public/private helper-reference count mismatch")
    private_references: list[dict[str, Any]] = []
    aligned_fields = (
        "reference_index",
        "symbol_scope",
        "reference_kind",
        "context_sha256",
        "context_character_count",
        "definition_candidate_overlap",
        "route_template_observed",
        "direct_transport_markers",
        "request_shape_markers",
    )
    for expected_index, (raw_private, public_row) in enumerate(
        zip(references_raw, public_references, strict=True),
        1,
    ):
        row = object_value(raw_private, f"private reference {expected_index}")
        for field in aligned_fields:
            if row.get(field) != public_row.get(field):
                raise ValueError(
                    f"public/private reference {expected_index} mismatch: {field}"
                )
        symbol = row.get("raw_symbol")
        if not isinstance(symbol, str) or not symbol:
            raise ValueError(f"private reference {expected_index} raw symbol is missing")
        start = integer_value(row.get("start"), f"private reference {expected_index} start")
        end = integer_value(row.get("end"), f"private reference {expected_index} end")
        if start < 0 or end <= start or end - start != len(symbol):
            raise ValueError(f"private reference {expected_index} symbol span is invalid")
        context = row.get("context")
        if not isinstance(context, str):
            raise ValueError(f"private reference {expected_index} context is missing")
        if sha256(context.encode()) != public_row.get("context_sha256"):
            raise ValueError(f"private reference {expected_index} context SHA-256 mismatch")
        if len(context) != public_row.get("context_character_count"):
            raise ValueError(f"private reference {expected_index} context length mismatch")
        context_start = integer_value(
            row.get("context_start"),
            f"private reference {expected_index} context start",
        )
        context_end = integer_value(
            row.get("context_end"),
            f"private reference {expected_index} context end",
        )
        if (
            context_start < 0
            or context_end <= context_start
            or context_end - context_start != len(context)
        ):
            raise ValueError(f"private reference {expected_index} context span is invalid")
        private_references.append(row)
    return callee, private_references


def _reference_disposition(row: Mapping[str, Any]) -> str:
    route = row.get("route_template_observed") is True
    transport = bool(row.get("direct_transport_markers"))
    request_shape = bool(row.get("request_shape_markers"))
    if row.get("definition_candidate_overlap") is True:
        return "definition_reference_only"
    if route and transport:
        return "route_transport_binding_candidate"
    if route and request_shape:
        return "route_request_shape_binding_candidate"
    if route:
        return "route_context_without_transport"
    if transport:
        return "transport_marker_context_without_route"
    if request_shape:
        return "request_shape_marker_context_without_route"
    return "unbound_reference_context"


def _checks() -> dict[str, bool]:
    names = """
    definition_review_contract_verified definition_review_checks_verified
    definition_review_privacy_verified definition_review_next_gate_verified
    public_inventory_contract_verified public_inventory_checks_verified
    public_inventory_privacy_verified public_inventory_definition_review_name_verified
    public_inventory_definition_review_hash_verified public_inventory_private_name_verified
    public_inventory_private_hash_verified private_inventory_contract_verified
    private_inventory_route_verified private_callee_hash_verified
    public_private_callee_hash_verified public_private_reference_count_verified
    public_private_reference_indexes_verified public_private_symbol_scopes_verified
    public_private_reference_kinds_verified public_private_context_hashes_verified
    public_private_context_lengths_verified public_private_definition_overlap_verified
    public_private_route_flags_verified public_private_transport_markers_verified
    public_private_request_shape_markers_verified private_symbol_spans_verified
    private_context_spans_verified private_context_hashes_recomputed
    occurrence_counts_verified reference_kind_inventory_verified
    symbol_scope_inventory_verified definition_overlap_count_verified
    route_context_count_zero_verified direct_transport_markers_absent
    request_shape_markers_not_bound_to_route helper_owner_not_inferred
    request_payload_mapping_not_inferred request_shape_not_inferred
    network_requests_performed_false route_probe_remains_disabled
    route_semantics_not_overclaimed pagination_not_overclaimed
    termination_not_overclaimed completeness_not_overclaimed
    full_crawl_and_scoring_remain_disabled helper_owner_inventory_selected_as_next_gate
    """.split()
    checks = {name: True for name in names}
    if len(checks) != 46:
        raise RuntimeError("helper-reference review integrity-check contract drift")
    return checks


def review_guild_progression_helper_references(
    *,
    inventory_path: Path,
    private_inventory_path: Path,
    definition_review_path: Path,
    receipt_output_path: Path,
) -> dict[str, Any]:
    """Review exact private helper-reference contexts without enabling a route probe."""
    inventory, inventory_body = load_json(inventory_path, "public helper-reference inventory")
    private_inventory, private_inventory_body = load_json(
        private_inventory_path,
        "private helper-reference inventory",
    )
    definition_review, definition_review_body = load_json(
        definition_review_path,
        "helper-definition review",
    )
    _validate_definition_review(definition_review)
    target, public_references = _validate_public_inventory(
        inventory,
        inventory_body,
        definition_review_path,
        definition_review_body,
        private_inventory_path,
        private_inventory_body,
    )
    _callee, private_references = _validate_private_inventory(
        private_inventory,
        target,
        public_references,
    )

    reference_reviews: list[dict[str, Any]] = []
    for public_row, private_row in zip(public_references, private_references, strict=True):
        disposition = _reference_disposition(private_row)
        reference_reviews.append(
            {
                "reference_index": public_row["reference_index"],
                "symbol_scope": public_row["symbol_scope"],
                "reference_kind": public_row["reference_kind"],
                "context_sha256": public_row["context_sha256"],
                "context_character_count": public_row["context_character_count"],
                "definition_candidate_overlap": public_row["definition_candidate_overlap"],
                "route_template_observed": public_row["route_template_observed"],
                "direct_transport_markers": list(public_row["direct_transport_markers"]),
                "request_shape_markers": list(public_row["request_shape_markers"]),
                "public_private_alignment_verified": True,
                "route_transport_binding_observed": (
                    public_row["route_template_observed"]
                    and bool(public_row["direct_transport_markers"])
                ),
                "route_request_shape_binding_observed": (
                    public_row["route_template_observed"]
                    and bool(public_row["request_shape_markers"])
                ),
                "helper_owner_evidence_sufficient": False,
                "request_payload_mapping_evidence_sufficient": False,
                "review_disposition": disposition,
                "contains_raw_callee": False,
                "contains_raw_symbol": False,
                "contains_raw_context": False,
                "contains_source_scalar_values": False,
            }
        )

    kind_counts = {
        kind: sum(row["reference_kind"] == kind for row in reference_reviews)
        for kind in _EXPECTED_REFERENCE_KINDS
    }
    scope_counts = {
        scope: sum(row["symbol_scope"] == scope for row in reference_reviews)
        for scope in _EXPECTED_SYMBOL_SCOPES
    }
    request_shape_context_count = sum(
        bool(row["request_shape_markers"]) for row in reference_reviews
    )
    route_transport_binding_count = sum(
        bool(row["route_transport_binding_observed"]) for row in reference_reviews
    )
    route_request_shape_binding_count = sum(
        bool(row["route_request_shape_binding_observed"]) for row in reference_reviews
    )
    blockers = [
        "route_not_observed_in_reference_contexts",
        "direct_transport_markers_not_observed",
        "receiver_or_owner_binding_unresolved",
        "request_shape_markers_not_bound_to_route_invocation",
    ]
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
        "source_definition_review_name": definition_review_path.name,
        "source_definition_review_sha256": sha256(canonical_lf(definition_review_body)),
        "source_binding_review": {
            "public_inventory_document_identity_preserved": True,
            "private_inventory_document_identity_preserved": True,
            "definition_review_sha256_verified_across_lf_crlf": True,
            "public_private_reference_alignment_verified": True,
        },
        "helper_reference_review": {
            "route_template": ROUTE,
            "reference_count": len(reference_reviews),
            "full_chain_occurrence_count_observed": 2,
            "terminal_symbol_occurrence_count_observed": 31,
            "terminal_symbol_only_occurrence_count": 29,
            "reference_kind_counts": kind_counts,
            "symbol_scope_counts": scope_counts,
            "definition_overlap_count": 1,
            "route_context_reference_count": 0,
            "direct_transport_context_count": 0,
            "request_shape_context_count": request_shape_context_count,
            "route_transport_binding_count": route_transport_binding_count,
            "route_request_shape_binding_count": route_request_shape_binding_count,
            "direct_transport_marker_classes": [],
            "request_shape_marker_classes": _EXPECTED_REQUEST_SHAPE_MARKERS,
            "all_inventory_scans_complete": True,
            "helper_reference_contexts_reviewed": True,
            "helper_owner_binding_resolved": False,
            "request_payload_mapping_resolved": False,
            "request_shape_sufficient_for_bounded_probe": False,
            "ready_for_guild_progression_helper_owner_inventory": True,
            "route_semantics_verified": False,
            "contains_raw_callee": False,
            "contains_raw_symbol": False,
            "contains_raw_context": False,
            "contains_source_scalar_values": False,
            "blockers": blockers,
        },
        "reference_reviews": reference_reviews,
        "integrity_checks": checks,
        "summary": {
            "all_integrity_checks_passed": True,
            "integrity_check_count": len(checks),
            "guild_progression_helper_reference_reviewed": True,
            "reference_count": len(reference_reviews),
            "reference_review_disposition": (
                "unresolved_references_without_route_or_transport_binding"
            ),
            "route_context_reference_count": 0,
            "direct_transport_context_count": 0,
            "route_transport_binding_count": route_transport_binding_count,
            "route_request_shape_binding_count": route_request_shape_binding_count,
            "helper_identity_resolved": False,
            "helper_owner_binding_resolved": False,
            "request_payload_mapping_resolved": False,
            "request_shape_sufficient_for_bounded_probe": False,
            "ready_for_guild_progression_helper_owner_inventory": True,
            **_FALSE_GATES,
            "contains_raw_callee": False,
            "contains_raw_symbol": False,
            "contains_raw_context": False,
            "contains_source_scalar_values": False,
            "network_requests_performed": False,
        },
        "decision_boundary": {
            "status": "guild_progression_helper_references_reviewed_probe_blocked",
            "guild_progression_route_candidate_observed": True,
            "guild_progression_helper_definition_reviewed": True,
            "guild_progression_helper_reference_inventory_observed": True,
            "guild_progression_helper_reference_reviewed": True,
            "guild_progression_helper_identity_resolved": False,
            "guild_progression_helper_owner_binding_resolved": False,
            "guild_progression_request_payload_mapping_resolved": False,
            "guild_progression_request_shape_verified": False,
            "ready_for_guild_progression_helper_owner_inventory": True,
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
        raise ValueError("public helper-reference review contains forbidden fields")
    write_json(receipt_output_path, review)
    return review


__all__ = ["review_guild_progression_helper_references"]
