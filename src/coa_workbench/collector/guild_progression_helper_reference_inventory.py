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
    load_asset,
    load_json,
    object_value,
    property_names,
    require_checks,
    sha256,
    sha256_value,
    write_json,
)
from .guild_progression_helper_reference_index import reference_candidates

KIND = "guild_progression_helper_reference_inventory"
PRIVATE_KIND = f"{KIND}_private"
VERSION = "guild-progression-helper-reference-inventory-v1"
ROUTE = "/api/guilds/progression"
_DEFINITION_KIND = "guild_progression_helper_definition_inventory"
_DEFINITION_PRIVATE_KIND = f"{_DEFINITION_KIND}_private"
_DEFINITION_VERSION = "guild-progression-helper-definition-inventory-v1"
_REVIEW_KIND = "guild_progression_helper_definition_review"
_REVIEW_VERSION = "guild-progression-helper-definition-review-v1"
_CALLEE_PATTERN = re.compile(
    r"[A-Za-z_$][A-Za-z0-9_$]*(?:\.[A-Za-z_$][A-Za-z0-9_$]*)*"
)
_FALSE_GATES = (
    "ready_for_bounded_progression_route_probe",
    "guild_api_route_semantics_verified",
    "pagination_semantics_verified",
    "termination_semantics_verified",
    "completeness_verified",
    "ready_for_full_guild_crawl",
    "planner_scoring_allowed",
)
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


def _require_false_fields(value: Mapping[str, Any], fields: tuple[str, ...], label: str) -> None:
    for field in fields:
        if value.get(field) is not False:
            raise ValueError(f"{label} mismatch: {field}")


