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
from .guild_progression_helper_owner_index import owner_candidates

KIND = "guild_progression_helper_owner_inventory"
PRIVATE_KIND = f"{KIND}_private"
VERSION = "guild-progression-helper-owner-inventory-v1"
ROUTE = "/api/guilds/progression"

_REFERENCE_REVIEW_KIND = "guild_progression_helper_reference_review"
_REFERENCE_REVIEW_VERSION = "guild-progression-helper-reference-review-v1"
_REFERENCE_INVENTORY_KIND = "guild_progression_helper_reference_inventory"
_REFERENCE_PRIVATE_KIND = f"{_REFERENCE_INVENTORY_KIND}_private"
_REFERENCE_INVENTORY_VERSION = "guild-progression-helper-reference-inventory-v1"

_IDENTIFIER = r"[A-Za-z_$][A-Za-z0-9_$]*"
_CALLEE_PATTERN = re.compile(rf"{_IDENTIFIER}(?:\.{_IDENTIFIER})*")
_REFERENCE_KINDS = {
    "definition_candidate",
    "invocation",
    "assignment_target",
    "object_key",
    "member_reference",
    "identifier_reference",
}
_SYMBOL_SCOPES = {"full_chain", "terminal_symbol"}
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
    "asset_content_manifest_path",
    "asset_url",
    "callee",
    "context",
    "context_end",
    "context_start",
    "end",
    "owner_chain",
    "owner_end",
    "owner_start",
    "private_excerpt",
    "private_query",
    "raw_callee",
    "raw_context",
    "raw_definition",
    "raw_owner_chain",
    "raw_payload",
    "raw_records",
    "raw_symbol",
    "request_url",
    "source_guild_id",
    "span",
    "start",
    "symbol",
}


def _require_false_fields(
    value: Mapping[str, Any],
    fields: tuple[str, ...],
    label: str,
) -> None:
    for field in fields:
        if value.get(field) is not False:
            raise ValueError(f"{label} mismatch: {field}")


def _validate_reference_review(
    review: Mapping[str, Any],
    public_inventory_path: Path,
    public_inventory_body: bytes,
    private_inventory_path: Path,
    private_inventory_body: bytes,
) -> None:
    expect(
        review,
        {
            "schema_version": 1,
            "review_kind": _REFERENCE_REVIEW_KIND,
            "review_version": _REFERENCE_REVIEW_VERSION,
            "source_inventory_name": public_inventory_path.name,
            "source_private_inventory_name": private_inventory_path.name,
        },
        "helper-reference review",
    )
    require_checks(review.get("integrity_checks"), 46, "helper-reference review checks")
    if property_names(review) & _FORBIDDEN_PUBLIC_FIELDS:
        raise ValueError("helper-reference review contains forbidden public fields")

    declared_public = sha256_value(
        review.get("source_inventory_sha256"),
        "helper-reference review public inventory SHA-256",
    )
    if declared_public not in document_hashes(public_inventory_body):
        raise ValueError("helper-reference review public inventory SHA-256 mismatch")
    declared_private = sha256_value(
        review.get("source_private_inventory_sha256"),
        "helper-reference review private inventory SHA-256",
    )
    if declared_private != sha256(private_inventory_body):
        raise ValueError("helper-reference review private inventory SHA-256 mismatch")

    summary = object_value(review.get("summary"), "helper-reference review summary")
    expect(
        summary,
        {
            "all_integrity_checks_passed": True,
            "integrity_check_count": 46,
            "guild_progression_helper_reference_reviewed": True,
            "reference_count": 31,
            "reference_review_disposition": (
                "unresolved_references_without_route_or_transport_binding"
            ),
            "route_context_reference_count": 0,
            "direct_transport_context_count": 0,
            "route_transport_binding_count": 0,
            "route_request_shape_binding_count": 0,
            "helper_identity_resolved": False,
            "helper_owner_binding_resolved": False,
            "request_payload_mapping_resolved": False,
            "request_shape_sufficient_for_bounded_probe": False,
            "ready_for_guild_progression_helper_owner_inventory": True,
            "contains_raw_callee": False,
            "contains_raw_symbol": False,
            "contains_raw_context": False,
            "contains_source_scalar_values": False,
            "network_requests_performed": False,
        },
        "helper-reference review summary",
    )
    _require_false_fields(summary, _FALSE_GATES, "helper-reference review summary")


