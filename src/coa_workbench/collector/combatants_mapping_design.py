from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

_DESIGN_SCHEMA_VERSION = 1
_SELECTION_KIND = "observed_combatants_info_field_selection"
_DESIGN_KIND = "observed_combatants_info_mapping_design"
_ENDPOINT_KIND = "combatants_info"
_ROUTE_TEMPLATE = "/api/reports/{template}/encounters/{template}/combatants-info"
_PAYLOAD_HASH = "45672e0f0ff9eb461c575bdd38385795daa6326378bc3f8ad51474276140dc14"
_SCHEMA_FINGERPRINT = "41d6d15422c668f83d2ccae1ec0ff2969671861f9e43b21cb371578961c5f8ff"
_SOURCE_CODE = "coa_ascension_logs"
_OUTER_ACTOR_SCOPE = "/combatants/*"
_OUTER_ACTOR_PATH = "/combatants/*/character_id"

_EXPECTED_GROUPS: dict[str, dict[str, Any]] = {
    "actor_identity": {
        "selected_field_count": 7,
        "mapping_strategy": "actor_enrichment_candidate",
        "actor_expression": "@ancestor[1]/character_id",
    },
    "guild_membership": {
        "selected_field_count": 3,
        "mapping_strategy": "actor_enrichment_candidate",
        "actor_expression": "@ancestor[1]/character_id",
    },
    "instance_context": {
        "selected_field_count": 8,
        "mapping_strategy": "deduplicated_context_observation_candidate",
        "actor_expression": "@ancestor[1]/character_id",
    },
    "specialization_summary": {
        "selected_field_count": 4,
        "mapping_strategy": "actor_enrichment_candidate",
        "actor_expression": "@ancestor[1]/character_id",
    },
    "talent_container_summary": {
        "selected_field_count": 3,
        "mapping_strategy": "nested_observation_candidate",
        "actor_expression": "@ancestor[2]/character_id",
    },
    "classless_talent_rank": {
        "selected_field_count": 5,
        "mapping_strategy": "nested_observation_candidate",
        "actor_expression": "@ancestor[3]/character_id",
    },
    "hero_build_entry": {
        "selected_field_count": 2,
        "mapping_strategy": "nested_observation_candidate",
        "actor_expression": "@ancestor[3]/character_id",
    },
    "gear_slot_summary": {
        "selected_field_count": 5,
        "mapping_strategy": "nested_observation_candidate",
        "actor_expression": "@ancestor[2]/character_id",
    },
}

