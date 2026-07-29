from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .report_slice_scope_review import (
    _endpoint_index,
    _required_list,
    _required_object,
    _required_string,
    _scope_review,
    _shape_index,
)

_COMBATANTS_REVIEW_SCHEMA_VERSION = 1
_MAPPING_REVIEW_KIND = "observed_report_slice_mapping_review"
_PERSISTENCE_KIND = "observed_report_slice_selected_parser_persistence"
_COMBATANTS_ENDPOINT_KIND = "combatants_info"
_COMBATANTS_ROUTE = "/api/reports/{template}/encounters/{template}/combatants-info"
_COMBATANTS_PAYLOAD_HASH = "45672e0f0ff9eb461c575bdd38385795daa6326378bc3f8ad51474276140dc14"
_COMBATANTS_SCHEMA_FINGERPRINT = (
    "41d6d15422c668f83d2ccae1ec0ff2969671861f9e43b21cb371578961c5f8ff"
)
_EXPECTED_PERSISTED_COUNTS = {
    "reports": 1,
    "encounters": 14,
    "actors": 31,
    "participants": 31,
    "aura_events": 0,
    "rejects": 0,
}
_EXPECTED_PERSISTED_MAPPING_IDS = {
    "coa-encounter-detail-v1",
    "coa-report-detail-v1",
}
_REQUIRED_SCOPE_CANDIDATES: tuple[tuple[str, str], ...] = (
    (
        "/combatants/*/ci_resolved/player",
        "resolved_player_identity_candidate",
    ),
    (
        "/combatants/*/ci_resolved/guild",
        "resolved_guild_membership_candidate",
    ),
    (
        "/combatants/*/ci_resolved/instance",
        "resolved_instance_context_candidate",
    ),
    (
        "/combatants/*/ci_resolved/specialization",
        "resolved_specialization_candidate",
    ),
)
_OPTIONAL_SCOPE_CANDIDATES: tuple[tuple[str, str], ...] = (
    (
        "/combatants/*/ci_resolved/specialization/talents",
        "resolved_talent_container_candidate",
    ),
    (
        "/combatants/*/ci_resolved/specialization/talents/trees/*",
        "resolved_talent_tree_candidate",
    ),
    (
        "/combatants/*/ci_resolved/specialization/resolved_ca_talent_ranks/*",
        "resolved_classless_talent_rank_candidate",
    ),
    (
        "/combatants/*/ci_resolved/specialization/hero_build/*",
        "resolved_hero_build_entry_candidate",
    ),
    (
        "/combatants/*/ci_resolved/specialization/unlocked_specs/*",
        "resolved_unlocked_specialization_candidate",
    ),
    (
        "/combatants/*/ci_resolved/specialization/vanilla_talents",
        "resolved_vanilla_talent_container_candidate",
    ),
    (
        "/combatants/*/ci_resolved/gear/*",
        "resolved_gear_slot_candidate",
    ),
    (
        "/combatants/*/ci_resolved/mystic_enchants/*",
        "resolved_mystic_enchant_candidate",
    ),
)


def _generated_at() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _load_object(path: Path, *, label: str) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{label} must contain a JSON object")
    return payload


