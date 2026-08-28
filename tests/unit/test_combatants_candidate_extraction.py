from __future__ import annotations

from typing import Any

import pytest

from coa_workbench.collector.combatants_candidate_extraction import (
    _validate_design,
    extract_combatants_info_candidate_payload,
)
from coa_workbench.normalizer.canonical import stable_id

_SOURCE_CODE = "coa_ascension_logs"

_GROUPS: dict[str, dict[str, Any]] = {
    "actor_identity": {
        "scope": "/combatants/*/ci_resolved/player",
        "fields": [
            ("class", "class", "string", True),
            ("gender", "gender", "integer", True),
            ("guid", "guid", "string", True),
            ("level", "level", "integer", True),
            ("name", "name", "string", True),
            ("race", "race", "string", True),
            ("realm", "realm", "string", True),
        ],
    },
    "guild_membership": {
        "scope": "/combatants/*/ci_resolved/guild",
        "fields": [
            ("name", "guild_name", "string", True),
            ("rank_index", "guild_rank_index", "integer", True),
            ("rank_name", "guild_rank_name", "string", True),
        ],
    },
    "instance_context": {
        "scope": "/combatants/*/ci_resolved/instance",
        "fields": [
            ("difficulty_index", "difficulty_index", "integer", True),
            ("difficulty_name", "difficulty_name", "string", True),
            ("instance_type", "instance_type", "string", True),
            ("is_dynamic", "is_dynamic", "boolean", True),
            ("map_id", "map_id", "integer", True),
            ("max_players", "max_players", "integer", True),
            ("name", "instance_name", "string", True),
            ("player_difficulty", "player_difficulty", "integer", True),
        ],
    },
    "specialization_summary": {
        "scope": "/combatants/*/ci_resolved/specialization",
        "fields": [
            ("active_spec_idx", "active_spec_idx", "integer", True),
            ("active_spec_name", "active_spec_name", "string", False),
            ("active_spec_role", "active_spec_role", "string", False),
            ("active_spec_slot", "active_spec_slot", "integer", False),
        ],
    },
    "talent_container_summary": {
        "scope": "/combatants/*/ci_resolved/specialization/talents",
        "fields": [
            ("class_label", "class_label", "string", True),
            ("class_slug", "class_slug", "string", True),
            ("tree_order", "tree_order", "array", True),
        ],
    },
    "classless_talent_rank": {
        "scope": "/combatants/*/ci_resolved/specialization/resolved_ca_talent_ranks/*",
        "fields": [
            ("bisbeard_tree", "bisbeard_tree", "string", True),
            ("cao_id", "cao_id", "integer", True),
            ("icon", "icon", "string", True),
            ("name", "name", "string", True),
            ("rank", "rank", "integer", True),
        ],
    },
    "hero_build_entry": {
        "scope": "/combatants/*/ci_resolved/specialization/hero_build/*",
        "fields": [
            ("entry_id", "entry_id", "integer", True),
            ("rank", "rank", "integer", True),
        ],
    },
    "gear_slot_summary": {
        "scope": "/combatants/*/ci_resolved/gear/*",
        "fields": [
            ("enchant", "enchant", "integer", True),
            ("item_id", "item_id", "integer", True),
            ("slot", "slot", "integer", True),
            ("suffix", "suffix", "integer", True),
            ("unique", "unique", "integer", True),
        ],
    },
}

_DESIGN_CONFIG = [
    (
        "coa-combatants-actor-enrichment-v1",
        "actor_enrichment_observation",
        ["actor_identity", "guild_membership", "specialization_summary"],
        "actor_enrichment_observation",
        "existing_stable_actor_id",
        14,
        11,
    ),
    (
        "coa-combatants-instance-context-v1",
        "deduplicated_context_observation",
        ["instance_context"],
        "combatants_instance_context_observation",
        "selected_record_sha256",
        8,
        11,
    ),
    (
        "coa-combatants-talent-container-v1",
        "nested_parser_observation",
        ["talent_container_summary"],
        "combatants_talent_container_observation",
        "raw_match_path_and_selected_record_sha256",
        3,
        11,
    ),
    (
        "coa-combatants-classless-talent-rank-v1",
        "nested_parser_observation",
        ["classless_talent_rank"],
        "combatants_classless_talent_rank_observation",
        "raw_match_path_and_selected_record_sha256",
        5,
        564,
    ),
    (
        "coa-combatants-hero-build-entry-v1",
        "nested_parser_observation",
        ["hero_build_entry"],
        "combatants_hero_build_entry_observation",
        "raw_match_path_and_selected_record_sha256",
        2,
        564,
    ),
    (
        "coa-combatants-gear-slot-v1",
        "nested_parser_observation",
        ["gear_slot_summary"],
        "combatants_gear_slot_observation",
        "raw_match_path_and_selected_record_sha256",
        5,
        189,
    ),
]


