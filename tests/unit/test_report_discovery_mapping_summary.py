from __future__ import annotations

import json
from pathlib import Path

import pytest

from coa_workbench.collector.report_discovery_mapping_summary import (
    summarize_report_discovery_mapping_review,
)


def _write_reviews(tmp_path: Path) -> tuple[Path, Path]:
    payload_hash = "a" * 64
    fingerprint = "b" * 64
    mapping = {
        "schema_version": 1,
        "review_kind": "report_discovery_mapping_review",
        "payload": {
            "payload_hash": payload_hash,
            "schema_fingerprint": fingerprint,
            "top_level_kind": "object",
            "top_level_keys": ["pagination", "reports", "success"],
            "review_status": "candidate",
            "field_shapes": [
                {
                    "path": "/",
                    "occurrence_count": 1,
                    "type_counts": {"object": 1},
                    "nullable": False,
                },
                {
                    "path": "/reports",
                    "occurrence_count": 1,
                    "type_counts": {"array": 1},
                    "nullable": False,
                    "array": {
                        "occurrence_count": 1,
                        "total_items": 2,
                        "min_length": 2,
                        "max_length": 2,
                        "item_type_counts": {"object": 2},
                    },
                },
                {
                    "path": "/reports/*",
                    "occurrence_count": 2,
                    "type_counts": {"object": 2},
                    "nullable": False,
                    "object": {
                        "occurrence_count": 2,
                        "key_mode_counts": {"fixed_fields": 2},
                        "fixed_fields": {
                            "occurrence_count": 2,
                            "observed_keys": ["id", "locations", "title"],
                            "required_keys": ["id", "locations", "title"],
                        },
                    },
                },
                {
                    "path": "/reports/*/id",
                    "occurrence_count": 2,
                    "type_counts": {"integer": 2},
                    "nullable": False,
                },
                {
                    "path": "/reports/*/title",
                    "occurrence_count": 2,
                    "type_counts": {"null": 1, "string": 1},
                    "nullable": True,
                },
                {
                    "path": "/reports/*/locations",
                    "occurrence_count": 2,
                    "type_counts": {"array": 2},
                    "nullable": False,
                    "array": {
                        "occurrence_count": 2,
                        "total_items": 2,
                        "min_length": 1,
                        "max_length": 1,
                        "item_type_counts": {"string": 2},
                    },
                },
            ],
        },
        "summary": {
            "archive_verified": 1,
            "field_path_count": 6,
            "node_occurrence_count": 12,
            "numeric_map_path_count": 0,
            "contains_source_scalar_values": False,
        },
    }
    structural = {
        "schema_version": 1,
        "review_kind": "report_discovery_structural_review",
        "response": {
            "payload_hash": payload_hash,
            "schema_fingerprint": fingerprint,
            "candidate_collections": [
                {
                    "path": "/reports",
                    "item_count": 2,
                    "object_item_count": 2,
                    "observed_keys": ["id", "locations", "title"],
                    "entity_scores": {
                        "report": 0.4,
                        "encounter": 0.0,
                        "actor": 0.0,
                        "aura_event": 0.0,
                    },
                },
                {
                    "path": "/reports/0/locations",
                    "item_count": 1,
                    "object_item_count": 0,
                    "observed_keys": [],
                    "entity_scores": {
                        "report": 0.0,
                        "encounter": 0.0,
                        "actor": 0.0,
                        "aura_event": 0.0,
                    },
                },
            ],
        },
        "summary": {"contains_source_scalar_values": False},
    }
    mapping_path = tmp_path / "mapping.json"
    structural_path = tmp_path / "structural.json"
    mapping_path.write_text(json.dumps(mapping), encoding="utf-8")
    structural_path.write_text(json.dumps(structural), encoding="utf-8")
    return mapping_path, structural_path


def test_summary_selects_unique_report_candidate_and_handles_optional_shapes(tmp_path):
    mapping_path, structural_path = _write_reviews(tmp_path)

    result = summarize_report_discovery_mapping_review(mapping_path, structural_path)

    decision = result["candidate_decision"]
    assert decision["unique_report_like_collection"] is True
    assert decision["report_collection_path"] == "/reports"
    assert decision["report_item_selector"] == "/reports/*"
    assert decision["can_promote"] is False

    item = result["report_item_shape"]
    assert item["occurrence_count"] == 2
    assert item["required_keys"] == ["id", "locations", "title"]
    fields = {field["name"]: field for field in item["fields"]}
    assert fields["id"]["types"] == ["integer"]
    assert fields["title"]["nullable"] is True
    assert fields["title"]["observed_on_all_items"] is True

    arrays = {entry["path"]: entry for entry in result["array_paths"]}
    assert arrays["/reports"]["item_type_counts"] == {"object": 2}
    assert arrays["/reports/*/locations"]["item_type_counts"] == {"string": 2}
    assert result["nullable_paths"] == [
        {
            "path": "/reports/*/title",
            "occurrence_count": 2,
            "type_counts": {"null": 1, "string": 1},
        }
    ]
    assert result["summary"]["contains_source_scalar_values"] is False


def test_summary_rejects_hash_mismatch(tmp_path):
    mapping_path, structural_path = _write_reviews(tmp_path)
    structural = json.loads(structural_path.read_text(encoding="utf-8"))
    structural["response"]["payload_hash"] = "c" * 64
    structural_path.write_text(json.dumps(structural), encoding="utf-8")

    with pytest.raises(ValueError, match="payload hashes do not match"):
        summarize_report_discovery_mapping_review(mapping_path, structural_path)