def _validate_persistence_receipt(receipt: dict[str, Any]) -> dict[str, Any]:
    if receipt.get("schema_version") != 1:
        raise ValueError("unsupported selected parser persistence schema version")
    if receipt.get("persistence_kind") != _PERSISTENCE_KIND:
        raise ValueError("unexpected selected parser persistence kind")
    if receipt.get("persistence_version") != "selected-parser-persistence-v1":
        raise ValueError("unexpected selected parser persistence version")

    summary = _required_object(receipt.get("summary"), "persistence.summary")
    expected_summary = {
        "source_batch_count": 2,
        "mapping_count": 2,
        "persistence_run_count": 1,
        "canonical_entity_observation_count": 77,
        "all_mapping_hashes_verified": True,
        "all_raw_objects_verified": True,
        "all_integrity_checks_passed": True,
        "transaction_committed": True,
        "contains_source_scalar_values": False,
        "database_contains_source_scalar_values": True,
        "ready_for_parser_observation_queries": True,
        "ready_for_combatants_info_mapping_review": True,
        "mechanic_semantics_verified": False,
        "full_report_slice_complete": False,
        "planner_scoring_allowed": False,
    }
    for field_name, expected in expected_summary.items():
        if summary.get(field_name) != expected:
            raise ValueError(f"selected parser persistence summary mismatch: {field_name}")
    if summary.get("persisted_counts") != _EXPECTED_PERSISTED_COUNTS:
        raise ValueError("selected parser persistence counts mismatch")

    boundary = _required_object(receipt.get("decision_boundary"), "persistence.decision_boundary")
    expected_boundary = {
        "status": "persisted_parser_slice",
        "selected_parser_persistence_completed": True,
        "ready_for_parser_observation_queries": True,
        "ready_for_combatants_info_mapping_review": True,
        "automatic_commit": False,
        "database_contains_source_scalar_values": True,
        "mechanic_semantics_verified": False,
        "combatants_info_enrichment_available": False,
        "aura_reconstruction_available": False,
        "full_report_slice_complete": False,
        "planner_scoring_allowed": False,
    }
    for field_name, expected in expected_boundary.items():
        if boundary.get(field_name) != expected:
            raise ValueError(f"selected parser persistence boundary mismatch: {field_name}")

    checks = _required_object(receipt.get("integrity_checks"), "persistence.integrity_checks")
    if not checks or any(value is not True for value in checks.values()):
        raise ValueError("selected parser persistence integrity checks are incomplete")

    mapping_ids: set[str] = set()
    for raw_row in _required_list(receipt.get("source_batches"), "persistence.source_batches"):
        row = _required_object(raw_row, "persistence.source_batches[]")
        mapping_id = _required_string(row.get("mapping_id"), "source batch mapping_id")
        if mapping_id in mapping_ids:
            raise ValueError(f"duplicate persisted source mapping: {mapping_id}")
        if row.get("mapping_hash_verified") is not True:
            raise ValueError(f"persisted mapping hash gate failed: {mapping_id}")
        if row.get("raw_object_verified") is not True:
            raise ValueError(f"persisted raw object gate failed: {mapping_id}")
        mapping_ids.add(mapping_id)
    if mapping_ids != _EXPECTED_PERSISTED_MAPPING_IDS:
        raise ValueError("persisted source mapping set mismatch")
    return summary


def _combatants_endpoint(mapping_review: dict[str, Any]) -> dict[str, Any]:
    if mapping_review.get("schema_version") != 1:
        raise ValueError("unsupported report slice mapping review schema version")
    if mapping_review.get("review_kind") != _MAPPING_REVIEW_KIND:
        raise ValueError("unexpected report slice mapping review kind")

    summary = _required_object(mapping_review.get("summary"), "mapping_review.summary")
    expected_summary = {
        "endpoint_count": 3,
        "raw_archive_count": 3,
        "all_archives_consistent": True,
        "contains_source_scalar_values": False,
        "semantic_verification_required": True,
        "normalization_allowed": False,
        "ready_for_manual_mapping_review": True,
    }
    for field_name, expected in expected_summary.items():
        if summary.get(field_name) != expected:
            raise ValueError(f"report slice mapping review summary mismatch: {field_name}")

    endpoints = _endpoint_index(mapping_review.get("endpoints"), label="mapping_review.endpoints")
    endpoint = endpoints.get(_COMBATANTS_ENDPOINT_KIND)
    if endpoint is None:
        raise ValueError("combatants_info endpoint is missing from mapping review")
    expected_endpoint = {
        "route_template": _COMBATANTS_ROUTE,
        "payload_hash": _COMBATANTS_PAYLOAD_HASH,
        "schema_fingerprint": _COMBATANTS_SCHEMA_FINGERPRINT,
        "top_level_kind": "object",
        "review_status": "candidate",
        "provenance_type": "upstream_derived",
        "scope": "/",
    }
    for field_name, expected in expected_endpoint.items():
        if endpoint.get(field_name) != expected:
            raise ValueError(f"combatants_info endpoint mismatch: {field_name}")
    top_level_keys = endpoint.get("top_level_keys")
    if top_level_keys != ["combatants", "success"]:
        raise ValueError("combatants_info top-level keys mismatch")
    return endpoint