def _contracts(group: str) -> list[dict[str, Any]]:
    scope = _GROUPS[group]["scope"]
    occurrence_count = {
        "actor_identity": 11,
        "guild_membership": 11,
        "instance_context": 11,
        "specialization_summary": 11,
        "talent_container_summary": 11,
        "classless_talent_rank": 564,
        "hero_build_entry": 564,
        "gear_slot_summary": 189,
    }[group]
    result = []
    for source_name, output_field, value_type, required in _GROUPS[group]["fields"]:
        count = occurrence_count
        if group == "specialization_summary" and not required:
            count = 1
        result.append(
            {
                "source_group": group,
                "source_path": f"{scope}/{source_name}",
                "output_field": output_field,
                "types": [value_type],
                "nullable": False,
                "required": required,
                "occurrence_count": count,
                "parser_status": "reviewed_candidate",
                "semantic_status": "unverified",
            }
        )
    return result


def _design_payload() -> dict[str, Any]:
    rows = []
    for (
        design_id,
        design_type,
        source_groups,
        entity_type,
        identity_policy,
        field_count,
        match_count,
    ) in _DESIGN_CONFIG:
        contracts = [contract for group in source_groups for contract in _contracts(group)]
        rows.append(
            {
                "design_id": design_id,
                "design_type": design_type,
                "design_version": "1",
                "source_code": _SOURCE_CODE,
                "source_groups": source_groups,
                "source_scopes": [_GROUPS[group]["scope"] for group in source_groups],
                "selected_field_count": field_count,
                "expected_source_match_count": match_count,
                "field_contracts": contracts,
                "target": {
                    "storage_table": "canonical_entity_observation",
                    "entity_type": entity_type,
                    "trust_status": "observed_candidate",
                    "core_entity_mutation_allowed": False,
                },
                "identity_contract": {
                    "identity_policy": identity_policy,
                    "selected_record_sha256_required": True,
                    "semantic_uniqueness_claimed": False,
                },
                "implementation_status": "design_only",
                "candidate_mapping_file": None,
                "generic_normalizer_compatible": False,
                "dedicated_extractor_required": True,
                "exact_raw_validation_required": True,
                "promotion_allowed": False,
                "normalization_allowed": False,
            }
        )
    return {
        "schema_version": 1,
        "design_kind": "observed_combatants_info_mapping_design",
        "endpoint": {
            "endpoint_kind": "combatants_info",
            "route_template": "/api/reports/{template}/encounters/{template}/combatants-info",
            "payload_hash": "45672e0f0ff9eb461c575bdd38385795daa6326378bc3f8ad51474276140dc14",
            "schema_fingerprint": "41d6d15422c668f83d2ccae1ec0ff2969671861f9e43b21cb371578961c5f8ff",
            "transport_provenance_type": "upstream_derived",
            "content_provenance_status": "candidate_companion_addon_enrichment",
        },
        "mapping_designs": rows,
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
            "mapping_design_count": 6,
            "source_group_count": 8,
            "selected_field_contract_count": 37,
            "actor_enrichment_design_count": 1,
            "context_observation_design_count": 1,
            "nested_observation_design_count": 4,
            "immutable_observation_design_count": 6,
            "dedicated_extractor_design_count": 6,
            "generic_normalizer_compatible_design_count": 0,
            "expected_outer_actor_link_count": 11,
            "deferred_field_count": 19,
            "missing_optional_scope_count": 2,
            "contains_source_scalar_values": False,
            "candidate_mapping_files_ready": False,
            "ready_for_candidate_extractor_implementation": True,
            "combatants_info_enrichment_available": False,
            "normalization_allowed": False,
            "planner_scoring_allowed": False,
        },
    }


