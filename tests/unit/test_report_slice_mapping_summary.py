from __future__ import annotations

import json
from pathlib import Path

import pytest

from coa_workbench.collector.report_slice_mapping_summary import (
    summarize_observed_report_slice_mapping_review,
)


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _field_shapes(top_level: list[tuple[str, str]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = [
        {
            "path": "/",
            "occurrence_count": 1,
            "type_counts": {"object": 1},
            "nullable": False,
            "object": {"occurrence_count": 1},
        }
    ]
    for name, value_type in top_level:
        row: dict[str, object] = {
            "path": f"/{name}",
            "occurrence_count": 1,
            "type_counts": {value_type: 1},
            "nullable": False,
        }
        if value_type == "array":
            row["array"] = {"occurrence_count": 1, "total_items": 2}
        if value_type == "object":
            row["object"] = {"occurrence_count": 1}
        rows.append(row)
    return rows


def _candidate(
    path: str,
    *,
    keys: list[str],
    item_count: int = 2,
    object_count: int = 2,
    report: float = 0.0,
    encounter: float = 0.0,
    actor: float = 0.0,
    aura_event: float = 0.0,
) -> dict[str, object]:
    scores = {
        "report": report,
        "encounter": encounter,
        "actor": actor,
        "aura_event": aura_event,
    }
    return {
        "path": path,
        "item_count": item_count,
        "object_item_count": object_count,
        "observed_keys": keys,
        "entity_scores": scores,
        "matched_hints": {
            entity: [key for key in keys if key in {"title", "duration", "guid", "name", "timestamp", "spell_id"}]
            for entity in scores
        },
    }


def _endpoint(
    endpoint_kind: str,
    route: str,
    payload_hash: str,
    fingerprint: str,
    top_level: list[tuple[str, str]],
    candidates: list[dict[str, object]],
) -> tuple[dict[str, object], dict[str, object]]:
    field_shapes = _field_shapes(top_level)
    top_level_keys = sorted(name for name, _ in top_level)
    mapping = {
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
            "node_occurrence_count": 10,
            "numeric_map_path_count": 0,
            "nullable_path_count": 0,
            "array_path_count": sum(1 for _, value_type in top_level if value_type == "array"),
            "object_path_count": 1 + sum(
                1 for _, value_type in top_level if value_type == "object"
            ),
            "candidate_collection_count": len(candidates),
        },
    }
    structural = {
        "endpoint_kind": endpoint_kind,
        "route_template": route,
        "payload_hash": payload_hash,
        "schema_fingerprint": fingerprint,
        "bytes_uncompressed": 100,
        "payload_path": f"ascension_logs/{payload_hash}.json.gz",
        "http_status": 200,
        "content_type": "application/json",
        "top_level_kind": "object",
        "top_level_keys": top_level_keys,
        "candidate_collections": candidates,
        "archive_verification": {"payload_hash": True},
    }
    return mapping, structural


def _fixture(tmp_path: Path) -> tuple[Path, Path]:
    definitions = [
        _endpoint(
            "report_detail",
            "/api/reports/{template}",
            "1" * 64,
            "a" * 64,
            [("encounters", "array"), ("report", "object"), ("success", "boolean")],
            [
                _candidate(
                    "/encounters",
                    keys=["duration", "encounter_id"],
                    encounter=0.4,
                )
            ],
        ),
        _endpoint(
            "encounter_detail",
            "/api/reports/{template}/encounters/{template}",
            "2" * 64,
            "b" * 64,
            [("damage", "array"), ("encounter", "object"), ("success", "boolean")],
            [
                _candidate(
                    "/damage/0/targets",
                    keys=["guid", "name"],
                    actor=0.4,
                ),
                _candidate(
                    "/damage/1/targets",
                    keys=["guid", "name"],
                    actor=0.4,
                    item_count=3,
                    object_count=3,
                ),
            ],
        ),
        _endpoint(
            "combatants_info",
            "/api/reports/{template}/encounters/{template}/combatants-info",
            "3" * 64,
            "c" * 64,
            [("combatants", "array"), ("success", "boolean")],
            [
                _candidate(
                    "/combatants",
                    keys=["class", "guid", "name"],
                    actor=0.6,
                ),
                _candidate(
                    "/combatants/0/auras",
                    keys=["spell_id", "timestamp"],
                    aura_event=0.4,
                ),
                _candidate(
                    "/combatants/1/auras",
                    keys=["spell_id", "timestamp"],
                    aura_event=0.4,
                ),
            ],
        ),
    ]
    mapping_endpoints = [mapping for mapping, _ in definitions]
    structural_endpoints = [structural for _, structural in definitions]
    candidate_count = sum(
        endpoint["summary"]["candidate_collection_count"] for endpoint in mapping_endpoints
    )
    field_count = sum(endpoint["summary"]["field_path_count"] for endpoint in mapping_endpoints)

    mapping_path = tmp_path / "mapping-review.json"
    structural_path = tmp_path / "structural-review.json"
    _write_json(
        mapping_path,
        {
            "schema_version": 1,
            "review_kind": "observed_report_slice_mapping_review",
            "endpoints": mapping_endpoints,
            "summary": {
                "endpoint_count": 3,
                "raw_archive_count": 3,
                "field_path_count": field_count,
                "node_occurrence_count": 30,
                "numeric_map_path_count": 0,
                "nullable_path_count": 0,
                "array_path_count": 3,
                "object_path_count": 5,
                "candidate_collection_count": candidate_count,
                "all_archives_consistent": True,
                "contains_source_scalar_values": False,
                "semantic_verification_required": True,
                "normalization_allowed": False,
                "ready_for_manual_mapping_review": True,
            },
        },
    )
    _write_json(
        structural_path,
        {
            "schema_version": 1,
            "review_kind": "observed_report_slice_structural_review",
            "endpoints": structural_endpoints,
            "summary": {
                "raw_archive_count": 3,
                "candidate_collection_count": candidate_count,
                "all_archives_consistent": True,
                "contains_source_scalar_values": False,
                "semantic_verification_required": True,
                "normalization_allowed": False,
            },
        },
    )
    return mapping_path, structural_path


def test_summary_wildcards_indexes_and_keeps_candidate_boundary(tmp_path):
    mapping_path, structural_path = _fixture(tmp_path)

    summary = summarize_observed_report_slice_mapping_review(
        mapping_path,
        structural_path,
        max_candidates_per_entity=4,
    )

    assert summary["summary"]["endpoint_count"] == 3
    assert summary["summary"]["source_candidate_collection_count"] == 6
    assert summary["summary"]["aggregated_candidate_path_count"] == 4
    assert summary["summary"]["contains_source_scalar_values"] is False
    assert summary["summary"]["ready_for_manual_scope_selection"] is True
    assert summary["decision_boundary"] == {
        "status": "candidate",
        "automatic_scope_selection": False,
        "can_promote": False,
        "semantic_verification_required": True,
        "normalization_allowed": False,
    }

    endpoints = {endpoint["endpoint_kind"]: endpoint for endpoint in summary["endpoints"]}
    encounter_candidates = endpoints["encounter_detail"]["aggregated_candidate_collections"]
    assert len(encounter_candidates) == 1
    assert encounter_candidates[0]["path"] == "/damage/*/targets"
    assert encounter_candidates[0]["source_candidate_count"] == 2
    assert encounter_candidates[0]["item_count_total"] == 5

    combatants = endpoints["combatants_info"]
    assert combatants["candidate_shortlists"]["actor"][0]["path"] == "/combatants"
    assert combatants["candidate_shortlists"]["aura_event"][0]["path"] == (
        "/combatants/*/auras"
    )
    assert {field["name"] for field in combatants["top_level_fields"]} == {
        "combatants",
        "success",
    }


def test_summary_rejects_payload_hash_mismatch(tmp_path):
    mapping_path, structural_path = _fixture(tmp_path)
    structural = json.loads(structural_path.read_text(encoding="utf-8"))
    structural["endpoints"][0]["payload_hash"] = "f" * 64
    _write_json(structural_path, structural)

    with pytest.raises(ValueError, match="payload_hash do not match"):
        summarize_observed_report_slice_mapping_review(mapping_path, structural_path)


def test_summary_rejects_candidate_count_mismatch(tmp_path):
    mapping_path, structural_path = _fixture(tmp_path)
    mapping = json.loads(mapping_path.read_text(encoding="utf-8"))
    mapping["endpoints"][0]["summary"]["candidate_collection_count"] += 1
    _write_json(mapping_path, mapping)

    with pytest.raises(ValueError, match="candidate collection count mismatch"):
        summarize_observed_report_slice_mapping_review(mapping_path, structural_path)


def test_summary_rejects_privacy_gate_change(tmp_path):
    mapping_path, structural_path = _fixture(tmp_path)
    mapping = json.loads(mapping_path.read_text(encoding="utf-8"))
    mapping["summary"]["contains_source_scalar_values"] = True
    _write_json(mapping_path, mapping)

    with pytest.raises(ValueError, match="privacy gate"):
        summarize_observed_report_slice_mapping_review(mapping_path, structural_path)


def test_summary_rejects_non_positive_shortlist_limit(tmp_path):
    mapping_path, structural_path = _fixture(tmp_path)

    with pytest.raises(ValueError, match="must be positive"):
        summarize_observed_report_slice_mapping_review(
            mapping_path,
            structural_path,
            max_candidates_per_entity=0,
        )
