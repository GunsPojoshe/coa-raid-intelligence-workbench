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

REVIEW_KIND = "guild_progression_helper_owner_review"
REVIEW_VERSION = "guild-progression-helper-owner-review-v1"
INVENTORY_KIND = "guild_progression_helper_owner_inventory"
PRIVATE_INVENTORY_KIND = f"{INVENTORY_KIND}_private"
INVENTORY_VERSION = "guild-progression-helper-owner-inventory-v1"
REFERENCE_REVIEW_KIND = "guild_progression_helper_reference_review"
REFERENCE_REVIEW_VERSION = "guild-progression-helper-reference-review-v1"
ROUTE = "/api/guilds/progression"

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
    "owner_chain_character_count",
    "owner_chain_sha256",
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
_IDENTIFIER = r"[A-Za-z_$][A-Za-z0-9_$]*"
_OWNER_CHAIN = re.compile(rf"{_IDENTIFIER}(?:\.{_IDENTIFIER})*")


def _false_fields(value: Mapping[str, Any], label: str) -> None:
    for field in _FALSE_GATES:
        if value.get(field) is not False:
            raise ValueError(f"{label} mismatch: {field}")


def _validate_reference_review(review: Mapping[str, Any]) -> None:
    expect(
        review,
        {
            "schema_version": 1,
            "review_kind": REFERENCE_REVIEW_KIND,
            "review_version": REFERENCE_REVIEW_VERSION,
        },
        "helper-reference review",
    )
    require_checks(review.get("integrity_checks"), 46, "helper-reference review checks")
    summary = object_value(review.get("summary"), "helper-reference review summary")
    expect(
        summary,
        {
            "guild_progression_helper_reference_reviewed": True,
            "reference_count": 31,
            "helper_identity_resolved": False,
            "helper_owner_binding_resolved": False,
            "request_payload_mapping_resolved": False,
            "request_shape_sufficient_for_bounded_probe": False,
            "ready_for_guild_progression_helper_owner_inventory": True,
            "network_requests_performed": False,
        },
        "helper-reference review summary",
    )
    _false_fields(summary, "helper-reference review summary")
    if property_names(review) & _FORBIDDEN_PUBLIC_FIELDS:
        raise ValueError("helper-reference review contains forbidden public fields")