_DESIGN_BLUEPRINTS: tuple[dict[str, Any], ...] = (
    {
        "design_id": "coa-combatants-actor-enrichment-v1",
        "design_type": "actor_enrichment_observation",
        "source_groups": (
            "actor_identity",
            "guild_membership",
            "specialization_summary",
        ),
        "target_entity_type": "actor_enrichment_observation",
        "identity_policy": "existing_stable_actor_id",
        "deduplication_scope": "source_actor_within_exact_payload",
        "route_context_required": False,
        "actor_merge_validation_required": True,
        "record_identity_fields": (),
    },
    {
        "design_id": "coa-combatants-instance-context-v1",
        "design_type": "deduplicated_context_observation",
        "source_groups": ("instance_context",),
        "target_entity_type": "combatants_instance_context_observation",
        "identity_policy": "selected_record_sha256",
        "deduplication_scope": "exact_payload_only",
        "route_context_required": True,
        "actor_merge_validation_required": False,
        "record_identity_fields": (
            "difficulty_index",
            "difficulty_name",
            "instance_type",
            "is_dynamic",
            "map_id",
            "max_players",
            "instance_name",
            "player_difficulty",
        ),
    },
    {
        "design_id": "coa-combatants-talent-container-v1",
        "design_type": "nested_parser_observation",
        "source_groups": ("talent_container_summary",),
        "target_entity_type": "combatants_talent_container_observation",
        "identity_policy": "raw_match_path_and_selected_record_sha256",
        "deduplication_scope": "none_beyond_exact_raw_match",
        "route_context_required": True,
        "actor_merge_validation_required": False,
        "record_identity_fields": (),
    },
    {
        "design_id": "coa-combatants-classless-talent-rank-v1",
        "design_type": "nested_parser_observation",
        "source_groups": ("classless_talent_rank",),
        "target_entity_type": "combatants_classless_talent_rank_observation",
        "identity_policy": "raw_match_path_and_selected_record_sha256",
        "deduplication_scope": "none_beyond_exact_raw_match",
        "route_context_required": True,
        "actor_merge_validation_required": False,
        "record_identity_fields": (),
    },
    {
        "design_id": "coa-combatants-hero-build-entry-v1",
        "design_type": "nested_parser_observation",
        "source_groups": ("hero_build_entry",),
        "target_entity_type": "combatants_hero_build_entry_observation",
        "identity_policy": "raw_match_path_and_selected_record_sha256",
        "deduplication_scope": "none_beyond_exact_raw_match",
        "route_context_required": True,
        "actor_merge_validation_required": False,
        "record_identity_fields": (),
    },
    {
        "design_id": "coa-combatants-gear-slot-v1",
        "design_type": "nested_parser_observation",
        "source_groups": ("gear_slot_summary",),
        "target_entity_type": "combatants_gear_slot_observation",
        "identity_policy": "raw_match_path_and_selected_record_sha256",
        "deduplication_scope": "none_beyond_exact_raw_match",
        "route_context_required": True,
        "actor_merge_validation_required": False,
        "record_identity_fields": (),
    },
)


def _generated_at() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _load_object(path: Path, *, label: str) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{label} must contain a JSON object")
    return payload


