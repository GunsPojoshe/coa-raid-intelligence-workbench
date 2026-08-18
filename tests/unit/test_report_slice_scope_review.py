from __future__ import annotations

import json
from pathlib import Path

import pytest

from coa_workbench.collector.report_slice_scope_review import (
    build_observed_report_slice_scope_review,
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
    required_keys: list[str] | None = None,
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
                "required_keys": required_keys if required_keys is not None else keys,
            },
        }
    if value_type == "array":
        row["array"] = {
            "occurrence_count": occurrences,
            "total_items": 2,
            "min_length": 2,
            "max_length": 2,
            "item_type_counts": {"object": 2},
        }
    return row


def _endpoint(
    endpoint_kind: str,
    route: str,
    payload_hash: str,
    fingerprint: str,
    top_level_keys: list[str],
    field_shapes: list[dict[str, object]],
) -> dict[str, object]:
    return {
        "endpoint_kind": endpoint_kind,
        "route_template": route,
        "payload_hash": payload_hash,
        "schema_fingerprint": fingerprint,
        "top_level_kind": "object",
        "top_level_keys": top_level_keys,
        "review_status": "candidate",
        "provenance_type": "upstream_derived",
        "scope": "/",
        "field_shapes": field_shapes,
        "summary": {
            "field_path_count": len(field_shapes),
            "node_occurrence_count": 100,
            "numeric_map_path_count": 0,
            "nullable_path_count": sum(1 for row in field_shapes if row["nullable"]),
            "array_path_count": sum(1 for row in field_shapes if "array" in row),
            "object_path_count": sum(1 for row in field_shapes if "object" in row),
            "candidate_collection_count": 1,
        },
    }


def _fixture(tmp_path: Path) -> tuple[Path, Path]:
    report_shapes = [
        _shape("/", "object", observed_keys=["encounters", "report", "success"]),
        _shape("/report", "object", observed_keys=["id", "title"]),
        _shape("/report/id", "integer"),
        _shape("/report/title", "string"),
        _shape("/encounters", "array"),
        _shape(
            "/encounters/*",
            "object",
            occurrences=2,
            observed_keys=["id", "name", "start_time"],
        ),
        _shape("/encounters/*/id", "integer", occurrences=2),
        _shape("/encounters/*/name", "string", occurrences=2),
        _shape("/encounters/*/start_time", "integer", occurrences=2),
        _shape("/success", "boolean"),
    ]
    encounter_shapes = [
        _shape(
            "/",
            "object",
            observed_keys=["character_stats", "encounter", "success"],
        ),
        _shape("/encounter", "object", observed_keys=["id", "name", "success"]),
        _shape("/encounter/id", "integer"),
        _shape("/encounter/name", "string"),
        _shape("/encounter/success", "boolean"),
        _shape("/character_stats", "array"),
        _shape(
            "/character_stats/*",
            "object",
            occurrences=2,
            observed_keys=["character_id", "class", "name", "spec"],
        ),
        _shape("/character_stats/*/character_id", "integer", occurrences=2),
        _shape("/character_stats/*/class", "string", occurrences=2),
        _shape("/character_stats/*/name", "string", occurrences=2),
        _shape("/character_stats/*/spec", "string", occurrences=1),
        _shape("/success", "boolean"),
    ]
    combatant_shapes = [
        _shape("/", "object", observed_keys=["combatants", "success"]),
        _shape("/combatants", "array"),
        _shape(
            "/combatants/*",
            "object",
            occurrences=2,
            observed_keys=["character_id", "ci_resolved", "source"],
        ),
        _shape("/combatants/*/character_id", "integer", occurrences=2),
        _shape(
            "/combatants/*/ci_resolved",
            "object",
            occurrences=2,
            observed_keys=["class", "name", "specialization"],
        ),
        _shape("/combatants/*/ci_resolved/class", "string", occurrences=2),
        _shape("/combatants/*/ci_resolved/name", "string", occurrences=2),
        _shape(
            "/combatants/*/ci_resolved/specialization",
            "object",
            occurrences=2,
            observed_keys=["name", "slug"],
        ),
        _shape(
            "/combatants/*/ci_resolved/specialization/name",
            "string",
            occurrences=2,
        ),
        _shape(
            "/combatants/*/ci_resolved/specialization/slug",
            "string",
            occurrences=1,
        ),
        _shape("/combatants/*/source", "string", occurrences=2),
        _shape("/success", "boolean"),
    ]

    endpoints = [
        _endpoint(
            "report_detail",
            "/api/reports/{template}",
            "1" * 64,
            "a" * 64,
            ["encounters", "report", "success"],
            report_shapes,
        ),
        _endpoint(
            "encounter_detail",
            "/api/reports/{template}/encounters/{template}",
            "2" * 64,
            "b" * 64,
            ["character_stats", "encounter", "success"],
            encounter_shapes,
        ),
        _endpoint(
            "combatants_info",
            "/api/reports/{template}/encounters/{template}/combatants-info",
            "3" * 64,
            "c" * 64,
            ["combatants", "success"],
            combatant_shapes,
        ),
    ]
    mapping_path = tmp_path / "mapping-review.json"
    summary_path = tmp_path / "mapping-summary.json"
    _write_json(
        mapping_path,
        {
            "schema_version": 1,
            "review_kind": "observed_report_slice_mapping_review",
            "endpoints": endpoints,
            "summary": {
                "endpoint_count": 3,
                "raw_archive_count": 3,
                "field_path_count": sum(len(row["field_shapes"]) for row in endpoints),
                "node_occurrence_count": 300,
                "numeric_map_path_count": 0,
                "nullable_path_count": 0,
                "array_path_count": 3,
                "object_path_count": 9,
                "candidate_collection_count": 3,
                "all_archives_consistent": True,
                "contains_source_scalar_values": False,
                "semantic_verification_required": True,
                "normalization_allowed": False,
                "ready_for_manual_mapping_review": True,
            },
        },
    )
    summary_endpoints = [
        {
            key: endpoint[key]
            for key in (
                "endpoint_kind",
                "route_template",
                "payload_hash",
                "schema_fingerprint",
                "top_level_kind",
                "top_level_keys",
                "review_status",
                "scope",
            )
        }
        for endpoint in endpoints
    ]
    _write_json(
        summary_path,
        {
            "schema_version": 1,
            "summary_kind": "observed_report_slice_mapping_summary",
            "endpoints": summary_endpoints,
            "decision_boundary": {
                "status": "candidate",
                "automatic_scope_selection": False,
                "can_promote": False,
                "semantic_verification_required": True,
                "normalization_allowed": False,
            },
            "summary": {
                "endpoint_count": 3,
                "field_path_count": sum(len(row["field_shapes"]) for row in endpoints),
                "node_occurrence_count": 300,
                "source_candidate_collection_count": 3,
                "aggregated_candidate_path_count": 3,
                "shortlist_row_count": 3,
                "all_archives_consistent": True,
                "contains_source_scalar_values": False,
                "semantic_verification_required": True,
                "normalization_allowed": False,
                "ready_for_manual_scope_selection": True,
            },
        },
    )
    return mapping_path, summary_path