def _validate_public_reference_inventory(
    inventory: Mapping[str, Any],
    private_inventory_path: Path,
    private_inventory_body: bytes,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    expect(
        inventory,
        {
            "schema_version": 1,
            "inventory_kind": _REFERENCE_INVENTORY_KIND,
            "inventory_version": _REFERENCE_INVENTORY_VERSION,
            "source_private_inventory_name": private_inventory_path.name,
        },
        "public helper-reference inventory",
    )
    require_checks(
        inventory.get("integrity_checks"),
        40,
        "public helper-reference inventory checks",
    )
    if property_names(inventory) & _FORBIDDEN_PUBLIC_FIELDS:
        raise ValueError("public helper-reference inventory contains forbidden fields")
    if sha256_value(
        inventory.get("source_private_inventory_sha256"),
        "public helper-reference private inventory SHA-256",
    ) != sha256(private_inventory_body):
        raise ValueError("public helper-reference private inventory SHA-256 mismatch")

    target = object_value(inventory.get("target"), "public helper-reference target")
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
        "public helper-reference target",
    )
    sha256_value(target.get("callee_sha256"), "public helper-reference callee SHA-256")

    summary = object_value(inventory.get("summary"), "public helper-reference summary")
    expect(
        summary,
        {
            "all_integrity_checks_passed": True,
            "integrity_check_count": 40,
            "full_chain_occurrence_count_observed": 2,
            "terminal_symbol_occurrence_count_observed": 31,
            "terminal_symbol_only_occurrence_count": 29,
            "unique_reference_candidate_count": 31,
            "definition_overlap_count": 1,
            "route_context_reference_count": 0,
            "reference_evidence_observed": True,
            "ready_for_guild_progression_helper_reference_review": True,
            "guild_progression_helper_identity_resolved": False,
            "guild_progression_request_payload_mapping_resolved": False,
            "guild_progression_request_shape_verified": False,
            "contains_raw_callee": False,
            "contains_raw_symbol": False,
            "contains_raw_context": False,
            "contains_source_scalar_values": False,
            "network_requests_performed": False,
        },
        "public helper-reference summary",
    )
    _require_false_fields(summary, _FALSE_GATES, "public helper-reference summary")

    raw_references = array_value(inventory.get("references"), "public helper references")
    if len(raw_references) != 31:
        raise ValueError("expected exactly 31 public helper references")
    references: list[dict[str, Any]] = []
    for expected_index, raw in enumerate(raw_references, 1):
        row = object_value(raw, f"public helper reference {expected_index}")
        expect(
            row,
            {
                "reference_index": expected_index,
                "contains_raw_symbol": False,
                "contains_raw_context": False,
                "contains_source_scalar_values": False,
            },
            f"public helper reference {expected_index}",
        )
        if row.get("symbol_scope") not in _SYMBOL_SCOPES:
            raise ValueError(
                f"public helper reference {expected_index} symbol scope mismatch"
            )
        if row.get("reference_kind") not in _REFERENCE_KINDS:
            raise ValueError(f"public helper reference {expected_index} kind mismatch")
        sha256_value(
            row.get("context_sha256"),
            f"public helper reference {expected_index} context SHA-256",
        )
        count = integer_value(
            row.get("context_character_count"),
            f"public helper reference {expected_index} context character count",
        )
        if count < 1:
            raise ValueError(
                f"public helper reference {expected_index} context count is invalid"
            )
        references.append(row)
    return target, references


