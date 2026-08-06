from __future__ import annotations

import json
from pathlib import Path

import pytest

from coa_workbench.collector.combatants_info_field_selection import (
    select_observed_combatants_info_fields,
)

_ROUTE = "/api/reports/{template}/encounters/{template}/combatants-info"
_HASH = "45672e0f0ff9eb461c575bdd38385795daa6326378bc3f8ad51474276140dc14"
_FINGERPRINT = "41d6d15422c668f83d2ccae1ec0ff2969671861f9e43b21cb371578961c5f8ff"


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _field(
    path: str,
    value_type: str,
    *,
    occurrences: int,
    observed_all: bool = True,
    nullable: bool = False,
) -> dict[str, object]:
    return {
        "name": path.rsplit("/", 1)[-1],
        "path": path,
        "types": [value_type],
        "type_counts": {value_type: occurrences},
        "nullable": nullable,
        "is_array": value_type == "array",
        "is_object": value_type == "object",
        "occurrence_count": occurrences,
        "observed_on_all_scope_occurrences": observed_all,
    }


def _scope(
    path: str,
    fields: list[dict[str, object]],
    *,
    required: bool,
) -> dict[str, object]:
    return {
        "endpoint_kind": "combatants_info",
        "route_template": _ROUTE,
        "payload_hash": _HASH,
        "schema_fingerprint": _FINGERPRINT,
        "scope": path,
        "review_label": "fixture_candidate",
        "review_status": "candidate",
        "semantic_status": "unverified_candidate",
        "manual_decision_required": True,
        "required_scope": required,
        "scope_shape": {
            "path": path,
            "types": ["object"],
            "type_counts": {"object": 11},
            "nullable": False,
            "is_array": False,
            "is_object": True,
            "occurrence_count": 11,
        },
        "direct_fields": fields,
        "summary": {
            "scope_occurrence_count": 11,
            "direct_field_count": len(fields),
            "nullable_direct_field_count": sum(field["nullable"] is True for field in fields),
            "array_direct_field_count": sum(field["is_array"] is True for field in fields),
            "object_direct_field_count": sum(field["is_object"] is True for field in fields),
            "fields_observed_on_all_scope_occurrences": sum(
                field["observed_on_all_scope_occurrences"] is True for field in fields
            ),
        },
    }


