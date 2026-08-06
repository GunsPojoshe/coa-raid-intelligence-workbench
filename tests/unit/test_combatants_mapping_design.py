from __future__ import annotations

import json
from pathlib import Path

import pytest

from coa_workbench.collector.combatants_mapping_design import (
    design_observed_combatants_info_mappings,
)


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _contract(
    source_name: str,
    output_field: str,
    value_type: str,
    occurrence_count: int,
    *,
    required: bool = True,
) -> dict[str, object]:
    return {
        "source_name": source_name,
        "source_path": f"/scope/{source_name}",
        "output_field": output_field,
        "types": [value_type],
        "nullable": False,
        "required": required,
        "occurrence_count": occurrence_count,
        "observed_on_all_scope_occurrences": required,
        "semantic_status": "reviewed_parser_candidate",
    }


def _group(
    group_id: str,
    scope: str,
    strategy: str,
    expression: str,
    contracts: list[dict[str, object]],
) -> dict[str, object]:
    for contract in contracts:
        contract["source_path"] = f"{scope}/{contract['source_name']}"
    return {
        "group_id": group_id,
        "scope": scope,
        "mapping_strategy": strategy,
        "mapping_status": "not_created",
        "selected_field_count": len(contracts),
        "source_actor_linkage": {
            "review_scope": "/combatants/*",
            "review_path": "/combatants/*/character_id",
            "expression": expression,
            "stable_actor_strategy": "reuse_existing_source_actor_id",
            "status": "exact_path_confirmed_candidate_merge",
        },
        "field_contracts": contracts,
    }


def _selection_payload() -> dict[str, object]:
    groups = [
        _group(
            "actor_identity",
            "/combatants/*/ci_resolved/player",
            "actor_enrichment_candidate",
            "@ancestor[1]/character_id",
            [
                _contract("class", "class", "string", 11),
                _contract("gender", "gender", "integer", 11),
                _contract("guid", "guid", "string", 11),
                _contract("level", "level", "integer", 11),
                _contract("name", "name", "string", 11),
                _contract("race", "race", "string", 11),
                _contract("realm", "realm", "string", 11),
            ],
        ),
        _group(
            "guild_membership",
            "/combatants/*/ci_resolved/guild",
            "actor_enrichment_candidate",
            "@ancestor[1]/character_id",
            [
                _contract("name", "guild_name", "string", 11),
                _contract("rank_index", "guild_rank_index", "integer", 11),
                _contract("rank_name", "guild_rank_name", "string", 11),
            ],
        ),
        _group(
            "instance_context",
            "/combatants/*/ci_resolved/instance",
            "deduplicated_context_observation_candidate",
            "@ancestor[1]/character_id",
            [
                _contract("difficulty_index", "difficulty_index", "integer", 11),
                _contract("difficulty_name", "difficulty_name", "string", 11),
                _contract("instance_type", "instance_type", "string", 11),
                _contract("is_dynamic", "is_dynamic", "boolean", 11),
                _contract("map_id", "map_id", "integer", 11),
                _contract("max_players", "max_players", "integer", 11),
                _contract("name", "instance_name", "string", 11),
                _contract("player_difficulty", "player_difficulty", "integer", 11),
            ],
        ),
        _group(
            "specialization_summary",
            "/combatants/*/ci_resolved/specialization",
            "actor_enrichment_candidate",
            "@ancestor[1]/character_id",
            [
                _contract("active_spec_idx", "active_spec_idx", "integer", 11),
                _contract(
                    "active_spec_name",
                    "active_spec_name",
                    "string",
                    1,
                    required=False,
                ),
                _contract(
                    "active_spec_role",
                    "active_spec_role",
                    "string",
                    1,
                    required=False,
                ),
                _contract(
                    "active_spec_slot",
                    "active_spec_slot",
                    "integer",
                    1,
                    required=False,
                ),
            ],
        ),
        _group(
            "talent_container_summary",
            "/combatants/*/ci_resolved/specialization/talents",
            "nested_observation_candidate",
            "@ancestor[2]/character_id",
            [
                _contract("class_label", "class_label", "string", 11),
                _contract("class_slug", "class_slug", "string", 11),
                _contract("tree_order", "tree_order", "array", 11),
            ],
        ),
        _group(
            "classless_talent_rank",
            "/combatants/*/ci_resolved/specialization/resolved_ca_talent_ranks/*",
            "nested_observation_candidate",
            "@ancestor[3]/character_id",
            [
                _contract("bisbeard_tree", "bisbeard_tree", "string", 564),
                _contract("cao_id", "cao_id", "integer", 564),
                _contract("icon", "icon", "string", 564),
                _contract("name", "name", "string", 564),
                _contract("rank", "rank", "integer", 564),
            ],
        ),
        _group(
            "hero_build_entry",
            "/combatants/*/ci_resolved/specialization/hero_build/*",
            "nested_observation_candidate",
            "@ancestor[3]/character_id",
            [
                _contract("entry_id", "entry_id", "integer", 564),
                _contract("rank", "rank", "integer", 564),
            ],
        ),
        _group(
            "gear_slot_summary",
            "/combatants/*/ci_resolved/gear/*",
            "nested_observation_candidate",
            "@ancestor[2]/character_id",
            [
                _contract("enchant", "enchant", "integer", 189),
                _contract("item_id", "item_id", "integer", 189),
                _contract("slot", "slot", "integer", 189),
                _contract("suffix", "suffix", "integer", 189),
                _contract("unique", "unique", "integer", 189),
            ],
        ),
    ]
    return {
        "schema_version": 1,
        "selection_kind": "observed_combatants_info_field_selection",
        "generated_at": "2026-07-29T21:50:16Z",
        "source_deep_review_name": "observed-combatants-info-deep-scope-review.json",
        "source_scope_review_name": "observed-report-slice-scope-review.json",
        "source_persistence_run_id": "a" * 64,
        "endpoint": {
            "endpoint_kind": "combatants_info",
            "route_template": "/api/reports/{template}/encounters/{template}/combatants-info",
            "payload_hash": "45672e0f0ff9eb461c575bdd38385795daa6326378bc3f8ad51474276140dc14",
            "schema_fingerprint": "41d6d15422c668f83d2ccae1ec0ff2969671861f9e43b21cb371578961c5f8ff",
            "transport_provenance_type": "upstream_derived",
            "content_provenance_status": "candidate_companion_addon_enrichment",
        },
        "outer_actor_linkage": {
            "review_scope": "/combatants/*",
            "review_path": "/combatants/*/character_id",
            "types": ["integer"],
            "nullable": False,
            "observed_on_all_scope_occurrences": True,
            "occurrence_count": 11,
            "status": "exact_path_confirmed_candidate_merge",
        },
        "selection_groups": groups,
        "deferred_fields": [
            {
                "path": f"/deferred/{index}",
                "decision": "deferred",
                "reason": "review required",
            }
            for index in range(19)
        ],
        "missing_optional_scopes": [
            {
                "scope": "/combatants/*/ci_resolved/mystic_enchants/*",
                "decision": "deferred",
                "reason": "scope_not_observed_in_exact_mapping_review",
            },
            {
                "scope": "/combatants/*/ci_resolved/specialization/talents/trees/*",
                "decision": "deferred",
                "reason": "scope_not_observed_in_exact_mapping_review",
            },
        ],
        "decision_boundary": {
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
        },
        "summary": {
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
        },
    }