def _validate_private_reference_inventory(
    private_inventory: Mapping[str, Any],
    target: Mapping[str, Any],
    public_references: list[dict[str, Any]],
) -> tuple[str, str, list[dict[str, Any]]]:
    expect(
        private_inventory,
        {
            "schema_version": 1,
            "inventory_kind": _REFERENCE_PRIVATE_KIND,
            "inventory_version": _REFERENCE_INVENTORY_VERSION,
            "route": ROUTE,
        },
        "private helper-reference inventory",
    )
    callee = private_inventory.get("callee")
    if not isinstance(callee, str) or not _CALLEE_PATTERN.fullmatch(callee):
        raise ValueError("private helper callee is missing or malformed")
    callee_hash = sha256_value(
        private_inventory.get("callee_sha256"),
        "private helper callee SHA-256",
    )
    if sha256(callee.encode()) != callee_hash or target.get("callee_sha256") != callee_hash:
        raise ValueError("public/private helper callee SHA-256 mismatch")
    payload_hash = sha256_value(
        private_inventory.get("asset_payload_hash"),
        "private helper-reference asset SHA-256",
    )

    summary = object_value(
        private_inventory.get("summary"),
        "private helper-reference summary",
    )
    expect(
        summary,
        {
            "full_chain_occurrence_count_observed": 2,
            "terminal_symbol_occurrence_count_observed": 31,
            "terminal_symbol_only_occurrence_count": 29,
            "unique_reference_candidate_count": 31,
            "definition_overlap_count": 1,
            "route_context_reference_count": 0,
            "contains_source_scalar_values": True,
            "network_requests_performed": False,
        },
        "private helper-reference summary",
    )

    raw_references = array_value(
        private_inventory.get("references"),
        "private helper references",
    )
    if len(raw_references) != len(public_references):
        raise ValueError("public/private helper-reference count mismatch")
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
    private_references: list[dict[str, Any]] = []
    for expected_index, (raw_private, public_row) in enumerate(
        zip(raw_references, public_references, strict=True),
        1,
    ):
        row = object_value(raw_private, f"private helper reference {expected_index}")
        for field in aligned_fields:
            if row.get(field) != public_row.get(field):
                raise ValueError(
                    f"public/private helper reference {expected_index} mismatch: {field}"
                )
        symbol = row.get("raw_symbol")
        if not isinstance(symbol, str) or not symbol:
            raise ValueError(
                f"private helper reference {expected_index} raw symbol is missing"
            )
        start = integer_value(
            row.get("start"),
            f"private helper reference {expected_index} start",
        )
        end = integer_value(
            row.get("end"),
            f"private helper reference {expected_index} end",
        )
        if start < 0 or end <= start or end - start != len(symbol):
            raise ValueError(
                f"private helper reference {expected_index} symbol span is invalid"
            )
        context = row.get("context")
        if not isinstance(context, str):
            raise ValueError(
                f"private helper reference {expected_index} context is missing"
            )
        if sha256(context.encode()) != public_row.get("context_sha256"):
            raise ValueError(
                f"private helper reference {expected_index} context SHA-256 mismatch"
            )
        if len(context) != public_row.get("context_character_count"):
            raise ValueError(
                f"private helper reference {expected_index} context length mismatch"
            )
        context_start = integer_value(
            row.get("context_start"),
            f"private helper reference {expected_index} context start",
        )
        context_end = integer_value(
            row.get("context_end"),
            f"private helper reference {expected_index} context end",
        )
        if (
            context_start < 0
            or context_end <= context_start
            or context_end - context_start != len(context)
        ):
            raise ValueError(
                f"private helper reference {expected_index} context span is invalid"
            )
        private_references.append(row)
    return callee, payload_hash, private_references


def _validate_references_against_asset(
    text: str,
    private_references: list[dict[str, Any]],
) -> None:
    for row in private_references:
        index = int(row["reference_index"])
        start = int(row["start"])
        end = int(row["end"])
        if text[start:end] != row["raw_symbol"]:
            raise ValueError(f"raw asset reference {index} symbol span mismatch")
        context_start = int(row["context_start"])
        context_end = int(row["context_end"])
        if text[context_start:context_end] != row["context"]:
            raise ValueError(f"raw asset reference {index} context span mismatch")


