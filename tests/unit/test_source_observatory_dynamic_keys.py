from __future__ import annotations

import json

from coa_workbench.collector.source_observatory import (
    diff_schema_snapshots,
    snapshot_json_payload,
)


def test_numeric_object_keys_are_wildcarded_in_source_schema_paths() -> None:
    first = snapshot_json_payload(
        json.dumps(
            {
                "series": {
                    "123": [{"amount": 1, "effective": 2}],
                    "456": [{"amount": 3}],
                }
            }
        ).encode()
    )
    second = snapshot_json_payload(
        json.dumps(
            {
                "series": {
                    "999": [{"amount": 8}],
                    "1000": [{"amount": 7, "effective": 6}],
                }
            }
        ).encode()
    )

    assert first.schema_fingerprint == second.schema_fingerprint
    assert "/series/{integer-key}/*/amount" in first.path_types
    assert "/series/123/*/amount" not in first.path_types
    assert diff_schema_snapshots(first, second) == ()


def test_fixed_field_change_still_produces_source_schema_change() -> None:
    first = snapshot_json_payload(
        json.dumps({"series": {"123": [{"amount": 1}]}}).encode()
    )
    second = snapshot_json_payload(
        json.dumps({"series": {"999": [{"amount": 1, "new_field": True}]}}).encode()
    )

    changes = diff_schema_snapshots(first, second)
    assert any(change.change_type == "schema_changed" for change in changes)
    assert any(
        change.change_type == "field_added"
        and change.subject_path == "/series/{integer-key}/*/new_field"
        for change in changes
    )
