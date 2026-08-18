from __future__ import annotations

import json
from pathlib import Path

import pytest

from coa_workbench.collector import RawArchive
from coa_workbench.collector.armory_mapping_review import build_armory_mapping_review


def _manifest(tmp_path: Path) -> tuple[Path, Path]:
    raw_root = tmp_path / "raw"
    archive = RawArchive(raw_root)
    payloads = {
        "character": {
            "success": True,
            "capture": {"id": 156120, "name": "PrivateCharacter"},
            "ci_resolved": {
                "gear": {
                    "1": {"item_id": 100, "slot": 1, "resolved_enchant": None},
                    "10": {"item_id": 200, "slot": 10, "resolved_enchant": {"id": 300}},
                },
                "specialization": {
                    "talents": {
                        "trees": {
                            "felsworn": {
                                "talents": [
                                    {"talent_id": 1, "name": "Hidden Talent", "rank": 1},
                                    {"talent_id": 2, "name": "Another Hidden Talent", "rank": None},
                                ]
                            }
                        }
                    }
                },
            },
            "stats_summary": {
                "primary": [
                    {"key": "strength", "label": "Strength", "value": 100},
                    {"key": "stamina", "label": "Stamina", "value": 200},
                ]
            },
        },
        "talent_grid": {
            "success": True,
            "class_name": "Felsworn",
            "trees": [
                {
                    "tree_slug": "felsworn",
                    "talents": [
                        {
                            "talent_id": 1,
                            "spell_id": 2,
                            "name": "Hidden Talent",
                            "rank_spell_ids": [2, 3],
                            "lock_rules": [],
                        }
                    ],
                }
            ],
        },
    }
    endpoints = {}
    for endpoint_kind, payload in payloads.items():
        body = json.dumps(payload).encode("utf-8")
        capture = archive.capture_bytes(
            body,
            source_code="coa_ascension_logs",
            endpoint_code=f"armory_api_{endpoint_kind}",
            request_key=f"GET:/api/armory/{endpoint_kind}",
            http_status=200,
            content_type="application/json",
        )
        endpoints[endpoint_kind] = {
            "state": "captured",
            "route": f"https://coa.ascensionlogs.gg/api/armory/{endpoint_kind}",
            "status": 200,
            "content_type": "application/json",
            "capture": {
                "payload_hash": capture.payload_hash,
                "schema_fingerprint": capture.schema_fingerprint,
                "bytes_uncompressed": capture.bytes_uncompressed,
                "payload_path": Path(capture.payload_path).relative_to(raw_root).as_posix(),
            },
        }
    manifest = {
        "schema_version": 1,
        "capture_mode": "endpoint_isolated_armory_api",
        "http_profile_version": "coa-fetch-context-v1",
        "subject": {"character_id": "156120", "class_slug": "felsworn"},
        "endpoint_order": ["character", "talent_grid"],
        "endpoints": endpoints,
    }
    path = tmp_path / "capture.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    return path, raw_root


def test_mapping_review_contains_types_without_source_scalar_values(tmp_path):
    manifest_path, raw_root = _manifest(tmp_path)

    result = build_armory_mapping_review(manifest_path, raw_root=raw_root)

    assert result["schema_version"] == 2
    assert result["summary"]["endpoint_count"] == 2
    assert result["summary"]["contains_source_scalar_values"] is False
    assert result["summary"]["ready_for_manual_mapping_review"] is True
    character = result["endpoints"][0]
    shape_by_path = {item["path"]: item for item in character["field_shapes"]}
    assert shape_by_path["/ci_resolved/specialization/talents/trees/felsworn/talents/*/rank"][
        "nullable"
    ] is True
    assert shape_by_path["/stats_summary/primary/*"]["object"]["fixed_fields"][
        "required_keys"
    ] == ["key", "label", "value"]
    serialized = json.dumps(result)
    assert "PrivateCharacter" not in serialized
    assert "Hidden Talent" not in serialized
    assert "Strength" not in serialized


def test_mapping_review_collapses_numeric_object_keys(tmp_path):
    manifest_path, raw_root = _manifest(tmp_path)

    result = build_armory_mapping_review(manifest_path, raw_root=raw_root)

    character = result["endpoints"][0]
    shape_by_path = {item["path"]: item for item in character["field_shapes"]}
    assert "/ci_resolved/gear/1" not in shape_by_path
    assert "/ci_resolved/gear/10" not in shape_by_path
    assert shape_by_path["/ci_resolved/gear"]["object"]["numeric_map"] == {
        "occurrence_count": 1,
        "total_entries": 2,
        "min_entries": 2,
        "max_entries": 2,
    }
    assert shape_by_path["/ci_resolved/gear/*/item_id"]["type_counts"] == {"integer": 2}
    assert shape_by_path["/ci_resolved/gear/*/resolved_enchant"]["type_counts"] == {
        "null": 1,
        "object": 1,
    }
    assert character["summary"]["numeric_map_path_count"] == 1


def test_mapping_review_rejects_too_small_node_budget(tmp_path):
    manifest_path, raw_root = _manifest(tmp_path)

    with pytest.raises(ValueError, match="exceeded max_nodes"):
        build_armory_mapping_review(manifest_path, raw_root=raw_root, max_nodes=1)