def _validate_review(review: Mapping[str, Any]) -> None:
    expect(
        review,
        {
            "schema_version": 1,
            "review_kind": _REVIEW_KIND,
            "review_version": _REVIEW_VERSION,
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
    _require_false_fields(summary, _FALSE_GATES, "helper-definition review summary")
    if property_names(review) & _FORBIDDEN_PUBLIC_FIELDS:
        raise ValueError("helper-definition review contains forbidden public fields")


def _validate_public_inventory(
    inventory: Mapping[str, Any],
    inventory_body: bytes,
    review: Mapping[str, Any],
    private_inventory_path: Path,
    private_inventory_body: bytes,
) -> tuple[dict[str, Any], dict[str, Any]]:
    expect(
        inventory,
        {
            "schema_version": 1,
            "inventory_kind": _DEFINITION_KIND,
            "inventory_version": _DEFINITION_VERSION,
            "source_private_inventory_name": private_inventory_path.name,
        },
        "public helper-definition inventory",
    )
    require_checks(inventory.get("integrity_checks"), 36, "definition inventory checks")
    if property_names(inventory) & _FORBIDDEN_PUBLIC_FIELDS:
        raise ValueError("public helper-definition inventory contains forbidden fields")
    if sha256_value(review.get("source_inventory_sha256"), "review inventory hash") not in (
        document_hashes(inventory_body)
    ):
        raise ValueError("review source inventory SHA-256 mismatch")
    private_hash = sha256(private_inventory_body)
    if sha256_value(review.get("source_private_inventory_sha256"), "review private hash") != (
        private_hash
    ):
        raise ValueError("review source private inventory SHA-256 mismatch")
    if sha256_value(inventory.get("source_private_inventory_sha256"), "inventory private hash") != (
        private_hash
    ):
        raise ValueError("definition inventory private SHA-256 mismatch")

    target = object_value(inventory.get("target"), "definition inventory target")
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
        "definition inventory target",
    )
    sha256_value(target.get("callee_sha256"), "definition inventory callee hash")

    evidence = object_value(inventory.get("cross_definition_evidence"), "definition evidence")
    expect(
        evidence,
        {
            "full_chain_occurrence_scan_truncated": False,
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
        },
        "definition evidence",
    )
    full_count = integer_value(evidence.get("full_chain_occurrence_count_observed"), "full count")
    terminal_count = integer_value(
        evidence.get("terminal_symbol_occurrence_count_observed"),
        "terminal count",
    )
    if full_count < 1 or terminal_count < full_count:
        raise ValueError("definition inventory occurrence counts are invalid")
    return target, evidence


def _validate_private_inventory(
    private_inventory: Mapping[str, Any],
    target: Mapping[str, Any],
) -> tuple[str, str, str, tuple[tuple[int, int], ...]]:
    expect(
        private_inventory,
        {
            "schema_version": 1,
            "inventory_kind": _DEFINITION_PRIVATE_KIND,
            "inventory_version": _DEFINITION_VERSION,
            "route": ROUTE,
        },
        "private helper-definition inventory",
    )
    callee = private_inventory.get("callee")
    if not isinstance(callee, str) or not _CALLEE_PATTERN.fullmatch(callee):
        raise ValueError("private helper callee is missing or malformed")
    callee_hash = sha256_value(private_inventory.get("callee_sha256"), "private callee hash")
    if sha256(callee.encode()) != callee_hash or target.get("callee_sha256") != callee_hash:
        raise ValueError("public/private helper callee SHA-256 mismatch")
    payload_hash = sha256_value(private_inventory.get("asset_payload_hash"), "asset hash")
    candidates = array_value(private_inventory.get("definition_candidates"), "definitions")
    if len(candidates) != 1:
        raise ValueError("expected exactly one private definition candidate")
    item = object_value(candidates[0], "private definition candidate")
    start = integer_value(item.get("start"), "private definition start")
    end = integer_value(item.get("end"), "private definition end")
    span = item.get("span")
    if start < 0 or end <= start or not isinstance(span, str) or len(span) != end - start:
        raise ValueError("private definition span is invalid")
    if sha256(span.encode()) != sha256_value(item.get("span_sha256"), "definition span hash"):
        raise ValueError("private definition span SHA-256 mismatch")
    return callee, callee_hash, payload_hash, ((start, end),)


def _checks() -> dict[str, bool]:
    names = """
    definition_review_contract_verified definition_review_checks_verified
    definition_review_privacy_verified definition_review_next_gate_verified
    public_definition_inventory_contract_verified public_definition_inventory_checks_verified
    public_definition_inventory_privacy_verified review_inventory_hash_verified
    review_private_hash_verified public_private_hash_verified
    private_definition_inventory_contract_verified private_definition_route_verified
    private_callee_hash_verified public_private_callee_hash_verified
    private_asset_hash_verified private_definition_span_verified
    asset_payload_hash_verified asset_payload_path_confined_to_raw_root
    full_chain_scan_bounded terminal_symbol_scan_bounded reference_scan_bounded
    reference_context_bounded occurrence_counts_reconciled definition_overlap_preserved
    reference_context_hashes_generated raw_symbols_kept_private raw_contexts_kept_private
    public_receipt_privacy_verified public_receipt_scalar_boundary_preserved
    network_requests_performed_false helper_identity_not_inferred
    request_payload_mapping_not_inferred request_shape_not_inferred
    route_probe_remains_disabled route_semantics_not_overclaimed
    pagination_not_overclaimed termination_not_overclaimed completeness_not_overclaimed
    full_crawl_and_scoring_remain_disabled helper_reference_review_selected_as_next_gate
    """.split()
    checks = {name: True for name in names}
    if len(checks) != 40:
        raise RuntimeError("helper-reference inventory integrity-check contract drift")
    return checks


def inventory_guild_progression_helper_references(
    *,
    definition_review_path: Path,
    public_definition_inventory_path: Path,
    private_definition_inventory_path: Path,
    raw_root: Path,
    private_output_path: Path,
    receipt_output_path: Path,
    max_symbol_occurrences: int = 500,
    max_reference_candidates: int = 500,
    private_context_chars: int = 1024,
) -> dict[str, Any]:
    review, review_body = load_json(definition_review_path, "helper-definition review")
    public_inventory, public_inventory_body = load_json(
        public_definition_inventory_path,
        "public helper-definition inventory",
    )
    private_inventory, private_inventory_body = load_json(
        private_definition_inventory_path,
        "private helper-definition inventory",
    )
    _validate_review(review)
    target, declared = _validate_public_inventory(
        public_inventory,
        public_inventory_body,
        review,
        private_definition_inventory_path,
        private_inventory_body,
    )
    callee, callee_hash, payload_hash, definition_spans = _validate_private_inventory(
        private_inventory,
        target,
    )
    asset_body, manifest_path = load_asset(raw_root, payload_hash)
    text = asset_body.decode("utf-8", errors="ignore").replace("\\/", "/")
    private_rows, evidence = reference_candidates(
        text,
        callee,
        definition_spans=definition_spans,
        route_template=ROUTE,
        max_symbol_occurrences=max_symbol_occurrences,
        max_reference_candidates=max_reference_candidates,
        private_context_chars=private_context_chars,
    )
    for field in (
        "full_chain_occurrence_count_observed",
        "terminal_symbol_occurrence_count_observed",
    ):
        if evidence[field] != declared[field]:
            raise ValueError(f"{field.replace('_', '-')} does not reconcile")
    for field in (
        "full_chain_occurrence_scan_truncated",
        "terminal_symbol_occurrence_scan_truncated",
        "reference_candidate_scan_truncated",
    ):
        if evidence[field]:
            raise ValueError(f"{field.replace('_', ' ')} is true")

    public_rows = [
        {
            "reference_index": index,
            "symbol_scope": row["symbol_scope"],
            "reference_kind": row["reference_kind"],
            "context_sha256": row["context_sha256"],
            "context_character_count": row["context_character_count"],
            "definition_candidate_overlap": row["definition_candidate_overlap"],
            "route_template_observed": row["route_template_observed"],
            "direct_transport_markers": row["direct_transport_markers"],
            "request_shape_markers": row["request_shape_markers"],
            "contains_raw_symbol": False,
            "contains_raw_context": False,
            "contains_source_scalar_values": False,
        }
        for index, row in enumerate(private_rows, 1)
    ]
    private_body_out = write_json(
        private_output_path,
        {
            "schema_version": 1,
            "inventory_kind": PRIVATE_KIND,
            "inventory_version": VERSION,
            "generated_at": generated_at(),
            "source_definition_review_sha256": sha256(review_body),
            "source_public_definition_inventory_sha256": sha256(public_inventory_body),
            "source_private_definition_inventory_sha256": sha256(private_inventory_body),
            "asset_payload_hash": payload_hash,
            "asset_content_manifest_path": str(manifest_path),
            "route": ROUTE,
            "callee": callee,
            "callee_sha256": callee_hash,
            "definition_spans": [
                {"start": start, "end": end} for start, end in definition_spans
            ],
            "references": [
                {**row, "reference_index": index}
                for index, row in enumerate(private_rows, 1)
            ],
            "summary": {
                **evidence,
                "contains_source_scalar_values": True,
                "network_requests_performed": False,
            },
        },
    )
    checks = _checks()
    receipt = {
        "schema_version": 1,
        "inventory_kind": KIND,
        "inventory_version": VERSION,
        "generated_at": generated_at(),
        "source_definition_review_name": definition_review_path.name,
        "source_definition_review_sha256": sha256(canonical_lf(review_body)),
        "source_public_definition_inventory_name": public_definition_inventory_path.name,
        "source_public_definition_inventory_sha256": sha256(
            canonical_lf(public_inventory_body)
        ),
        "source_private_definition_inventory_name": private_definition_inventory_path.name,
        "source_private_definition_inventory_sha256": sha256(private_inventory_body),
        "source_private_inventory_name": private_output_path.name,
        "source_private_inventory_sha256": sha256(private_body_out),
        "target": {
            "guild_label": "Argentum",
            "route_template": ROUTE,
            "callee_sha256": callee_hash,
            "callee_published": False,
            "raw_symbol_published": False,
            "raw_context_published": False,
            "source_scalar_values_published": False,
        },
        "request_contract": {
            "network_requests_performed": False,
            "raw_archive_only": True,
            "max_symbol_occurrences": max_symbol_occurrences,
            "max_reference_candidates": max_reference_candidates,
            "private_context_chars_per_side": private_context_chars,
        },
        "references": public_rows,
        "cross_reference_evidence": {
            **evidence,
            "reference_evidence_observed": bool(public_rows),
            "contains_raw_callee": False,
            "contains_raw_symbol": False,
            "contains_raw_context": False,
            "contains_source_scalar_values": False,
        },
        "integrity_checks": checks,
        "summary": {
            "all_integrity_checks_passed": True,
            "integrity_check_count": len(checks),
            **evidence,
            "reference_evidence_observed": bool(public_rows),
            "ready_for_guild_progression_helper_reference_review": True,
            "guild_progression_helper_identity_resolved": False,
            "guild_progression_request_payload_mapping_resolved": False,
            "guild_progression_request_shape_verified": False,
            **{field: False for field in _FALSE_GATES},
            "contains_raw_callee": False,
            "contains_raw_symbol": False,
            "contains_raw_context": False,
            "contains_source_scalar_values": False,
            "network_requests_performed": False,
        },
        "decision_boundary": {
            "status": "guild_progression_helper_reference_inventory_observed_probe_blocked",
            "guild_progression_route_candidate_observed": True,
            "guild_progression_helper_definition_reviewed": True,
            "guild_progression_helper_reference_inventory_observed": True,
            "guild_progression_helper_identity_resolved": False,
            "guild_progression_request_payload_mapping_resolved": False,
            "guild_progression_request_shape_verified": False,
            "ready_for_guild_progression_helper_reference_review": True,
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
    if property_names(receipt) & _FORBIDDEN_PUBLIC_FIELDS:
        raise ValueError("public helper-reference inventory contains forbidden fields")
    write_json(receipt_output_path, receipt)
    return receipt


__all__ = ["inventory_guild_progression_helper_references"]
