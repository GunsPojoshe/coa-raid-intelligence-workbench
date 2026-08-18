from __future__ import annotations

import json
from pathlib import Path

import pytest

from coa_workbench.collector.combatants_scope_review import (
    build_observed_combatants_info_deep_scope_review,
)


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _shape(
    path: str,
    value_type: str,
    *,
    occurrences: int = 1,
    nullable: bool = False,
    observed_keys: list[str] | None = None,
) -> dict[str, object]:
    row: dict[str, object] = {
        "path": path,
        "occurrence_count": occurrences,
        "type_counts": {value_type: occurrences},
        "nullable": nullable,
    }
    if value_type == "object":
        keys = observed_keys or []
        row["object"] = {
            "occurrence_count": occurrences,
            "key_mode_counts": {"fixed_fields": occurrences},
            "fixed_fields": {
                "occurrence_count": occurrences,
                "observed_keys": keys,
                "required_keys": keys,
            },
        }
    if value_type == "array":
        row["array"] = {
            "occurrence_count": occurrences,
            "total_items": occurrences,
            "min_length": 1,
            "max_length": 1,
            "item_type_counts": {"object": occurrences},
        }
    return row


def _mapping_review() -> dict[str, object]:
    combatant_shapes = [
        _shape("/", "object", observed_keys=["combatants", "success"]),
        _shape("/combatants", "array"),
        _shape(
            "/combatants/*",
            "object",
            occurrences=2,
            observed_keys=["character_id", "ci_resolved"],
        ),
        _shape("/combatants/*/character_id", "integer", occurrences=2),
        _shape(
            "/combatants/*/ci_resolved",
            "object",
            occurrences=2,
            observed_keys=["gear", "guild", "instance", "player", "specialization"],
        ),
        _shape(
            "/combatants/*/ci_resolved/player",
            "object",
            occurrences=2,
            observed_keys=["class", "guid", "name", "realm"],
        ),
        _shape("/combatants/*/ci_resolved/player/class", "string", occurrences=2),
        _shape("/combatants/*/ci_resolved/player/guid", "string", occurrences=2),
        _shape("/combatants/*/ci_resolved/player/name", "string", occurrences=2),
        _shape("/combatants/*/ci_resolved/player/realm", "string", occurrences=2),
        _shape(
            "/combatants/*/ci_resolved/guild",
            "object",
            occurrences=2,
            observed_keys=["name", "rank_index", "rank_name"],
        ),
        _shape("/combatants/*/ci_resolved/guild/name", "string", occurrences=2),
        _shape("/combatants/*/ci_resolved/guild/rank_index", "integer", occurrences=2),
        _shape("/combatants/*/ci_resolved/guild/rank_name", "string", occurrences=2),
        _shape(
            "/combatants/*/ci_resolved/instance",
            "object",
            occurrences=2,
            observed_keys=["difficulty_index", "map_id", "name"],
        ),
        _shape(
            "/combatants/*/ci_resolved/instance/difficulty_index",
            "integer",
            occurrences=2,
        ),
        _shape("/combatants/*/ci_resolved/instance/map_id", "integer", occurrences=2),
        _shape("/combatants/*/ci_resolved/instance/name", "string", occurrences=2),
        _shape(
            "/combatants/*/ci_resolved/specialization",
            "object",
            occurrences=2,
            observed_keys=["active_spec_idx", "resolved_ca_talent_ranks", "talents"],
        ),
        _shape(
            "/combatants/*/ci_resolved/specialization/active_spec_idx",
            "integer",
            occurrences=2,
        ),
        _shape(
            "/combatants/*/ci_resolved/specialization/talents",
            "object",
            occurrences=2,
            observed_keys=["class_label", "class_slug", "trees"],
        ),
        _shape(
            "/combatants/*/ci_resolved/specialization/talents/class_label",
            "string",
            occurrences=2,
        ),
        _shape(
            "/combatants/*/ci_resolved/specialization/talents/class_slug",
            "string",
            occurrences=2,
        ),
        _shape(
            "/combatants/*/ci_resolved/specialization/resolved_ca_talent_ranks",
            "array",
            occurrences=2,
        ),
        _shape(
            "/combatants/*/ci_resolved/specialization/resolved_ca_talent_ranks/*",
            "object",
            occurrences=2,
            observed_keys=["rank", "spell_id"],
        ),
        _shape(
            "/combatants/*/ci_resolved/specialization/resolved_ca_talent_ranks/*/rank",
            "integer",
            occurrences=2,
        ),
        _shape(
            "/combatants/*/ci_resolved/specialization/resolved_ca_talent_ranks/*/spell_id",
            "integer",
            occurrences=2,
        ),
        _shape(
            "/combatants/*/ci_resolved/gear/*",
            "object",
            occurrences=4,
            observed_keys=["item_id", "slot"],
        ),
        _shape("/combatants/*/ci_resolved/gear/*/item_id", "integer", occurrences=4),
        _shape("/combatants/*/ci_resolved/gear/*/slot", "integer", occurrences=4),
        _shape("/success", "boolean"),
    ]
    placeholder = {
        "endpoint_kind": "report_detail",
        "route_template": "/api/reports/{template}",
        "payload_hash": "1" * 64,
        "schema_fingerprint": "a" * 64,
        "top_level_kind": "object",
        "top_level_keys": ["encounters", "report", "success"],
        "review_status": "candidate",
        "provenance_type": "upstream_derived",
        "scope": "/",
        "field_shapes": [_shape("/", "object")],
    }
    encounter = {
        **placeholder,
        "endpoint_kind": "encounter_detail",
        "route_template": "/api/reports/{template}/encounters/{template}",
        "payload_hash": "2" * 64,
        "schema_fingerprint": "b" * 64,
        "top_level_keys": ["character_stats", "encounter", "success"],
    }
    combatants = {
        **placeholder,
        "endpoint_kind": "combatants_info",
        "route_template": "/api/reports/{template}/encounters/{template}/combatants-info",
        "payload_hash": "45672e0f0ff9eb461c575bdd38385795daa6326378bc3f8ad51474276140dc14",
        "schema_fingerprint": "41d6d15422c668f83d2ccae1ec0ff2969671861f9e43b21cb371578961c5f8ff",
        "top_level_keys": ["combatants", "success"],
        "field_shapes": combatant_shapes,
    }
    return {
        "schema_version": 1,
        "review_kind": "observed_report_slice_mapping_review",
        "endpoints": [placeholder, encounter, combatants],
        "summary": {
            "endpoint_count": 3,
            "raw_archive_count": 3,
            "all_archives_consistent": True,
            "contains_source_scalar_values": False,
            "semantic_verification_required": True,
            "normalization_allowed": False,
            "ready_for_manual_mapping_review": True,
        },
    }