def _checks() -> dict[str, bool]:
    names = """
    reference_review_contract_verified reference_review_checks_verified
    reference_review_privacy_verified reference_review_next_gate_verified
    public_reference_inventory_contract_verified public_reference_inventory_checks_verified
    public_reference_inventory_privacy_verified reference_review_inventory_name_verified
    reference_review_inventory_hash_verified reference_review_private_name_verified
    reference_review_private_hash_verified public_inventory_private_name_verified
    public_inventory_private_hash_verified private_reference_inventory_contract_verified
    private_reference_inventory_route_verified private_callee_hash_verified
    public_private_callee_hash_verified private_asset_hash_verified
    asset_payload_hash_verified asset_payload_path_confined_to_raw_root
    public_private_reference_count_verified public_private_reference_indexes_verified
    public_private_symbol_scopes_verified public_private_reference_kinds_verified
    public_private_context_hashes_verified public_private_context_lengths_verified
    public_private_definition_overlap_verified private_symbol_spans_verified
    private_context_spans_verified raw_asset_symbol_spans_verified
    raw_asset_context_spans_verified owner_prefix_scan_bounded
    definition_container_scan_bounded owner_candidate_hashes_generated
    owner_candidate_counts_reconciled owner_group_counts_reconciled
    cross_definition_reference_groups_reconciled raw_owner_chains_kept_private
    raw_symbols_kept_private raw_contexts_kept_private
    public_receipt_privacy_verified public_receipt_scalar_boundary_preserved
    network_requests_performed_false helper_identity_not_inferred
    helper_owner_binding_not_inferred request_payload_mapping_not_inferred
    request_shape_not_inferred route_probe_remains_disabled
    route_semantics_not_overclaimed pagination_not_overclaimed
    termination_not_overclaimed completeness_not_overclaimed
    full_crawl_and_scoring_remain_disabled helper_owner_review_selected_as_next_gate
    """.split()
    checks = {name: True for name in names}
    if len(checks) != 54:
        raise RuntimeError("helper-owner inventory integrity-check contract drift")
    return checks


