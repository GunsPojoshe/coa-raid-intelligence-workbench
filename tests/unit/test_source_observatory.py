from __future__ import annotations

import json

import pytest

from coa_workbench.collector.source_observatory import (
    ReviewedGetContract,
    build_get_url,
    diff_schema_snapshots,
    snapshot_json_payload,
)


def _contract() -> ReviewedGetContract:
    return ReviewedGetContract(
        source_code="coa_logs",
        endpoint_code="guild_progression_rankings",
        base_url="https://coa.ascensionlogs.gg",
        route_template="/api/guilds/progression/rankings/{bossId}",
        parameter_keys=("phaseId", "realm"),
        auth_state="none",
        discovery_source="archived_spa_review",
        review_state="verified",
    )


def test_reviewed_get_url_rejects_unreviewed_query_keys() -> None:
    contract = _contract()
    assert build_get_url(
        contract,
        path_params={"bossId": 42},
        query_params={"phaseId": 3, "realm": "coa"},
    ) == "https://coa.ascensionlogs.gg/api/guilds/progression/rankings/42?phaseId=3&realm=coa"

    with pytest.raises(ValueError, match="not in reviewed contract"):
        build_get_url(
            contract,
            path_params={"bossId": 42},
            query_params={"unknown": "value"},
        )


def test_schema_diff_detects_new_field_type_and_dimension_value() -> None:
    previous = snapshot_json_payload(
        json.dumps(
            {
                "rows": [
                    {"bossId": 1, "name": "A", "score": 10},
                    {"bossId": 2, "name": "B", "score": 12},
                ]
            }
        ).encode(),
        dimension_keys=("bossId",),
    )
    current = snapshot_json_payload(
        json.dumps(
            {
                "rows": [
                    {"bossId": 1, "name": "A", "score": "10", "difficulty": "heroic"},
                    {"bossId": 3, "name": "C", "score": "15", "difficulty": "heroic"},
                ]
            }
        ).encode(),
        dimension_keys=("bossId",),
    )

    changes = diff_schema_snapshots(previous, current)
    by_type = {}
    for change in changes:
        by_type.setdefault(change.change_type, []).append(change)

    assert "schema_changed" in by_type
    assert any(change.subject_path == "/rows/*/difficulty" for change in by_type["field_added"])
    assert any(change.subject_path == "/rows/*/score" for change in by_type["field_type_changed"])
    assert by_type["new_dimension_value"][0].subject_path == "dimension:bossId"
    assert by_type["new_dimension_value"][0].current_value == ["3"]


def test_truncated_snapshot_does_not_claim_removed_fields() -> None:
    previous = snapshot_json_payload(
        json.dumps({"rows": [{"id": 1, "legacy": True}]}).encode(),
        max_array_items=10,
    )
    current = snapshot_json_payload(
        json.dumps({"rows": [{"id": 1}, {"id": 2}]}).encode(),
        max_array_items=1,
    )
    assert current.scan_truncated is True

    changes = diff_schema_snapshots(previous, current)
    assert not any(change.change_type == "field_removed" for change in changes)
