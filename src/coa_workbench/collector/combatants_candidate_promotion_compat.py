from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Mapping

from . import combatants_candidate_promotion as _base


def _align_context_actor_links(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Validate independently sorted context link arrays and align them for v1 validation."""
    prepared = deepcopy(dict(payload))
    observations = _base._required_object(prepared.get("observations"), "observations")

    actor_design_id = "coa-combatants-actor-enrichment-v1"
    actor_rows = _base._required_list(observations.get(actor_design_id), actor_design_id)
    actor_map: dict[str, str] = {}
    for raw_row in actor_rows:
        row = _base._required_object(raw_row, f"{actor_design_id}[]")
        source_actor_id = _base._required_string(row.get("source_actor_id"), "source_actor_id")
        actor_id = _base._required_sha256(row.get("actor_id"), "actor_id")
        if source_actor_id in actor_map or actor_id in actor_map.values():
            raise ValueError("combatants actor enrichment linkage is duplicated")
        actor_map[source_actor_id] = actor_id

    context_design_id = "coa-combatants-instance-context-v1"
    context_rows = _base._required_list(observations.get(context_design_id), context_design_id)
    for raw_row in context_rows:
        row = _base._required_object(raw_row, f"{context_design_id}[]")
        actor_ids = [
            _base._required_sha256(value, "linked_actor_id")
            for value in _base._required_list(row.get("linked_actor_ids"), "linked_actor_ids")
        ]
        source_actor_ids = [
            _base._required_string(value, "linked_source_actor_id")
            for value in _base._required_list(
                row.get("linked_source_actor_ids"), "linked_source_actor_ids"
            )
        ]
        source_paths = [
            _base._required_string(value, "source_raw_match_path")
            for value in _base._required_list(
                row.get("source_raw_match_paths"), "source_raw_match_paths"
            )
        ]
        if not actor_ids or len(actor_ids) != len(source_actor_ids) or len(actor_ids) != len(source_paths):
            raise ValueError("combatants context linkage arrays are inconsistent")
        if len(set(actor_ids)) != len(actor_ids):
            raise ValueError("combatants context actor linkage array contains duplicates")
        if len(set(source_actor_ids)) != len(source_actor_ids):
            raise ValueError("combatants context source linkage array contains duplicates")
        if len(set(source_paths)) != len(source_paths):
            raise ValueError("combatants context raw path array contains duplicates")
        if any(source_actor_id not in actor_map for source_actor_id in source_actor_ids):
            raise ValueError("combatants context references an unknown source actor")

        expected_actor_ids = [actor_map[source_actor_id] for source_actor_id in source_actor_ids]
        if set(actor_ids) != set(expected_actor_ids):
            raise ValueError("combatants context actor linkage mismatch")

        # The extractor sorts actor IDs, source actor IDs and paths independently for deterministic
        # serialization. The v1 validator expected positional pairing, so align only the copied
        # payload after proving that both actor sets are exactly equivalent.
        row["linked_actor_ids"] = expected_actor_ids

    return prepared


def promote_observed_combatants_info_candidates(
    extraction_receipt_path: Path,
    private_extraction_path: Path,
    *,
    reviewed_by: str,
    reviewed_at: str,
) -> dict[str, Any]:
    """Promote the exact private candidate batch with order-independent context validation."""
    prepared_reviewer = _base._required_string(reviewed_by, "reviewed_by")
    prepared_reviewed_at = _base._reviewed_at(reviewed_at)

    private_body = private_extraction_path.read_bytes()
    private_sha256 = hashlib.sha256(private_body).hexdigest()
    receipt = _base._load_object(extraction_receipt_path, "combatants candidate extraction receipt")
    receipt_rows = _base._validate_extraction_receipt(
        receipt,
        private_path=private_extraction_path,
        private_sha256=private_sha256,
    )
    private_payload = json.loads(private_body)
    if not isinstance(private_payload, dict):
        raise ValueError("private combatants extraction must contain a JSON object")

    promoted_rows, aggregate = _base._validate_private_batch(
        _align_context_actor_links(private_payload)
    )
    for row in promoted_rows:
        source = receipt_rows[row["design_id"]]
        if row["source_match_count"] != source["source_match_count"]:
            raise ValueError(f"combatants promoted source count mismatch: {row['design_id']}")
        if row["output_observation_count"] != source["output_observation_count"]:
            raise ValueError(f"combatants promoted output count mismatch: {row['design_id']}")

    checks = {
        "candidate_receipt_verified": True,
        "private_extraction_sha256_verified": True,
        "private_extraction_schema_verified": True,
        "exact_payload_binding_verified": True,
        "exact_route_context_consistent": True,
        "all_design_sets_verified": True,
        "all_output_counts_verified": True,
        "all_observation_ids_verified": True,
        "all_selected_record_hashes_verified": True,
        "all_selected_field_counts_verified": True,
        "all_actor_links_verified": True,
        "all_actor_sets_consistent": True,
        "all_nested_raw_paths_unique_per_design": True,
        "instance_context_deduplication_verified": True,
        "core_entity_mutation_not_allowed": True,
    }

    return {
        "schema_version": _base._PROMOTION_SCHEMA_VERSION,
        "promotion_kind": "observed_combatants_info_manual_candidate_promotion",
        "promotion_version": _base._PROMOTION_VERSION,
        "generated_at": _base._generated_at(),
        "source_extraction_receipt_name": extraction_receipt_path.name,
        "source_private_extraction_name": private_extraction_path.name,
        "source_private_extraction_sha256": private_sha256,
        "source_payload_hash": _base._PAYLOAD_HASH,
        "schema_fingerprint": _base._SCHEMA_FINGERPRINT,
        "reviewed_by": prepared_reviewer,
        "reviewed_at": prepared_reviewed_at,
        "verification_scope": (
            "exact_private_batch_schema_hash_counts_actor_linkage_route_context_and_record_hashes_only"
        ),
        "promoted_designs": promoted_rows,
        "integrity_checks": checks,
        "decision_boundary": {
            "status": "verified_parser_observation_batch",
            "automatic_promotion": False,
            "manual_promotion_completed": True,
            "automatic_persistence": False,
            "ready_for_immutable_observation_persistence": True,
            "core_entity_mutation_allowed": False,
            "actor_linkage_verified_for_exact_payload": True,
            "route_context_verified_for_exact_payload": True,
            "companion_addon_provenance_verified": False,
            "nested_collection_semantics_verified": False,
            "semantic_uniqueness_verified": False,
            "mechanic_semantics_verified": False,
            "combatants_info_enrichment_available": False,
            "planner_scoring_allowed": False,
            "private_extraction_contains_source_scalar_values": True,
        },
        "summary": {
            **aggregate,
            "integrity_check_count": len(checks),
            "all_integrity_checks_passed": True,
            "contains_source_scalar_values": False,
            "private_extraction_contains_source_scalar_values": True,
            "manual_promotion_completed": True,
            "automatic_persistence": False,
            "ready_for_immutable_observation_persistence": True,
            "core_entity_mutation_allowed": False,
            "companion_addon_provenance_verified": False,
            "nested_collection_semantics_verified": False,
            "mechanic_semantics_verified": False,
            "combatants_info_enrichment_available": False,
            "planner_scoring_allowed": False,
        },
    }