def _required_object(value: object, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be an object")
    return value


def _required_list(value: object, field_name: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be an array")
    return value


def _required_string(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field_name} must be a non-empty string")
    return value


def _validate_selection(selection: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    if selection.get("schema_version") != 1 or selection.get("selection_kind") != _SELECTION_KIND:
        raise ValueError("unsupported combatants-info field selection")

    endpoint = _required_object(selection.get("endpoint"), "selection.endpoint")
    expected_endpoint = {
        "endpoint_kind": _ENDPOINT_KIND,
        "route_template": _ROUTE_TEMPLATE,
        "payload_hash": _PAYLOAD_HASH,
        "schema_fingerprint": _SCHEMA_FINGERPRINT,
        "transport_provenance_type": "upstream_derived",
        "content_provenance_status": "candidate_companion_addon_enrichment",
    }
    for field_name, expected in expected_endpoint.items():
        if endpoint.get(field_name) != expected:
            raise ValueError(f"combatants-info field selection endpoint mismatch: {field_name}")

    summary = _required_object(selection.get("summary"), "selection.summary")
    expected_summary = {
        "selection_group_count": 8,
        "selected_scope_count": 8,
        "selected_field_contract_count": 37,
        "linkage_contract_count": 8,
        "unique_linkage_field_count": 1,
        "deferred_field_count": 19,
        "missing_optional_scope_count": 2,
        "generic_actor_enrichment_group_count": 3,
        "specialized_observation_group_count": 5,
        "contains_source_scalar_values": False,
        "all_source_reviews_consistent": True,
        "candidate_mapping_files_ready": False,
        "ready_for_manual_mapping_design": True,
        "combatants_info_enrichment_available": False,
        "normalization_allowed": False,
        "planner_scoring_allowed": False,
    }
    for field_name, expected in expected_summary.items():
        if summary.get(field_name) != expected:
            raise ValueError(f"combatants-info field selection summary mismatch: {field_name}")

    boundary = _required_object(selection.get("decision_boundary"), "selection.decision_boundary")
    expected_boundary = {
        "status": "candidate",
        "automatic_mapping_creation": False,
        "automatic_promotion": False,
        "can_promote": False,
        "actor_merge_verified": False,
        "companion_addon_provenance_verified": False,
        "nested_collection_semantics_verified": False,
        "combatants_info_enrichment_available": False,
        "normalization_allowed": False,
        "mechanic_semantics_verified": False,
        "planner_scoring_allowed": False,
        "ready_for_manual_mapping_design": True,
    }
    for field_name, expected in expected_boundary.items():
        if boundary.get(field_name) != expected:
            raise ValueError(f"combatants-info field selection boundary mismatch: {field_name}")

    linkage = _required_object(selection.get("outer_actor_linkage"), "outer_actor_linkage")
    expected_linkage = {
        "review_scope": _OUTER_ACTOR_SCOPE,
        "review_path": _OUTER_ACTOR_PATH,
        "types": ["integer"],
        "nullable": False,
        "observed_on_all_scope_occurrences": True,
        "occurrence_count": 11,
        "status": "exact_path_confirmed_candidate_merge",
    }
    for field_name, expected in expected_linkage.items():
        if linkage.get(field_name) != expected:
            raise ValueError(f"combatants-info actor linkage mismatch: {field_name}")

    groups: dict[str, dict[str, Any]] = {}
    contract_count = 0
    for raw_group in _required_list(selection.get("selection_groups"), "selection_groups"):
        group = _required_object(raw_group, "selection_groups[]")
        group_id = _required_string(group.get("group_id"), "selection group id")
        if group_id in groups:
            raise ValueError(f"duplicate combatants-info selection group: {group_id}")
        expected_group = _EXPECTED_GROUPS.get(group_id)
        if expected_group is None:
            raise ValueError(f"unexpected combatants-info selection group: {group_id}")
        for field_name, expected in (
            ("selected_field_count", expected_group["selected_field_count"]),
            ("mapping_strategy", expected_group["mapping_strategy"]),
            ("mapping_status", "not_created"),
        ):
            if group.get(field_name) != expected:
                raise ValueError(f"combatants-info selection group mismatch: {group_id} {field_name}")
        source_linkage = _required_object(group.get("source_actor_linkage"), "source_actor_linkage")
        if source_linkage.get("review_scope") != _OUTER_ACTOR_SCOPE:
            raise ValueError(f"combatants-info group actor scope mismatch: {group_id}")
        if source_linkage.get("review_path") != _OUTER_ACTOR_PATH:
            raise ValueError(f"combatants-info group actor path mismatch: {group_id}")
        if source_linkage.get("expression") != expected_group["actor_expression"]:
            raise ValueError(f"combatants-info group actor expression mismatch: {group_id}")
        if source_linkage.get("stable_actor_strategy") != "reuse_existing_source_actor_id":
            raise ValueError(f"combatants-info group stable actor strategy mismatch: {group_id}")
        if source_linkage.get("status") != "exact_path_confirmed_candidate_merge":
            raise ValueError(f"combatants-info group actor linkage status mismatch: {group_id}")

        contracts = _required_list(group.get("field_contracts"), "field_contracts")
        if len(contracts) != expected_group["selected_field_count"]:
            raise ValueError(f"combatants-info group contract count mismatch: {group_id}")
        output_fields: set[str] = set()
        for raw_contract in contracts:
            contract = _required_object(raw_contract, "field_contracts[]")
            output_field = _required_string(contract.get("output_field"), "output_field")
            if output_field in output_fields:
                raise ValueError(f"duplicate combatants-info output field: {group_id} {output_field}")
            output_fields.add(output_field)
            _required_string(contract.get("source_path"), "source_path")
            if contract.get("semantic_status") != "reviewed_parser_candidate":
                raise ValueError(f"combatants-info field semantic status mismatch: {group_id}")
            if contract.get("nullable") is not False:
                raise ValueError(f"combatants-info selected field cannot be nullable: {group_id}")
            if not isinstance(contract.get("required"), bool):
                raise ValueError(f"combatants-info selected field required flag invalid: {group_id}")
            types = _required_list(contract.get("types"), "field contract types")
            if not types or any(not isinstance(item, str) or not item for item in types):
                raise ValueError(f"combatants-info selected field types invalid: {group_id}")
            contract_count += 1
        groups[group_id] = group

    if set(groups) != set(_EXPECTED_GROUPS):
        raise ValueError("combatants-info selection group set mismatch")
    if contract_count != 37:
        raise ValueError("combatants-info selection contract total mismatch")

    deferred = _required_list(selection.get("deferred_fields"), "deferred_fields")
    if len(deferred) != 19:
        raise ValueError("combatants-info deferred field count mismatch")
    if any(_required_object(row, "deferred_fields[]").get("decision") != "deferred" for row in deferred):
        raise ValueError("combatants-info deferred field decision mismatch")

    missing = _required_list(selection.get("missing_optional_scopes"), "missing_optional_scopes")
    if len(missing) != 2:
        raise ValueError("combatants-info missing optional scope count mismatch")
    if any(
        _required_object(row, "missing_optional_scopes[]").get("decision") != "deferred"
        for row in missing
    ):
        raise ValueError("combatants-info missing optional scope decision mismatch")
    return groups


def _copy_contract(contract: Mapping[str, Any], *, group_id: str) -> dict[str, Any]:
    return {
        "source_group": group_id,
        "source_path": contract["source_path"],
        "output_field": contract["output_field"],
        "types": list(contract["types"]),
        "nullable": False,
        "required": contract["required"],
        "occurrence_count": contract.get("occurrence_count"),
        "parser_status": "reviewed_candidate",
        "semantic_status": "unverified",
    }


def _source_match_count(groups: list[Mapping[str, Any]]) -> int:
    counts = [
        int(contract.get("occurrence_count") or 0)
        for group in groups
        for contract in _required_list(group.get("field_contracts"), "field_contracts")
        if contract.get("required") is True
    ]
    if not counts:
        raise ValueError("mapping design has no required source contracts")
    return max(counts)


def _build_design(blueprint: Mapping[str, Any], groups: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    source_group_ids = list(blueprint["source_groups"])
    source_groups = [groups[group_id] for group_id in source_group_ids]
    field_contracts = [
        _copy_contract(contract, group_id=group_id)
        for group_id, group in zip(source_group_ids, source_groups, strict=True)
        for contract in _required_list(group.get("field_contracts"), "field_contracts")
    ]
    output_fields = [contract["output_field"] for contract in field_contracts]
    if len(output_fields) != len(set(output_fields)):
        raise ValueError(f"mapping design output field collision: {blueprint['design_id']}")

    return {
        "design_id": blueprint["design_id"],
        "design_version": "1",
        "design_type": blueprint["design_type"],
        "implementation_status": "design_only",
        "candidate_mapping_file": None,
        "source_code": _SOURCE_CODE,
        "source_groups": source_group_ids,
        "source_scopes": [group["scope"] for group in source_groups],
        "source_actor_linkage": {
            "review_scope": _OUTER_ACTOR_SCOPE,
            "review_path": _OUTER_ACTOR_PATH,
            "stable_actor_strategy": "reuse_existing_source_actor_id",
            "stable_actor_id_formula": "stable_id('actor', source_code, source_actor_id)",
            "expected_link_count": 11,
        },
        "target": {
            "storage_table": "canonical_entity_observation",
            "entity_type": blueprint["target_entity_type"],
            "trust_status": "observed_candidate",
            "core_entity_mutation_allowed": False,
        },
        "identity_contract": {
            "identity_policy": blueprint["identity_policy"],
            "record_identity_fields": list(blueprint["record_identity_fields"]),
            "raw_match_path_required": blueprint["identity_policy"]
            == "raw_match_path_and_selected_record_sha256",
            "selected_record_sha256_required": True,
            "deduplication_scope": blueprint["deduplication_scope"],
            "semantic_uniqueness_claimed": False,
        },
        "route_context_contract": {
            "required": blueprint["route_context_required"],
            "source": "capture_observation_route_context",
            "report_and_encounter_linkage_verified": False,
        },
        "merge_contract": {
            "actor_merge_validation_required": blueprint["actor_merge_validation_required"],
            "existing_non_null_conflict_policy": "require_exact_match",
            "null_fill_policy": "candidate_only",
            "automatic_core_projection": False,
        },
        "field_contracts": field_contracts,
        "selected_field_count": len(field_contracts),
        "expected_source_match_count": _source_match_count(source_groups),
        "generic_normalizer_compatible": False,
        "dedicated_extractor_required": True,
        "exact_raw_validation_required": True,
        "content_provenance_status": "candidate_companion_addon_enrichment",
        "promotion_allowed": False,
        "normalization_allowed": False,
    }


def design_observed_combatants_info_mappings(selection_path: Path) -> dict[str, Any]:
    """Create a scalar-free storage-aware design packet without creating mappings."""
    selection = _load_object(selection_path, label="combatants-info field selection")
    groups = _validate_selection(selection)
    designs = [_build_design(blueprint, groups) for blueprint in _DESIGN_BLUEPRINTS]

    selected_field_count = sum(design["selected_field_count"] for design in designs)
    if selected_field_count != 37:
        raise ValueError("combatants-info mapping design field total mismatch")

    return {
        "schema_version": _DESIGN_SCHEMA_VERSION,
        "design_kind": _DESIGN_KIND,
        "generated_at": _generated_at(),
        "source_selection_name": selection_path.name,
        "source_persistence_run_id": selection.get("source_persistence_run_id"),
        "endpoint": {
            "endpoint_kind": _ENDPOINT_KIND,
            "route_template": _ROUTE_TEMPLATE,
            "payload_hash": _PAYLOAD_HASH,
            "schema_fingerprint": _SCHEMA_FINGERPRINT,
            "transport_provenance_type": "upstream_derived",
            "content_provenance_status": "candidate_companion_addon_enrichment",
        },
        "mapping_designs": designs,
        "deferred_fields": selection["deferred_fields"],
        "missing_optional_scopes": selection["missing_optional_scopes"],
        "decision_boundary": {
            "status": "mapping_design",
            "automatic_implementation": False,
            "candidate_mapping_files_ready": False,
            "generic_normalizer_extension_allowed": False,
            "dedicated_extractor_required": True,
            "exact_raw_validation_required": True,
            "actor_merge_validation_required": True,
            "route_context_validation_required": True,
            "companion_addon_provenance_verified": False,
            "nested_collection_semantics_verified": False,
            "can_promote": False,
            "combatants_info_enrichment_available": False,
            "normalization_allowed": False,
            "mechanic_semantics_verified": False,
            "planner_scoring_allowed": False,
            "ready_for_candidate_extractor_implementation": True,
        },
        "summary": {
            "mapping_design_count": len(designs),
            "source_group_count": len(groups),
            "selected_field_contract_count": selected_field_count,
            "actor_enrichment_design_count": sum(
                design["design_type"] == "actor_enrichment_observation" for design in designs
            ),
            "context_observation_design_count": sum(
                design["design_type"] == "deduplicated_context_observation" for design in designs
            ),
            "nested_observation_design_count": sum(
                design["design_type"] == "nested_parser_observation" for design in designs
            ),
            "immutable_observation_design_count": len(designs),
            "dedicated_extractor_design_count": sum(
                design["dedicated_extractor_required"] is True for design in designs
            ),
            "generic_normalizer_compatible_design_count": sum(
                design["generic_normalizer_compatible"] is True for design in designs
            ),
            "expected_outer_actor_link_count": 11,
            "deferred_field_count": len(selection["deferred_fields"]),
            "missing_optional_scope_count": len(selection["missing_optional_scopes"]),
            "contains_source_scalar_values": False,
            "candidate_mapping_files_ready": False,
            "ready_for_candidate_extractor_implementation": True,
            "combatants_info_enrichment_available": False,
            "normalization_allowed": False,
            "planner_scoring_allowed": False,
        },
    }
