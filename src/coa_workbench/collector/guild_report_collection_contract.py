from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

_CONTRACT_VERSION = "guild-report-collection-contract-v1"
_MAPPING_ID = "coa-public-report-discovery-v1"
_MAPPING_ROUTE = "/api/reports/public"
_MAPPING_FINGERPRINT = "4f47885820e6931cd76db538cabd68405b4969778c1bede9dee53a7f1e005ed4"
_MAPPING_PAYLOAD_HASH = "2203e52709fad4fbc8d5235bc3699abeec6b85cf1e13b9df3e24091ddf8775c2"
_PERSISTENCE_KIND = "observed_combatants_info_immutable_observation_persistence"
_PERSISTENCE_VERSION = "combatants-observation-persistence-v1"
_COMBATANTS_PAYLOAD_HASH = "45672e0f0ff9eb461c575bdd38385795daa6326378bc3f8ad51474276140dc14"
_COMBATANTS_FINGERPRINT = "41d6d15422c668f83d2ccae1ec0ff2969671861f9e43b21cb371578961c5f8ff"
_SAFE_DISCOVERY_FIELDS = (
    "source_report_id",
    "title",
    "created_at",
    "start_time",
    "end_time",
    "visibility",
    "uploader_username",
)
_REQUIRED_DEFERRED_SCOPES = {
    "/pagination",
    "/reports/*/guild_id",
    "/reports/*/guild_name",
    "/reports/*/highest_difficulty",
    "/reports/*/locations",
}


def _generated_at() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _load_object(path: Path, label: str) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{label} must contain a JSON object")
    return payload


def _required_object(value: object, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"guild report collection contract field {field_name} must be an object")
    return value


def _required_list(value: object, field_name: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"guild report collection contract field {field_name} must be an array")
    return value