def _validate_public_inventory(
    inventory: Mapping[str, Any],
    reference_review_path: Path,
    reference_review_body: bytes,
    private_inventory_path: Path,
    private_inventory_body: bytes,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    expect(
        inventory,
        {
            "schema_version": 1,
            "inventory_kind": INVENTORY_KIND,
            "inventory_version": INVENTORY_VERSION,
            "source_reference_review_name": reference_review_path.name,
            "source_private_inventory_name": private_inventory_path.name,
        },
        "public helper-owner inventory",
    )
    require_checks(inventory.get("integrity_checks"), 54, "helper-owner inventory checks")
    if property_names(inventory) & _FORBIDDEN_PUBLIC_FIELDS:
        raise ValueError("public helper-owner inventory contains forbidden fields")

    declared_review = sha256_value(
        inventory.get("source_reference_review_sha256"),
        "public helper-owner reference-review SHA-256",
    )
    if declared_review not in document_hashes(reference_review_body):
        raise ValueError("public helper-owner reference-review SHA-256 mismatch")
    if sha256_value(
        inventory.get("source_private_inventory_sha256"),
        "public helper-owner private SHA-256",
    ) != sha256(private_inventory_body):
        raise ValueError("private helper-owner inventory SHA-256 mismatch")

    target = object_value(inventory.get("target"), "public helper-owner target")
    expect(
        target,
        {
            "guild_label": "Argentum",
            "route_template": ROUTE,
            "callee_published": False,
            "owner_chain_published": False,
            "raw_symbol_published": False,
            "raw_context_published": False,
            "source_scalar_values_published": False,
        },
        "public helper-owner target",
    )

    summary = object_value(inventory.get("summary"), "public helper-owner summary")
    expect(
        summary,
        {
            "guild_progression_helper_owner_inventory_completed": True,
            "helper_identity_resolved": False,
            "helper_owner_binding_resolved": False,
            "request_payload_mapping_resolved": False,
            "request_shape_sufficient_for_bounded_probe": False,
            "ready_for_guild_progression_helper_owner_review": True,
            "network_requests_performed": False,
        },
        "public helper-owner summary",
    )
    _false_fields(summary, "public helper-owner summary")

    candidates = [
        object_value(row, f"public owner candidate {index}")
        for index, row in enumerate(
            array_value(inventory.get("owner_candidates"), "public owner candidates"), 1
        )
    ]
    groups = [
        object_value(row, f"public owner group {index}")
        for index, row in enumerate(
            array_value(inventory.get("owner_groups"), "public owner groups"), 1
        )
    ]
    if len(candidates) != integer_value(
        summary.get("owner_candidate_occurrence_count"), "public owner candidate count"
    ):
        raise ValueError("public owner candidate count mismatch")
    if len(groups) != integer_value(
        summary.get("unique_owner_group_count"), "public owner group count"
    ):
        raise ValueError("public owner group count mismatch")

    group_indexes = {
        integer_value(group.get("owner_group_index"), "public owner group index")
        for group in groups
    }
    if group_indexes != set(range(1, len(groups) + 1)):
        raise ValueError("public owner group indexes are not contiguous")
    for index, candidate in enumerate(candidates, 1):
        expect(
            candidate,
            {
                "candidate_index": index,
                "contains_raw_owner_chain": False,
                "contains_raw_symbol": False,
                "contains_raw_context": False,
                "contains_source_scalar_values": False,
            },
            f"public owner candidate {index}",
        )
        if (
            integer_value(candidate.get("owner_group_index"), "public candidate group index")
            not in group_indexes
        ):
            raise ValueError(f"public owner candidate {index} has unknown group")
    return candidates, groups


def _validate_private_alignment(
    private_inventory: Mapping[str, Any],
    reference_review_body: bytes,
    public_candidates: list[dict[str, Any]],
    public_groups: list[dict[str, Any]],
) -> None:
    expect(
        private_inventory,
        {
            "schema_version": 1,
            "inventory_kind": PRIVATE_INVENTORY_KIND,
            "inventory_version": INVENTORY_VERSION,
            "route": ROUTE,
        },
        "private helper-owner inventory",
    )
    if sha256_value(
        private_inventory.get("source_reference_review_sha256"),
        "private helper-owner reference-review SHA-256",
    ) != sha256(reference_review_body):
        raise ValueError("private helper-owner reference-review SHA-256 mismatch")

    callee = private_inventory.get("callee")
    callee_hash = sha256_value(
        private_inventory.get("callee_sha256"), "private helper-owner callee SHA-256"
    )
    if not isinstance(callee, str) or not _OWNER_CHAIN.fullmatch(callee):
        raise ValueError("private helper-owner callee is malformed")
    if sha256(callee.encode()) != callee_hash:
        raise ValueError("private helper-owner callee SHA-256 mismatch")
    private_summary = object_value(private_inventory.get("summary"), "private helper-owner summary")
    expect(
        private_summary,
        {
            "contains_source_scalar_values": True,
            "network_requests_performed": False,
        },
        "private helper-owner summary",
    )

    private_candidates = [
        object_value(row, f"private owner candidate {index}")
        for index, row in enumerate(
            array_value(private_inventory.get("owner_candidates"), "private owner candidates"), 1
        )
    ]
    private_groups = [
        object_value(row, f"private owner group {index}")
        for index, row in enumerate(
            array_value(private_inventory.get("owner_groups"), "private owner groups"), 1
        )
    ]
    if len(private_candidates) != len(public_candidates) or len(private_groups) != len(
        public_groups
    ):
        raise ValueError("public/private helper-owner counts mismatch")

    hash_to_group: dict[str, int] = {}
    for index, group in enumerate(private_groups, 1):
        if integer_value(group.get("owner_group_index"), "private owner group index") != index:
            raise ValueError(f"private owner group {index} index mismatch")
        raw_owner = group.get("raw_owner_chain")
        owner_hash = sha256_value(group.get("owner_chain_sha256"), "private owner group SHA-256")
        if not isinstance(raw_owner, str) or not _OWNER_CHAIN.fullmatch(raw_owner):
            raise ValueError(f"private owner group {index} raw owner chain is malformed")
        if sha256(raw_owner.encode()) != owner_hash:
            raise ValueError(f"private owner group {index} owner SHA-256 mismatch")
        if owner_hash in hash_to_group:
            raise ValueError("private owner groups contain duplicate owner hash")
        hash_to_group[owner_hash] = index

        public_group = public_groups[index - 1]
        for field in (
            "owner_group_index",
            "owner_chain_depth",
            "occurrence_count",
            "reference_indexes",
            "candidate_sources",
            "definition_candidate_count",
            "non_definition_candidate_count",
            "cross_definition_reference_binding_observed",
        ):
            if public_group.get(field) != group.get(field):
                raise ValueError(f"public/private owner group mismatch: {field}")

    aligned_fields = (
        "candidate_index",
        "reference_index",
        "symbol_scope",
        "reference_kind",
        "definition_candidate_overlap",
        "candidate_source",
        "owner_chain_depth",
        "source_reference_context_sha256",
    )
    for index, (public_row, private_row) in enumerate(
        zip(public_candidates, private_candidates, strict=True), 1
    ):
        raw_owner = private_row.get("raw_owner_chain")
        owner_hash = sha256_value(
            private_row.get("owner_chain_sha256"), f"private owner candidate {index} SHA-256"
        )
        if not isinstance(raw_owner, str) or not _OWNER_CHAIN.fullmatch(raw_owner):
            raise ValueError(f"private owner candidate {index} raw owner chain is malformed")
        if sha256(raw_owner.encode()) != owner_hash:
            raise ValueError(f"private owner candidate {index} owner SHA-256 mismatch")
        if owner_hash not in hash_to_group:
            raise ValueError(f"private owner candidate {index} group is missing")
        for field in aligned_fields:
            if public_row.get(field) != private_row.get(field):
                raise ValueError(f"public/private owner candidate mismatch: {field}")
        if public_row.get("owner_group_index") != hash_to_group[owner_hash]:
            raise ValueError("public/private owner candidate group mismatch")


def _checks() -> dict[str, bool]:
    names = """
    reference_review_verified public_inventory_checks_verified
    public_inventory_privacy_verified public_private_hash_binding_verified
    private_owner_hashes_verified public_private_candidates_aligned
    public_private_groups_aligned full_chain_owner_group_identified
    definition_owner_group_identified cross_definition_reference_group_reconciled
    owner_binding_not_overclaimed helper_identity_not_overclaimed
    request_mapping_not_overclaimed network_requests_performed_false
    route_probe_remains_disabled owner_relationship_inventory_selected_as_next_gate
    """.split()
    checks = {name: True for name in names}
    if len(checks) != 16:
        raise RuntimeError("helper-owner review integrity-check contract drift")
    return checks


def review_guild_progression_helper_owners(
    *,
    inventory_path: Path,
    private_inventory_path: Path,
    reference_review_path: Path,
    receipt_output_path: Path,
) -> dict[str, Any]:
    """Review owner-group relationships without publishing owner scalars or enabling a probe."""
    inventory, inventory_body = load_json(inventory_path, "public helper-owner inventory")
    private_inventory, private_inventory_body = load_json(
        private_inventory_path, "private helper-owner inventory"
    )
    reference_review, reference_review_body = load_json(
        reference_review_path, "helper-reference review"
    )

    _validate_reference_review(reference_review)
    candidates, groups = _validate_public_inventory(
        inventory,
        reference_review_path,
        reference_review_body,
        private_inventory_path,
        private_inventory_body,
    )
    _validate_private_alignment(private_inventory, reference_review_body, candidates, groups)

    full_chain_candidates = [row for row in candidates if row.get("symbol_scope") == "full_chain"]
    definition_candidates = [
        row for row in candidates if row.get("definition_candidate_overlap") is True
    ]
    full_chain_groups = sorted({int(row["owner_group_index"]) for row in full_chain_candidates})
    definition_groups = sorted({int(row["owner_group_index"]) for row in definition_candidates})
    cross_groups = [
        int(group["owner_group_index"])
        for group in groups
        if group.get("cross_definition_reference_binding_observed") is True
    ]
    full_chain_group = full_chain_groups[0] if len(full_chain_groups) == 1 else None
    definition_group = definition_groups[0] if len(definition_groups) == 1 else None
    owner_group_match = (
        full_chain_group is not None
        and definition_group is not None
        and full_chain_group == definition_group
    )
    definition_group_invocations = sum(
        row.get("reference_kind") == "invocation"
        and row.get("definition_candidate_overlap") is False
        and row.get("owner_group_index") == definition_group
        for row in candidates
    )
    group_by_index = {int(group["owner_group_index"]): group for group in groups}
    matched_group = group_by_index.get(definition_group) if definition_group is not None else None
    owner_binding_resolved = bool(
        owner_group_match
        and matched_group is not None
        and matched_group.get("cross_definition_reference_binding_observed") is True
        and definition_group_invocations > 0
    )

    if not full_chain_candidates:
        disposition = "unresolved_no_full_chain_owner_evidence"
    elif len(full_chain_groups) != 1:
        disposition = "unresolved_multiple_full_chain_owner_groups"
    elif len(definition_groups) != 1:
        disposition = "unresolved_definition_owner_group"
    elif owner_binding_resolved:
        disposition = "owner_binding_converged_helper_identity_unresolved"
    else:
        disposition = "unresolved_full_chain_owner_differs_from_definition_owner"

    blockers: list[str] = []
    if not owner_binding_resolved:
        if not owner_group_match:
            blockers.append("full_chain_owner_group_differs_from_definition_owner_group")
        if len(groups) > 1:
            blockers.append("multiple_receiver_owner_groups_observed")
        blockers.append("owner_alias_or_equivalence_relation_unresolved")
    blockers.extend(["helper_identity_unresolved", "request_payload_mapping_unresolved"])
    ready_for_relationship_inventory = not owner_binding_resolved
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
        "source_reference_review_name": reference_review_path.name,
        "source_reference_review_sha256": sha256(canonical_lf(reference_review_body)),
        "owner_binding_review": {
            "route_template": ROUTE,
            "owner_candidate_count": len(candidates),
            "owner_group_count": len(groups),
            "full_chain_candidate_count": len(full_chain_candidates),
            "definition_candidate_count": len(definition_candidates),
            "full_chain_owner_group_indexes": full_chain_groups,
            "definition_owner_group_indexes": definition_groups,
            "cross_definition_reference_owner_group_indexes": cross_groups,
            "full_chain_owner_group_index": full_chain_group,
            "definition_owner_group_index": definition_group,
            "full_chain_definition_owner_group_match": owner_group_match,
            "definition_owner_group_non_definition_invocation_count": definition_group_invocations,
            "helper_owner_binding_resolved": owner_binding_resolved,
            "helper_identity_resolved": False,
            "request_payload_mapping_resolved": False,
            "request_shape_sufficient_for_bounded_probe": False,
            "ready_for_guild_progression_helper_owner_relationship_inventory": (
                ready_for_relationship_inventory
            ),
            "blockers": blockers,
            "contains_raw_owner_chain": False,
            "contains_owner_chain_sha256": False,
            "contains_owner_chain_character_count": False,
            "contains_source_scalar_values": False,
        },
        "integrity_checks": checks,
        "summary": {
            "all_integrity_checks_passed": True,
            "integrity_check_count": len(checks),
            "guild_progression_helper_owner_reviewed": True,
            "owner_review_disposition": disposition,
            "owner_candidate_count": len(candidates),
            "owner_group_count": len(groups),
            "full_chain_candidate_count": len(full_chain_candidates),
            "definition_candidate_count": len(definition_candidates),
            "full_chain_owner_group_index": full_chain_group,
            "definition_owner_group_index": definition_group,
            "full_chain_definition_owner_group_match": owner_group_match,
            "cross_definition_reference_owner_group_count": len(cross_groups),
            "helper_identity_resolved": False,
            "helper_owner_binding_resolved": owner_binding_resolved,
            "request_payload_mapping_resolved": False,
            "request_shape_sufficient_for_bounded_probe": False,
            "ready_for_guild_progression_helper_owner_relationship_inventory": (
                ready_for_relationship_inventory
            ),
            **{field: False for field in _FALSE_GATES},
            "contains_raw_owner_chain": False,
            "contains_owner_chain_sha256": False,
            "contains_owner_chain_character_count": False,
            "contains_source_scalar_values": False,
            "network_requests_performed": False,
        },
        "decision_boundary": {
            "status": "guild_progression_helper_owner_reviewed_probe_blocked",
            "guild_progression_route_candidate_observed": True,
            "guild_progression_helper_reference_reviewed": True,
            "guild_progression_helper_owner_inventory_completed": True,
            "guild_progression_helper_owner_reviewed": True,
            "guild_progression_helper_identity_resolved": False,
            "guild_progression_helper_owner_binding_resolved": owner_binding_resolved,
            "guild_progression_request_payload_mapping_resolved": False,
            "guild_progression_request_shape_verified": False,
            "ready_for_guild_progression_helper_owner_relationship_inventory": (
                ready_for_relationship_inventory
            ),
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
        raise ValueError("public helper-owner review contains forbidden fields")
    write_json(receipt_output_path, review)
    return review


__all__ = ["review_guild_progression_helper_owners"]