def _selected_and_deferred_fields() -> dict[str, list[dict[str, object]]]:
    player = "/combatants/*/ci_resolved/player"
    guild = "/combatants/*/ci_resolved/guild"
    instance = "/combatants/*/ci_resolved/instance"
    specialization = "/combatants/*/ci_resolved/specialization"
    talents = specialization + "/talents"
    ranks = specialization + "/resolved_ca_talent_ranks/*"
    hero = specialization + "/hero_build/*"
    unlocked = specialization + "/unlocked_specs/*"
    vanilla = specialization + "/vanilla_talents"
    gear = "/combatants/*/ci_resolved/gear/*"

    return {
        player: [
            _field(player + "/class", "string", occurrences=11),
            _field(player + "/gender", "integer", occurrences=11),
            _field(player + "/guid", "string", occurrences=11),
            _field(player + "/guild", "string", occurrences=11),
            _field(player + "/level", "integer", occurrences=11),
            _field(player + "/name", "string", occurrences=11),
            _field(player + "/race", "string", occurrences=11),
            _field(player + "/realm", "string", occurrences=11),
        ],
        guild: [
            _field(guild + "/name", "string", occurrences=11),
            _field(guild + "/rank_index", "integer", occurrences=11),
            _field(guild + "/rank_name", "string", occurrences=11),
        ],
        instance: [
            _field(instance + "/difficulty_index", "integer", occurrences=11),
            _field(instance + "/difficulty_name", "string", occurrences=11),
            _field(instance + "/instance_type", "string", occurrences=11),
            _field(instance + "/is_dynamic", "boolean", occurrences=11),
            _field(instance + "/map_id", "integer", occurrences=11),
            _field(instance + "/max_players", "integer", occurrences=11),
            _field(instance + "/name", "string", occurrences=11),
            _field(instance + "/player_difficulty", "integer", occurrences=11),
        ],
        specialization: [
            _field(specialization + "/active_spec_idx", "integer", occurrences=11),
            _field(
                specialization + "/active_spec_name",
                "string",
                occurrences=1,
                observed_all=False,
            ),
            _field(
                specialization + "/active_spec_role",
                "string",
                occurrences=1,
                observed_all=False,
            ),
            _field(
                specialization + "/active_spec_slot",
                "integer",
                occurrences=1,
                observed_all=False,
            ),
            _field(specialization + "/hero_build", "object", occurrences=11),
            _field(
                specialization + "/investment",
                "object",
                occurrences=1,
                observed_all=False,
            ),
            _field(specialization + "/resolved_ca_known", "array", occurrences=11),
            _field(
                specialization + "/resolved_ca_talent_ranks",
                "array",
                occurrences=11,
            ),
            _field(specialization + "/talents", "object", occurrences=11),
            _field(
                specialization + "/unlocked_specs",
                "object",
                occurrences=10,
                observed_all=False,
            ),
            _field(specialization + "/vanilla_talents", "object", occurrences=11),
        ],
        talents: [
            _field(talents + "/class_label", "string", occurrences=11),
            _field(talents + "/class_slug", "string", occurrences=11),
            _field(talents + "/tree_order", "array", occurrences=11),
            _field(talents + "/trees", "object", occurrences=11),
        ],
        ranks: [
            _field(ranks + "/bisbeard_tree", "string", occurrences=564),
            _field(ranks + "/cao_id", "integer", occurrences=564),
            _field(ranks + "/icon", "string", occurrences=564),
            _field(ranks + "/name", "string", occurrences=564),
            _field(ranks + "/rank", "integer", occurrences=564),
        ],
        hero: [
            _field(hero + "/entry_id", "integer", occurrences=564),
            _field(hero + "/rank", "integer", occurrences=564),
        ],
        unlocked: [],
        vanilla: [_field(vanilla + "/*", "object", occurrences=1, observed_all=False)],
        gear: [
            _field(gear + "/enchant", "integer", occurrences=189),
            _field(gear + "/gems", "object", occurrences=189),
            _field(gear + "/is_vanity", "boolean", occurrences=1, observed_all=False),
            _field(gear + "/item_id", "integer", occurrences=189),
            _field(gear + "/raw", "string", occurrences=189),
            _field(gear + "/resolved_bisbeard", "object", occurrences=189, nullable=True),
            _field(gear + "/resolved_enchant", "object", occurrences=189, nullable=True),
            _field(gear + "/resolved_gems", "array", occurrences=189),
            _field(gear + "/resolved_item", "object", occurrences=189, nullable=True),
            _field(gear + "/resolved_set", "object", occurrences=189, nullable=True),
            _field(gear + "/resolved_suffix", "null", occurrences=189, nullable=True),
            _field(gear + "/slot", "integer", occurrences=189),
            _field(gear + "/suffix", "integer", occurrences=189),
            _field(gear + "/unique", "integer", occurrences=189),
        ],
    }


def _fixture(tmp_path: Path) -> tuple[Path, Path]:
    scope_fields = _selected_and_deferred_fields()
    required_scopes = {
        "/combatants/*/ci_resolved/player",
        "/combatants/*/ci_resolved/guild",
        "/combatants/*/ci_resolved/instance",
        "/combatants/*/ci_resolved/specialization",
    }
    deep_path = tmp_path / "deep-review.json"
    scope_path = tmp_path / "scope-review.json"
    _write_json(
        deep_path,
        {
            "schema_version": 1,
            "review_kind": "observed_combatants_info_deep_scope_review",
            "source_persistence_run_id": "a" * 64,
            "endpoint": {
                "endpoint_kind": "combatants_info",
                "route_template": _ROUTE,
                "payload_hash": _HASH,
                "schema_fingerprint": _FINGERPRINT,
                "review_status": "candidate",
                "transport_provenance_type": "upstream_derived",
                "content_provenance_status": "candidate_companion_addon_enrichment",
            },
            "scopes": [
                _scope(path, fields, required=path in required_scopes)
                for path, fields in scope_fields.items()
            ],
            "missing_optional_scopes": [
                {
                    "scope": "/combatants/*/ci_resolved/specialization/talents/trees/*",
                    "review_label": "resolved_talent_tree_candidate",
                    "reason": "scope_not_observed_in_exact_mapping_review",
                },
                {
                    "scope": "/combatants/*/ci_resolved/mystic_enchants/*",
                    "review_label": "resolved_mystic_enchant_candidate",
                    "reason": "scope_not_observed_in_exact_mapping_review",
                },
            ],
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
                "scope_candidate_count": 12,
                "present_scope_count": 10,
                "required_scope_count": 4,
                "required_scope_present_count": 4,
                "optional_scope_candidate_count": 8,
                "optional_scope_present_count": 6,
                "optional_scope_missing_count": 2,
                "direct_field_count": 56,
                "persisted_report_count": 1,
                "persisted_encounter_count": 14,
                "persisted_actor_count": 31,
                "persisted_participant_count": 31,
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
        },
    )
    _write_json(
        scope_path,
        {
            "schema_version": 1,
            "review_kind": "observed_report_slice_scope_review",
            "scopes": [
                {
                    "endpoint_kind": "combatants_info",
                    "route_template": _ROUTE,
                    "payload_hash": _HASH,
                    "schema_fingerprint": _FINGERPRINT,
                    "scope": "/combatants/*",
                    "review_status": "candidate",
                    "semantic_status": "unverified_candidate",
                    "manual_decision_required": True,
                    "direct_fields": [
                        {
                            "path": "/combatants/*/character_id",
                            "types": ["integer"],
                            "nullable": False,
                            "occurrence_count": 31,
                            "observed_on_all_scope_occurrences": True,
                        }
                    ],
                }
            ],
            "decision_boundary": {
                "status": "candidate",
                "automatic_scope_selection": False,
                "automatic_field_selection": False,
                "can_promote": False,
                "semantic_verification_required": True,
                "normalization_allowed": False,
            },
            "summary": {
                "endpoint_count": 3,
                "scope_candidate_count": 7,
                "direct_field_count": 120,
                "all_archives_consistent": True,
                "contains_source_scalar_values": False,
                "semantic_verification_required": True,
                "normalization_allowed": False,
                "ready_for_manual_field_selection": True,
            },
        },
    )
    return deep_path, scope_path