def test_scope_review_emits_explicit_candidate_scopes_without_scalar_values(tmp_path):
    mapping_path, summary_path = _fixture(tmp_path)

    review = build_observed_report_slice_scope_review(mapping_path, summary_path)

    assert review["summary"]["endpoint_count"] == 3
    assert review["summary"]["scope_candidate_count"] == 7
    assert review["summary"]["contains_source_scalar_values"] is False
    assert review["summary"]["ready_for_manual_field_selection"] is True
    assert review["decision_boundary"] == {
        "status": "candidate",
        "automatic_scope_selection": False,
        "automatic_field_selection": False,
        "can_promote": False,
        "semantic_verification_required": True,
        "normalization_allowed": False,
    }

    scopes = {(row["endpoint_kind"], row["scope"]): row for row in review["scopes"]}
    participant = scopes[("encounter_detail", "/character_stats/*")]
    participant_fields = {row["name"]: row for row in participant["direct_fields"]}
    assert set(participant_fields) == {"character_id", "class", "name", "spec"}
    assert participant_fields["spec"]["observed_on_all_scope_occurrences"] is False

    specialization = scopes[
        ("combatants_info", "/combatants/*/ci_resolved/specialization")
    ]
    specialization_fields = {row["name"]: row for row in specialization["direct_fields"]}
    assert set(specialization_fields) == {"name", "slug"}
    assert specialization_fields["slug"]["observed_on_all_scope_occurrences"] is False

    rendered = json.dumps(review)
    assert "Private Player" not in rendered
    assert "987654" not in rendered


def test_scope_review_rejects_missing_required_scope(tmp_path):
    mapping_path, summary_path = _fixture(tmp_path)
    mapping = json.loads(mapping_path.read_text(encoding="utf-8"))
    combatants = next(
        row for row in mapping["endpoints"] if row["endpoint_kind"] == "combatants_info"
    )
    combatants["field_shapes"] = [
        row
        for row in combatants["field_shapes"]
        if row["path"] != "/combatants/*/ci_resolved/specialization"
    ]
    _write_json(mapping_path, mapping)

    with pytest.raises(ValueError, match="required scope is missing"):
        build_observed_report_slice_scope_review(mapping_path, summary_path)


def test_scope_review_rejects_summary_hash_mismatch(tmp_path):
    mapping_path, summary_path = _fixture(tmp_path)
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary["endpoints"][0]["payload_hash"] = "f" * 64
    _write_json(summary_path, summary)

    with pytest.raises(ValueError, match="payload_hash do not match"):
        build_observed_report_slice_scope_review(mapping_path, summary_path)


def test_scope_review_rejects_automatic_scope_selection(tmp_path):
    mapping_path, summary_path = _fixture(tmp_path)
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary["decision_boundary"]["automatic_scope_selection"] = True
    _write_json(summary_path, summary)

    with pytest.raises(ValueError, match="automatic scope selection"):
        build_observed_report_slice_scope_review(mapping_path, summary_path)