def _selection_file(tmp_path: Path) -> Path:
    path = tmp_path / "selection.json"
    _write_json(path, _selection_payload())
    return path


def test_mapping_design_emits_six_storage_aware_units(tmp_path: Path) -> None:
    design = design_observed_combatants_info_mappings(_selection_file(tmp_path))

    assert design["schema_version"] == 1
    assert design["design_kind"] == "observed_combatants_info_mapping_design"
    assert design["summary"]["mapping_design_count"] == 6
    assert design["summary"]["selected_field_contract_count"] == 37
    assert design["summary"]["actor_enrichment_design_count"] == 1
    assert design["summary"]["context_observation_design_count"] == 1
    assert design["summary"]["nested_observation_design_count"] == 4
    assert design["summary"]["immutable_observation_design_count"] == 6
    assert design["summary"]["dedicated_extractor_design_count"] == 6
    assert design["summary"]["generic_normalizer_compatible_design_count"] == 0
    assert design["summary"]["contains_source_scalar_values"] is False
    assert design["summary"]["candidate_mapping_files_ready"] is False


def test_actor_design_uses_existing_actor_without_core_mutation(tmp_path: Path) -> None:
    design = design_observed_combatants_info_mappings(_selection_file(tmp_path))
    actor = next(
        row for row in design["mapping_designs"] if row["design_id"] == "coa-combatants-actor-enrichment-v1"
    )

    assert actor["source_groups"] == [
        "actor_identity",
        "guild_membership",
        "specialization_summary",
    ]
    assert actor["selected_field_count"] == 14
    assert actor["expected_source_match_count"] == 11
    assert actor["source_actor_linkage"]["expected_link_count"] == 11
    assert actor["target"]["storage_table"] == "canonical_entity_observation"
    assert actor["target"]["core_entity_mutation_allowed"] is False
    assert actor["merge_contract"]["actor_merge_validation_required"] is True
    assert actor["merge_contract"]["automatic_core_projection"] is False


def test_nested_designs_do_not_claim_semantic_uniqueness(tmp_path: Path) -> None:
    design = design_observed_combatants_info_mappings(_selection_file(tmp_path))
    rows = {
        row["design_id"]: row
        for row in design["mapping_designs"]
        if row["design_type"] == "nested_parser_observation"
    }

    assert set(rows) == {
        "coa-combatants-talent-container-v1",
        "coa-combatants-classless-talent-rank-v1",
        "coa-combatants-hero-build-entry-v1",
        "coa-combatants-gear-slot-v1",
    }
    assert rows["coa-combatants-talent-container-v1"]["expected_source_match_count"] == 11
    assert rows["coa-combatants-classless-talent-rank-v1"]["expected_source_match_count"] == 564
    assert rows["coa-combatants-hero-build-entry-v1"]["expected_source_match_count"] == 564
    assert rows["coa-combatants-gear-slot-v1"]["expected_source_match_count"] == 189
    for row in rows.values():
        assert row["identity_contract"]["raw_match_path_required"] is True
        assert row["identity_contract"]["semantic_uniqueness_claimed"] is False
        assert row["generic_normalizer_compatible"] is False
        assert row["dedicated_extractor_required"] is True
        assert row["normalization_allowed"] is False


def test_mapping_design_rejects_tampered_group_status(tmp_path: Path) -> None:
    payload = _selection_payload()
    payload["selection_groups"][0]["mapping_status"] = "candidate"
    path = tmp_path / "selection.json"
    _write_json(path, payload)

    with pytest.raises(ValueError, match="selection group mismatch"):
        design_observed_combatants_info_mappings(path)


def test_mapping_design_rejects_changed_actor_link_count(tmp_path: Path) -> None:
    payload = _selection_payload()
    payload["outer_actor_linkage"]["occurrence_count"] = 12
    path = tmp_path / "selection.json"
    _write_json(path, payload)

    with pytest.raises(ValueError, match="actor linkage mismatch"):
        design_observed_combatants_info_mappings(path)
