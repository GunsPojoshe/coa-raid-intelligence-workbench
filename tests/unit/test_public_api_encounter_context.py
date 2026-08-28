from __future__ import annotations

import json

import pytest

from coa_workbench.analytics.public_api_encounter_context import (
    EncounterContextStatus,
    parse_encounter_reference_url,
    resolve_public_api_boss_id,
)


def test_encounter_reference_accepts_exact_report_encounter_shape() -> None:
    reference = parse_encounter_reference_url(
        "https://coa.ascensionlogs.gg/reports/12345/encounters?encounters=67890"
    )
    assert reference.report_id == 12345
    assert reference.encounter_id == 67890


@pytest.mark.parametrize(
    "value",
    [
        "http://coa.ascensionlogs.gg/reports/1/encounters?encounters=2",
        "https://example.com/reports/1/encounters?encounters=2",
        "https://coa.ascensionlogs.gg/reports/nope/encounters?encounters=2",
        "https://coa.ascensionlogs.gg/reports/1/encounters",
        "https://coa.ascensionlogs.gg/reports/1/encounters?encounters=2&encounters=3",
    ],
)
def test_encounter_reference_fails_closed(value: str) -> None:
    with pytest.raises(ValueError):
        parse_encounter_reference_url(value)


def test_boss_binding_requires_one_exact_name_location_match() -> None:
    payload = {
        "success": True,
        "bosses": [
            {"boss_id": 101, "name": "Example Boss", "location": "Example Raid"},
            {"boss_id": 102, "name": "Example Boss", "location": "Other Raid"},
        ],
    }
    assert (
        resolve_public_api_boss_id(
            payload,
            boss_name="Example Boss",
            location="Example Raid",
        )
        == 101
    )

    with pytest.raises(ValueError, match="exactly one exact"):
        resolve_public_api_boss_id(
            payload,
            boss_name="example boss",
            location="Example Raid",
        )


def test_boss_binding_rejects_ambiguous_catalog_match() -> None:
    payload = {
        "success": True,
        "bosses": [
            {"boss_id": 101, "name": "Example Boss", "location": "Example Raid"},
            {"boss_id": 102, "name": "Example Boss", "location": "Example Raid"},
        ],
    }
    with pytest.raises(ValueError, match="found 2"):
        resolve_public_api_boss_id(
            payload,
            boss_name="Example Boss",
            location="Example Raid",
        )


def test_public_encounter_summary_is_scalar_safe() -> None:
    status = EncounterContextStatus(
        required_slice_count=4,
        covered_slice_indexes=(0, 1, 2, 3),
        missing_slice_indexes=(),
        selected_batch_count=4,
        aggregate_class_count=60,
        aggregate_spec_record_count=162,
        aggregate_percentile_value_count=2106,
    )
    public = status.public_summary()
    assert public["complete"] is True
    assert public["encounter_scoped"] is True
    assert public["bounded_capture_plan"] is True
    assert public["bulk_dataset_mode"] is False
    assert public["planner_scoring_allowed"] is False
    assert public["boss_ids_included"] is False
    assert public["location_values_included"] is False
    assert public["difficulty_values_included"] is False

    rendered = json.dumps(public, sort_keys=True)
    for private_value in (
        "Private Boss",
        "Private Raid",
        "heroic",
        "avg_dps",
        "support",
        "67890",
    ):
        assert private_value not in rendered