def _required_string(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(
            f"guild report collection contract field {field_name} must be a non-empty string"
        )
    return value.strip()


def _validate_mapping(mapping: Mapping[str, Any]) -> None:
    expected = {
        "mapping_schema_version": 1,
        "mapping_id": _MAPPING_ID,
        "source_code": "coa_ascension_logs",
        "mapping_version": "1",
        "status": "verified",
        "route_template": _MAPPING_ROUTE,
        "schema_fingerprint": _MAPPING_FINGERPRINT,
        "reviewed_payload_hash": _MAPPING_PAYLOAD_HASH,
        "provenance_type": "upstream_derived",
    }
    for field_name, expected_value in expected.items():
        if mapping.get(field_name) != expected_value:
            raise ValueError(f"public report discovery mapping mismatch: {field_name}")

    collection = _required_object(mapping.get("collection"), "mapping.collection")
    if collection.get("path") != "/reports/*" or collection.get("observed_occurrences") != 5:
        raise ValueError("public report discovery collection contract changed")
    fields = _required_object(collection.get("fields"), "mapping.collection.fields")
    if set(fields) != set(_SAFE_DISCOVERY_FIELDS):
        raise ValueError("public report discovery selected field set changed")
    for field_name in _SAFE_DISCOVERY_FIELDS:
        contract = _required_object(fields.get(field_name), f"mapping.collection.fields.{field_name}")
        if contract.get("nullable") is not False or contract.get("required") is not True:
            raise ValueError(f"public report discovery field contract changed: {field_name}")

    deferred = {
        _required_string(value, "mapping.deferred_scopes[]")
        for value in _required_list(mapping.get("deferred_scopes"), "mapping.deferred_scopes")
    }
    if deferred != _REQUIRED_DEFERRED_SCOPES:
        raise ValueError("public report discovery deferred scope set changed")


def _validate_persistence(receipt: Mapping[str, Any]) -> None:
    expected = {
        "schema_version": 1,
        "persistence_kind": _PERSISTENCE_KIND,
        "persistence_version": _PERSISTENCE_VERSION,
        "source_payload_hash": _COMBATANTS_PAYLOAD_HASH,
        "schema_fingerprint": _COMBATANTS_FINGERPRINT,
    }
    for field_name, expected_value in expected.items():
        if receipt.get(field_name) != expected_value:
            raise ValueError(f"combatants persistence receipt mismatch: {field_name}")

    summary = _required_object(receipt.get("summary"), "persistence.summary")
    expected_summary = {
        "design_count": 6,
        "persisted_observation_count": 1343,
        "actor_build_observation_count": 1339,
        "linked_actor_count": 11,
        "persistence_run_count": 1,
        "all_integrity_checks_passed": True,
        "transaction_committed": True,
        "core_entity_mutation_performed": False,
        "contains_source_scalar_values": False,
        "database_contains_source_scalar_values": True,
        "ready_for_parser_observation_queries": True,
        "ready_for_actor_build_observation_queries": True,
        "combatants_info_enrichment_available": False,
        "mechanic_semantics_verified": False,
        "planner_scoring_allowed": False,
    }
    for field_name, expected_value in expected_summary.items():
        if summary.get(field_name) != expected_value:
            raise ValueError(f"combatants persistence summary mismatch: {field_name}")

    boundary = _required_object(receipt.get("decision_boundary"), "persistence.decision_boundary")
    expected_boundary = {
        "status": "persisted_verified_parser_observations",
        "immutable_observation_persistence_completed": True,
        "core_entity_mutation_performed": False,
        "ready_for_parser_observation_queries": True,
        "ready_for_actor_build_observation_queries": True,
        "combatants_info_enrichment_available": False,
        "mechanic_semantics_verified": False,
        "planner_scoring_allowed": False,
    }
    for field_name, expected_value in expected_boundary.items():
        if boundary.get(field_name) != expected_value:
            raise ValueError(f"combatants persistence boundary mismatch: {field_name}")

    checks = _required_object(receipt.get("integrity_checks"), "persistence.integrity_checks")
    if not checks or any(value is not True for value in checks.values()):
        raise ValueError("combatants persistence integrity checks are incomplete")


def build_guild_report_collection_contract(
    mapping_path: Path,
    persistence_receipt_path: Path,
    *,
    guild_label: str,
    minimum_candidate_characters: int = 30,
    preferred_candidate_characters: int = 40,
    final_roster_size: int = 25,
) -> dict[str, Any]:
    """Build a bounded collection contract without claiming unobserved pagination or guild semantics."""
    prepared_guild_label = _required_string(guild_label, "guild_label")
    if minimum_candidate_characters < final_roster_size:
        raise ValueError("minimum candidate character count cannot be below final roster size")
    if preferred_candidate_characters < minimum_candidate_characters:
        raise ValueError("preferred candidate character count cannot be below minimum")
    if final_roster_size < 1:
        raise ValueError("final roster size must be positive")

    mapping = _load_object(mapping_path, "public report discovery mapping")
    persistence = _load_object(persistence_receipt_path, "combatants persistence receipt")
    _validate_mapping(mapping)
    _validate_persistence(persistence)

    persistence_summary = _required_object(persistence.get("summary"), "persistence.summary")
    return {
        "schema_version": 1,
        "contract_kind": "guild_wide_report_collection_contract",
        "contract_version": _CONTRACT_VERSION,
        "generated_at": _generated_at(),
        "target": {
            "guild_label": prepared_guild_label,
            "guild_identity_status": "operator_named_target_unresolved",
            "verified_source_guild_id": False,
            "verified_source_guild_name": False,
            "minimum_candidate_characters": minimum_candidate_characters,
            "preferred_candidate_characters": preferred_candidate_characters,
            "final_roster_size": final_roster_size,
        },
        "verified_foundation": {
            "report_discovery_mapping_id": _MAPPING_ID,
            "report_discovery_route": _MAPPING_ROUTE,
            "report_discovery_schema_fingerprint": _MAPPING_FINGERPRINT,
            "report_discovery_reviewed_payload_hash": _MAPPING_PAYLOAD_HASH,
            "verified_discovery_fields": list(_SAFE_DISCOVERY_FIELDS),
            "reviewed_discovery_page_count": 1,
            "reviewed_discovery_record_count": 5,
            "combatants_persistence_run_id": _required_string(
                persistence.get("persistence_run_id"), "persistence.persistence_run_id"
            ),
            "persisted_parser_observations": persistence_summary[
                "persisted_observation_count"
            ],
            "persisted_actor_build_observations": persistence_summary[
                "actor_build_observation_count"
            ],
            "exact_payload_linked_actors": persistence_summary["linked_actor_count"],
        },
        "required_evidence_gates": {
            "pagination": {
                "status": "unverified",
                "requirements": [
                    "capture_multiple_consecutive_pages_with_the_same_observed_query_shape",
                    "review_exact_pagination_object_fields_without_guessing_names_or_meanings",
                    "prove_a_deterministic_termination_condition",
                    "verify_cross_page_source_report_id_deduplication",
                    "verify_limit_behavior_before_raising_the_current_limit_of_5",
                ],
            },
            "guild_identity": {
                "status": "unresolved",
                "requirements": [
                    "observe_a_non_null_guild_identifier_or_an_independent_guild_identity_route",
                    "bind_the_observed_source_identity_to_the_operator_label",
                    "reject_title_uploader_and_nickname_heuristics_as_guild_identity",
                ],
            },
            "cross_report_character_identity": {
                "status": "single_payload_only",
                "requirements": [
                    "verify_stable_source_actor_or_character_identifiers_across_reports",
                    "record_aliases_without_using_nickname_as_the_primary_identity",
                    "detect_collisions_splits_and_renames_before_aggregation",
                ],
            },
            "performance_and_benchmark": {
                "status": "not_started",
                "requirements": [
                    "collect_versioned_encounter_performance_observations",
                    "define_comparable_boss_difficulty_role_and_time_cohorts",
                    "build_global_distributions_before_assigning_player_scores",
                    "separate_player_strength_consistency_and_raid_composition_utility",
                ],
            },
        },
        "collection_phases": [
            {
                "phase": 1,
                "code": "pagination_evidence",
                "status": "ready_for_bounded_capture",
            },
            {"phase": 2, "code": "guild_identity_binding", "status": "blocked"},
            {"phase": 3, "code": "guild_report_manifest", "status": "blocked"},
            {"phase": 4, "code": "per_report_evidence_capture", "status": "blocked"},
            {"phase": 5, "code": "multi_report_character_graph", "status": "blocked"},
            {"phase": 6, "code": "performance_and_global_benchmark", "status": "blocked"},
            {"phase": 7, "code": "bis25_roster_optimization", "status": "blocked"},
        ],
        "decision_boundary": {
            "status": "collection_contract_only",
            "automatic_network_collection": False,
            "ready_for_bounded_pagination_capture": True,
            "ready_for_full_guild_crawl": False,
            "ready_for_guild_filtering": False,
            "ready_for_multi_report_character_graph": False,
            "ready_for_performance_model": False,
            "ready_for_global_benchmark": False,
            "ready_for_bis25_scoring": False,
            "planner_scoring_allowed": False,
            "contains_source_scalar_values": False,
        },
        "summary": {
            "collection_phase_count": 7,
            "open_phase_count": 1,
            "blocked_phase_count": 6,
            "verified_discovery_field_count": len(_SAFE_DISCOVERY_FIELDS),
            "deferred_discovery_scope_count": len(_REQUIRED_DEFERRED_SCOPES),
            "persisted_parser_observation_count": persistence_summary[
                "persisted_observation_count"
            ],
            "persisted_actor_build_observation_count": persistence_summary[
                "actor_build_observation_count"
            ],
            "current_exact_payload_actor_count": persistence_summary["linked_actor_count"],
            "minimum_candidate_character_count": minimum_candidate_characters,
            "preferred_candidate_character_count": preferred_candidate_characters,
            "final_roster_size": final_roster_size,
            "ready_for_bounded_pagination_capture": True,
            "ready_for_full_guild_crawl": False,
            "ready_for_bis25_scoring": False,
            "contains_source_scalar_values": False,
        },
    }