def _payload() -> dict[str, Any]:
    combatants = []
    talent_offset = 0
    gear_offset = 0
    for actor_number in range(1, 12):
        nested_count = 514 if actor_number == 1 else 5
        gear_count = 17 if actor_number <= 9 else 18
        specialization: dict[str, Any] = {
            "active_spec_idx": actor_number,
            "talents": {
                "class_label": "Classless",
                "class_slug": "classless",
                "tree_order": [1, 2, 3],
            },
            "resolved_ca_talent_ranks": [
                {
                    "bisbeard_tree": "tree",
                    "cao_id": talent_offset + index + 1,
                    "icon": "icon",
                    "name": f"Talent {talent_offset + index + 1}",
                    "rank": 1,
                }
                for index in range(nested_count)
            ],
            "hero_build": [
                {"entry_id": talent_offset + index + 1, "rank": 1}
                for index in range(nested_count)
            ],
        }
        if actor_number == 1:
            specialization.update(
                {
                    "active_spec_name": "Observed spec",
                    "active_spec_role": "Observed role",
                    "active_spec_slot": 1,
                }
            )
        combatants.append(
            {
                "character_id": actor_number,
                "ci_resolved": {
                    "player": {
                        "class": "Classless",
                        "gender": 1,
                        "guid": f"GUID-{actor_number}",
                        "level": 60,
                        "name": f"Player {actor_number}",
                        "race": "Human",
                        "realm": "Realm",
                    },
                    "guild": {
                        "name": "Guild",
                        "rank_index": 1,
                        "rank_name": "Member",
                    },
                    "instance": {
                        "difficulty_index": 1,
                        "difficulty_name": "Observed",
                        "instance_type": "raid",
                        "is_dynamic": False,
                        "map_id": 1,
                        "max_players": 25,
                        "name": "Instance",
                        "player_difficulty": 1,
                    },
                    "specialization": specialization,
                    "gear": [
                        {
                            "enchant": 0,
                            "item_id": gear_offset + index + 1,
                            "slot": index,
                            "suffix": 0,
                            "unique": gear_offset + index + 1,
                        }
                        for index in range(gear_count)
                    ],
                },
            }
        )
        talent_offset += nested_count
        gear_offset += gear_count
    return {"combatants": combatants}


def _actor_index() -> dict[str, dict[str, str]]:
    return {
        str(number): {
            "actor_id": stable_id("actor", _SOURCE_CODE, str(number)),
            "nickname": f"Player {number}",
        }
        for number in range(1, 12)
    }


def test_exact_design_packet_is_accepted() -> None:
    rows = _validate_design(_design_payload())
    assert set(rows) == {row[0] for row in _DESIGN_CONFIG}


def test_candidate_extraction_matches_exact_bounded_counts() -> None:
    design = _design_payload()
    designs = {row["design_id"]: row for row in design["mapping_designs"]}
    observations, receipt_rows, summary = extract_combatants_info_candidate_payload(
        _payload(),
        designs,
        report_id="report-id",
        encounter_id="encounter-id",
        actor_index=_actor_index(),
    )

    assert summary == {
        "design_count": 6,
        "selected_field_contract_count": 37,
        "source_match_count": 1350,
        "output_observation_count": 1340,
        "linked_actor_count": 11,
        "actor_name_exact_match_count": 11,
        "deduplicated_source_match_count": 10,
    }
    counts = {row["design_id"]: row["output_observation_count"] for row in receipt_rows}
    assert counts == {
        "coa-combatants-actor-enrichment-v1": 11,
        "coa-combatants-instance-context-v1": 1,
        "coa-combatants-talent-container-v1": 11,
        "coa-combatants-classless-talent-rank-v1": 564,
        "coa-combatants-hero-build-entry-v1": 564,
        "coa-combatants-gear-slot-v1": 189,
    }
    instance_rows = observations["coa-combatants-instance-context-v1"]
    assert len(instance_rows) == 1
    assert len(instance_rows[0]["linked_actor_ids"]) == 11
    assert all(row["core_entity_mutation_performed"] is False for row in receipt_rows)


def test_candidate_extraction_rejects_selected_field_type_change() -> None:
    payload = _payload()
    payload["combatants"][0]["ci_resolved"]["player"]["gender"] = "unexpected"
    designs = {row["design_id"]: row for row in _design_payload()["mapping_designs"]}

    with pytest.raises(ValueError, match="field type mismatch"):
        extract_combatants_info_candidate_payload(
            payload,
            designs,
            report_id="report-id",
            encounter_id="encounter-id",
            actor_index=_actor_index(),
        )


def test_candidate_extraction_rejects_missing_persisted_actor() -> None:
    actors = _actor_index()
    del actors["11"]
    designs = {row["design_id"]: row for row in _design_payload()["mapping_designs"]}

    with pytest.raises(ValueError, match="missing from persisted actor table"):
        extract_combatants_info_candidate_payload(
            _payload(),
            designs,
            report_id="report-id",
            encounter_id="encounter-id",
            actor_index=actors,
        )


def test_candidate_extraction_rejects_actor_nickname_conflict() -> None:
    actors = _actor_index()
    actors["1"]["nickname"] = "Different"
    designs = {row["design_id"]: row for row in _design_payload()["mapping_designs"]}

    with pytest.raises(ValueError, match="nickname conflict"):
        extract_combatants_info_candidate_payload(
            _payload(),
            designs,
            report_id="report-id",
            encounter_id="encounter-id",
            actor_index=actors,
        )
