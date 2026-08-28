from __future__ import annotations

import json
from pathlib import Path

import duckdb
import pytest

from coa_workbench.collector.source_field_correspondence import (
    build_source_field_correspondence_review_from_inputs,
    load_server_schema_paths,
)


def _upstream_review() -> dict[str, object]:
    return {
        "source": {
            "source_code": "ascension_logs_companion",
            "revision": "abc1234",
        },
        "field_lineage": [
            {
                "record_code": "ci",
                "field_path": "instance.difficulty_index",
                "source_kind": "api_binding",
                "source_identifier": "GetInstanceInfo",
                "source_file": "Capture/LocalScan.lua",
                "line": 10,
            },
            {
                "record_code": "ci",
                "field_path": "instance.map_id",
                "source_kind": "api_binding",
                "source_identifier": "GetInstanceInfo",
                "source_file": "Capture/LocalScan.lua",
                "line": 11,
            },
            {
                "record_code": "ci",
                "field_path": "player.name",
                "source_kind": "api_binding",
                "source_identifier": "UnitName",
                "source_file": "Capture/LocalScan.lua",
                "line": 2,
            },
        ],
    }


def test_structural_bridge_finds_exact_suffix_without_promoting_semantics() -> None:
    review = build_source_field_correspondence_review_from_inputs(
        upstream_review=_upstream_review(),
        server_path_types={
            "report_combatants_roster_api": {
                "/characters/*/instance/difficulty_index": ["integer"],
                "/characters/*/instance/map_id": ["integer"],
            },
            "report_detail_api": {
                "/report/difficulty": ["string"],
            },
        },
    )

    assert review["summary"] == {
        "upstream_focus_field_count": 2,
        "server_focus_field_count": 3,
        "exact_suffix_candidate_count": 2,
        "leaf_name_candidate_count": 0,
    }
    candidates = review["correspondence_candidates"]
    assert {item["upstream_field_path"] for item in candidates} == {
        "instance.difficulty_index",
        "instance.map_id",
    }
    assert all(item["match_kind"] == "exact_suffix" for item in candidates)
    assert review["interpretation"]["runtime_value_equivalence_verified"] is False
    assert review["interpretation"]["backend_transformation_semantics_verified"] is False
    assert review["public_release_safe"] is True


def test_server_paths_publish_only_focus_suffix_not_private_prefix() -> None:
    review = build_source_field_correspondence_review_from_inputs(
        upstream_review=_upstream_review(),
        server_path_types={
            "report_combatants_roster_api": {
                "/characters/PrivatePlayerName/instance/difficulty_index": ["integer"],
            },
        },
    )

    rendered = json.dumps(review, sort_keys=True)
    assert "PrivatePlayerName" not in rendered
    assert review["server_focus_fields"] == [
        {
            "endpoint_code": "report_combatants_roster_api",
            "focused_path_suffix": "instance.difficulty_index",
            "json_types": ["integer"],
        }
    ]
    assert review["privacy"]["full_server_paths_included"] is False


def test_leaf_name_match_is_kept_weaker_than_exact_suffix() -> None:
    review = build_source_field_correspondence_review_from_inputs(
        upstream_review=_upstream_review(),
        server_path_types={
            "report_detail_api": {
                "/difficulty_index": ["integer"],
            },
        },
    )

    assert review["summary"]["exact_suffix_candidate_count"] == 0
    assert review["summary"]["leaf_name_candidate_count"] == 1
    assert review["correspondence_candidates"][0]["match_kind"] == "leaf_name"


def test_load_server_schema_paths_merges_snapshots(tmp_path: Path) -> None:
    database = tmp_path / "coa.duckdb"
    with duckdb.connect(str(database)) as connection:
        connection.execute(
            """
            CREATE TABLE source_schema_snapshot (
                snapshot_id VARCHAR,
                endpoint_code VARCHAR,
                observed_at TIMESTAMP,
                path_types_json VARCHAR
            )
            """
        )
        connection.execute(
            "INSERT INTO source_schema_snapshot VALUES (?, ?, CURRENT_TIMESTAMP, ?)",
            [
                "one",
                "report_combatants_roster_api",
                json.dumps({"/characters/*/instance/difficulty_index": ["integer"]}),
            ],
        )
        connection.execute(
            "INSERT INTO source_schema_snapshot VALUES (?, ?, CURRENT_TIMESTAMP, ?)",
            [
                "two",
                "report_combatants_roster_api",
                json.dumps(
                    {
                        "/characters/*/instance/difficulty_index": ["null", "integer"],
                        "/characters/*/instance/map_id": ["integer"],
                    }
                ),
            ],
        )

    paths, counts = load_server_schema_paths(
        database,
        endpoint_codes=["report_combatants_roster_api"],
    )

    assert counts == {"report_combatants_roster_api": 2}
    assert paths["report_combatants_roster_api"][
        "/characters/*/instance/difficulty_index"
    ] == ("integer", "null")
    assert paths["report_combatants_roster_api"]["/characters/*/instance/map_id"] == (
        "integer",
    )


def test_correspondence_rejects_unsafe_endpoint_code() -> None:
    with pytest.raises(ValueError, match="public-safe"):
        build_source_field_correspondence_review_from_inputs(
            upstream_review=_upstream_review(),
            server_path_types={
                "private/player": {"/instance/difficulty_index": ["integer"]}
            },
        )