def inventory_guild_progression_helper_owners(
    *,
    reference_review_path: Path,
    public_reference_inventory_path: Path,
    private_reference_inventory_path: Path,
    raw_root: Path,
    private_output_path: Path,
    receipt_output_path: Path,
    max_owner_prefix_chars: int = 512,
    max_definition_container_chars: int = 2048,
) -> dict[str, Any]:
    """Inventory bounded lexical owner candidates without enabling a route probe."""
    review, review_body = load_json(reference_review_path, "helper-reference review")
    public_inventory, public_inventory_body = load_json(
        public_reference_inventory_path,
        "public helper-reference inventory",
    )
    private_inventory, private_inventory_body = load_json(
        private_reference_inventory_path,
        "private helper-reference inventory",
    )

    _validate_reference_review(
        review,
        public_reference_inventory_path,
        public_inventory_body,
        private_reference_inventory_path,
        private_inventory_body,
    )
    target, public_references = _validate_public_reference_inventory(
        public_inventory,
        private_reference_inventory_path,
        private_inventory_body,
    )
    callee, payload_hash, private_references = _validate_private_reference_inventory(
        private_inventory,
        target,
        public_references,
    )

    asset_body, manifest_path = load_asset(raw_root, payload_hash)
    text = asset_body.decode("utf-8", errors="ignore").replace("\\/", "/")
    _validate_references_against_asset(text, private_references)

    private_candidates, owner_result = owner_candidates(
        text,
        callee,
        private_references,
        max_owner_prefix_chars=max_owner_prefix_chars,
        max_definition_container_chars=max_definition_container_chars,
    )
    private_groups = list(owner_result["groups"])
    evidence = dict(owner_result["evidence"])

    public_candidates = [
        {
            "candidate_index": row["candidate_index"],
            "reference_index": row["reference_index"],
            "symbol_scope": row["symbol_scope"],
            "reference_kind": row["reference_kind"],
            "definition_candidate_overlap": row["definition_candidate_overlap"],
            "candidate_source": row["candidate_source"],
            "owner_chain_sha256": row["owner_chain_sha256"],
            "owner_chain_character_count": row["owner_chain_character_count"],
            "owner_chain_depth": row["owner_chain_depth"],
            "source_reference_context_sha256": row[
                "source_reference_context_sha256"
            ],
            "contains_raw_owner_chain": False,
            "contains_raw_symbol": False,
            "contains_raw_context": False,
            "contains_source_scalar_values": False,
        }
        for row in private_candidates
    ]
    public_groups = [
        {
            "owner_group_index": group["owner_group_index"],
            "owner_chain_sha256": group["owner_chain_sha256"],
            "owner_chain_character_count": group["owner_chain_character_count"],
            "owner_chain_depth": group["owner_chain_depth"],
            "occurrence_count": group["occurrence_count"],
            "reference_indexes": list(group["reference_indexes"]),
            "candidate_sources": list(group["candidate_sources"]),
            "definition_candidate_count": group["definition_candidate_count"],
            "non_definition_candidate_count": group["non_definition_candidate_count"],
            "cross_definition_reference_binding_observed": group[
                "cross_definition_reference_binding_observed"
            ],
            "raw_owner_chain_published": False,
            "contains_source_scalar_values": False,
        }
        for group in private_groups
    ]

    private_body_out = write_json(
        private_output_path,
        {
            "schema_version": 1,
            "inventory_kind": PRIVATE_KIND,
            "inventory_version": VERSION,
            "generated_at": generated_at(),
            "source_reference_review_sha256": sha256(review_body),
            "source_public_reference_inventory_sha256": sha256(
                public_inventory_body
            ),
            "source_private_reference_inventory_sha256": sha256(
                private_inventory_body
            ),
            "asset_payload_hash": payload_hash,
            "asset_content_manifest_path": str(manifest_path),
            "route": ROUTE,
            "callee": callee,
            "callee_sha256": target["callee_sha256"],
            "owner_candidates": private_candidates,
            "owner_groups": private_groups,
            "summary": {
                **evidence,
                "contains_raw_owner_chain": bool(private_candidates),
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
        "source_reference_review_name": reference_review_path.name,
        "source_reference_review_sha256": sha256(canonical_lf(review_body)),
        "source_reference_inventory_name": public_reference_inventory_path.name,
        "source_reference_inventory_sha256": sha256(
            canonical_lf(public_inventory_body)
        ),
        "source_private_reference_inventory_name": (
            private_reference_inventory_path.name
        ),
        "source_private_reference_inventory_sha256": sha256(
            private_inventory_body
        ),
        "source_private_inventory_name": private_output_path.name,
        "source_private_inventory_sha256": sha256(private_body_out),
        "target": {
            "guild_label": "Argentum",
            "route_template": ROUTE,
            "callee_sha256": target["callee_sha256"],
            "callee_published": False,
            "owner_chain_published": False,
            "raw_symbol_published": False,
            "raw_context_published": False,
            "source_scalar_values_published": False,
        },
        "inventory_contract": {
            "network_requests_performed": False,
            "raw_archive_only": True,
            "max_owner_prefix_chars": max_owner_prefix_chars,
            "max_definition_container_chars": max_definition_container_chars,
            "owner_candidate_classes_only": True,
        },
        "owner_candidates": public_candidates,
        "owner_groups": public_groups,
        "cross_owner_evidence": {
            **evidence,
            "helper_owner_inventory_completed": True,
            "helper_owner_binding_resolved": False,
            "contains_raw_owner_chain": False,
            "contains_raw_symbol": False,
            "contains_raw_context": False,
            "contains_source_scalar_values": False,
        },
        "integrity_checks": checks,
        "summary": {
            "all_integrity_checks_passed": True,
            "integrity_check_count": len(checks),
            **evidence,
            "guild_progression_helper_owner_inventory_completed": True,
            "helper_identity_resolved": False,
            "helper_owner_binding_resolved": False,
            "request_payload_mapping_resolved": False,
            "request_shape_sufficient_for_bounded_probe": False,
            "ready_for_guild_progression_helper_owner_review": True,
            **{field: False for field in _FALSE_GATES},
            "contains_raw_owner_chain": False,
            "contains_raw_symbol": False,
            "contains_raw_context": False,
            "contains_source_scalar_values": False,
            "network_requests_performed": False,
        },
        "decision_boundary": {
            "status": "guild_progression_helper_owner_inventory_completed_probe_blocked",
            "guild_progression_route_candidate_observed": True,
            "guild_progression_helper_reference_reviewed": True,
            "guild_progression_helper_owner_inventory_completed": True,
            "guild_progression_helper_identity_resolved": False,
            "guild_progression_helper_owner_binding_resolved": False,
            "guild_progression_request_payload_mapping_resolved": False,
            "guild_progression_request_shape_verified": False,
            "ready_for_guild_progression_helper_owner_review": True,
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
        raise ValueError("public helper-owner inventory contains forbidden fields")
    write_json(receipt_output_path, receipt)
    return receipt


__all__ = ["inventory_guild_progression_helper_owners"]