def _persistence_receipt() -> dict[str, object]:
    counts = {
        "reports": 1,
        "encounters": 14,
        "actors": 31,
        "participants": 31,
        "aura_events": 0,
        "rejects": 0,
    }
    source_batches = [
        {
            "mapping_id": "coa-encounter-detail-v1",
            "mapping_hash_verified": True,
            "raw_object_verified": True,
        },
        {
            "mapping_id": "coa-report-detail-v1",
            "mapping_hash_verified": True,
            "raw_object_verified": True,
        },
    ]
    return {
        "schema_version": 1,
        "persistence_kind": "observed_report_slice_selected_parser_persistence",
        "persistence_version": "selected-parser-persistence-v1",
        "persistence_run_id": "f" * 64,
        "source_batches": source_batches,
        "integrity_checks": {
            "mapping_hashes_verified": True,
            "raw_objects_verified": True,
            "transaction_committed": True,
        },
        "decision_boundary": {
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
        },
        "summary": {
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
            "persisted_counts": counts,
        },
    }


def _fixture(tmp_path: Path) -> tuple[Path, Path]:
    mapping_path = tmp_path / "mapping-review.json"
    persistence_path = tmp_path / "persistence.json"
    _write_json(mapping_path, _mapping_review())
    _write_json(persistence_path, _persistence_receipt())
    return mapping_path, persistence_path