def build_observed_combatants_info_deep_scope_review(
    mapping_review_path: Path,
    persistence_path: Path,
) -> dict[str, Any]:
    """Build a scalar-free deep structural packet for observed combatants-info scopes."""
    mapping_review = _load_object(mapping_review_path, label="report slice mapping review")
    persistence = _load_object(persistence_path, label="selected parser persistence receipt")
    persistence_summary = _validate_persistence_receipt(persistence)
    endpoint = _combatants_endpoint(mapping_review)
    shapes = _shape_index(endpoint.get("field_shapes"), endpoint_kind=_COMBATANTS_ENDPOINT_KIND)

    scopes: list[dict[str, Any]] = []
    missing_optional_scopes: list[dict[str, str]] = []
    total_direct_fields = 0
    for scope, review_label in _REQUIRED_SCOPE_CANDIDATES:
        packet = _scope_review(
            endpoint_kind=_COMBATANTS_ENDPOINT_KIND,
            route_template=_COMBATANTS_ROUTE,
            payload_hash=_COMBATANTS_PAYLOAD_HASH,
            schema_fingerprint=_COMBATANTS_SCHEMA_FINGERPRINT,
            scope=scope,
            review_label=review_label,
            shapes=shapes,
        )
        packet["required_scope"] = True
        total_direct_fields += packet["summary"]["direct_field_count"]
        scopes.append(packet)

    for scope, review_label in _OPTIONAL_SCOPE_CANDIDATES:
        if scope not in shapes:
            missing_optional_scopes.append(
                {
                    "scope": scope,
                    "review_label": review_label,
                    "reason": "scope_not_observed_in_exact_mapping_review",
                }
            )
            continue
        packet = _scope_review(
            endpoint_kind=_COMBATANTS_ENDPOINT_KIND,
            route_template=_COMBATANTS_ROUTE,
            payload_hash=_COMBATANTS_PAYLOAD_HASH,
            schema_fingerprint=_COMBATANTS_SCHEMA_FINGERPRINT,
            scope=scope,
            review_label=review_label,
            shapes=shapes,
        )
        packet["required_scope"] = False
        total_direct_fields += packet["summary"]["direct_field_count"]
        scopes.append(packet)

    required_scope_count = len(_REQUIRED_SCOPE_CANDIDATES)
    optional_scope_candidate_count = len(_OPTIONAL_SCOPE_CANDIDATES)
    optional_scope_present_count = len(scopes) - required_scope_count
    return {
        "schema_version": _COMBATANTS_REVIEW_SCHEMA_VERSION,
        "review_kind": "observed_combatants_info_deep_scope_review",
        "generated_at": _generated_at(),
        "source_mapping_review_name": mapping_review_path.name,
        "source_persistence_name": persistence_path.name,
        "source_persistence_run_id": _required_string(
            persistence.get("persistence_run_id"),
            "persistence_run_id",
        ),
        "endpoint": {
            "endpoint_kind": _COMBATANTS_ENDPOINT_KIND,
            "route_template": _COMBATANTS_ROUTE,
            "payload_hash": _COMBATANTS_PAYLOAD_HASH,
            "schema_fingerprint": _COMBATANTS_SCHEMA_FINGERPRINT,
            "review_status": "candidate",
            "transport_provenance_type": "upstream_derived",
            "content_provenance_status": "candidate_companion_addon_enrichment",
        },
        "scopes": scopes,
        "missing_optional_scopes": missing_optional_scopes,
        "decision_boundary": {
            "status": "candidate",
            "automatic_scope_selection": False,
            "automatic_field_selection": False,
            "automatic_mapping_creation": False,
            "can_promote": False,
            "semantic_verification_required": True,
            "companion_addon_provenance_verified": False,
            "combatants_info_enrichment_available": False,
            "normalization_allowed": False,
            "mechanic_semantics_verified": False,
            "planner_scoring_allowed": False,
        },
        "summary": {
            "endpoint_count": 1,
            "scope_candidate_count": required_scope_count + optional_scope_candidate_count,
            "present_scope_count": len(scopes),
            "required_scope_count": required_scope_count,
            "required_scope_present_count": required_scope_count,
            "optional_scope_candidate_count": optional_scope_candidate_count,
            "optional_scope_present_count": optional_scope_present_count,
            "optional_scope_missing_count": len(missing_optional_scopes),
            "direct_field_count": total_direct_fields,
            "persisted_report_count": persistence_summary["persisted_counts"]["reports"],
            "persisted_encounter_count": persistence_summary["persisted_counts"]["encounters"],
            "persisted_actor_count": persistence_summary["persisted_counts"]["actors"],
            "persisted_participant_count": persistence_summary["persisted_counts"]["participants"],
            "all_archives_consistent": True,
            "selected_parser_persistence_verified": True,
            "contains_source_scalar_values": False,
            "semantic_verification_required": True,
            "ready_for_manual_combatants_field_selection": True,
            "companion_addon_provenance_verified": False,
            "combatants_info_enrichment_available": False,
            "normalization_allowed": False,
            "mechanic_semantics_verified": False,
            "planner_scoring_allowed": False,
        },
    }