def test_selects_bounded_combatants_fields_without_creating_mapping(tmp_path):
    deep_path, scope_path = _fixture(tmp_path)

    selection = select_observed_combatants_info_fields(deep_path, scope_path)

    assert selection["summary"] == {
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
    assert selection["outer_actor_linkage"]["review_path"] == "/combatants/*/character_id"
    groups = {row["group_id"]: row for row in selection["selection_groups"]}
    assert groups["actor_identity"]["source_actor_linkage"]["expression"] == (
        "@ancestor[1]/character_id"
    )
    assert groups["classless_talent_rank"]["source_actor_linkage"]["expression"] == (
        "@ancestor[3]/character_id"
    )
    assert groups["gear_slot_summary"]["selected_field_count"] == 5
    assert all(row["mapping_status"] == "not_created" for row in groups.values())
    assert "PRIVATE PLAYER" not in json.dumps(selection)


def test_rejects_selected_field_type_mismatch(tmp_path):
    deep_path, scope_path = _fixture(tmp_path)
    review = json.loads(deep_path.read_text(encoding="utf-8"))
    gear = next(row for row in review["scopes"] if row["scope"].endswith("/gear/*"))
    slot = next(row for row in gear["direct_fields"] if row["name"] == "slot")
    slot["types"] = ["string"]
    _write_json(deep_path, review)

    with pytest.raises(ValueError, match="field type mismatch"):
        select_observed_combatants_info_fields(deep_path, scope_path)


def test_rejects_optional_field_that_appears_everywhere(tmp_path):
    deep_path, scope_path = _fixture(tmp_path)
    review = json.loads(deep_path.read_text(encoding="utf-8"))
    specialization = next(
        row
        for row in review["scopes"]
        if row["scope"] == "/combatants/*/ci_resolved/specialization"
    )
    active_name = next(
        row for row in specialization["direct_fields"] if row["name"] == "active_spec_name"
    )
    active_name["observed_on_all_scope_occurrences"] = True
    _write_json(deep_path, review)

    with pytest.raises(ValueError, match="optional combatants field unexpectedly appears everywhere"):
        select_observed_combatants_info_fields(deep_path, scope_path)


def test_rejects_missing_outer_actor_linkage(tmp_path):
    deep_path, scope_path = _fixture(tmp_path)
    review = json.loads(scope_path.read_text(encoding="utf-8"))
    review["scopes"][0]["direct_fields"] = []
    _write_json(scope_path, review)

    with pytest.raises(ValueError, match="outer actor linkage field is missing"):
        select_observed_combatants_info_fields(deep_path, scope_path)


def test_rejects_changed_missing_scope_set(tmp_path):
    deep_path, scope_path = _fixture(tmp_path)
    review = json.loads(deep_path.read_text(encoding="utf-8"))
    review["missing_optional_scopes"].pop()
    _write_json(deep_path, review)

    with pytest.raises(ValueError, match="missing optional scope set mismatch"):
        select_observed_combatants_info_fields(deep_path, scope_path)