def test_deep_review_emits_present_and_missing_candidate_scopes_without_scalars(tmp_path):
    mapping_path, persistence_path = _fixture(tmp_path)

    review = build_observed_combatants_info_deep_scope_review(mapping_path, persistence_path)

    assert review["summary"]["scope_candidate_count"] == 12
    assert review["summary"]["required_scope_count"] == 4
    assert review["summary"]["required_scope_present_count"] == 4
    assert review["summary"]["optional_scope_present_count"] == 3
    assert review["summary"]["optional_scope_missing_count"] == 5
    assert review["summary"]["selected_parser_persistence_verified"] is True
    assert review["summary"]["ready_for_manual_combatants_field_selection"] is True
    assert review["summary"]["contains_source_scalar_values"] is False
    assert review["decision_boundary"]["can_promote"] is False
    assert review["decision_boundary"]["combatants_info_enrichment_available"] is False
    assert review["decision_boundary"]["planner_scoring_allowed"] is False

    scopes = {row["scope"]: row for row in review["scopes"]}
    assert set(scopes) == {
        "/combatants/*/ci_resolved/player",
        "/combatants/*/ci_resolved/guild",
        "/combatants/*/ci_resolved/instance",
        "/combatants/*/ci_resolved/specialization",
        "/combatants/*/ci_resolved/specialization/talents",
        "/combatants/*/ci_resolved/specialization/resolved_ca_talent_ranks/*",
        "/combatants/*/ci_resolved/gear/*",
    }
    player_fields = {row["name"] for row in scopes["/combatants/*/ci_resolved/player"]["direct_fields"]}
    assert player_fields == {"class", "guid", "name", "realm"}
    assert scopes["/combatants/*/ci_resolved/player"]["required_scope"] is True
    assert scopes["/combatants/*/ci_resolved/gear/*"]["required_scope"] is False

    rendered = json.dumps(review)
    assert "PRIVATE PLAYER" not in rendered
    assert "source_scalar_values" in rendered


def test_deep_review_rejects_missing_required_player_scope(tmp_path):
    mapping_path, persistence_path = _fixture(tmp_path)
    mapping = json.loads(mapping_path.read_text(encoding="utf-8"))
    combatants = next(
        row for row in mapping["endpoints"] if row["endpoint_kind"] == "combatants_info"
    )
    combatants["field_shapes"] = [
        row
        for row in combatants["field_shapes"]
        if row["path"] != "/combatants/*/ci_resolved/player"
    ]
    _write_json(mapping_path, mapping)

    with pytest.raises(ValueError, match="required scope is missing"):
        build_observed_combatants_info_deep_scope_review(mapping_path, persistence_path)


def test_deep_review_rejects_uncommitted_persistence(tmp_path):
    mapping_path, persistence_path = _fixture(tmp_path)
    persistence = json.loads(persistence_path.read_text(encoding="utf-8"))
    persistence["summary"]["transaction_committed"] = False
    _write_json(persistence_path, persistence)

    with pytest.raises(ValueError, match="summary mismatch: transaction_committed"):
        build_observed_combatants_info_deep_scope_review(mapping_path, persistence_path)


def test_deep_review_rejects_combatants_hash_mismatch(tmp_path):
    mapping_path, persistence_path = _fixture(tmp_path)
    mapping = json.loads(mapping_path.read_text(encoding="utf-8"))
    combatants = next(
        row for row in mapping["endpoints"] if row["endpoint_kind"] == "combatants_info"
    )
    combatants["payload_hash"] = "0" * 64
    _write_json(mapping_path, mapping)

    with pytest.raises(ValueError, match="endpoint mismatch: payload_hash"):
        build_observed_combatants_info_deep_scope_review(mapping_path, persistence_path)
