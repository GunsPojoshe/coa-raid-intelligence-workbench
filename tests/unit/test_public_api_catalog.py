import json
from pathlib import Path

import pytest

from coa_workbench.collector.public_api_catalog import (
    build_public_api_catalog_review,
    load_latest_public_api_payload,
    parse_public_api_phases,
    select_current_phase_number,
)
from coa_workbench.collector.raw_archive import RawArchive


def _phases_payload() -> dict[str, object]:
    return {
        "success": True,
        "phases": [
            {
                "phase_number": 1,
                "is_active": False,
                "end_date": "2026-01-01T00:00:00Z",
                "locations": [
                    {
                        "location": "Old Raid",
                        "is_main": True,
                        "track_progression": True,
                        "is_world_boss": False,
                    }
                ],
            },
            {
                "phase_number": 2,
                "is_active": True,
                "end_date": None,
                "locations": [
                    {
                        "location": "Current Raid",
                        "is_main": True,
                        "track_progression": True,
                        "is_world_boss": False,
                    },
                    {
                        "location": "World Bosses",
                        "is_main": False,
                        "track_progression": False,
                        "is_world_boss": True,
                    },
                ],
            },
        ],
    }


def _bosses_payload() -> dict[str, object]:
    return {
        "success": True,
        "count": 2,
        "bosses": [
            {
                "boss_id": 101,
                "name": "Boss One",
                "location": "Current Raid",
                "display_order": 1,
                "instance_type": "raid",
            },
            {
                "boss_id": 102,
                "name": "Boss Two",
                "location": None,
                "display_order": None,
                "instance_type": None,
            },
        ],
    }


def test_catalog_review_selects_one_current_phase_without_publishing_values() -> None:
    phases = _phases_payload()
    bosses = _bosses_payload()

    parsed_phases = parse_public_api_phases(phases)
    assert select_current_phase_number(parsed_phases) == 2

    review = build_public_api_catalog_review(phases, bosses)
    assert review["phase_catalog"]["phase_count"] == 2
    assert review["phase_catalog"]["active_current_candidate_count"] == 1
    assert review["boss_catalog"]["boss_count"] == 2
    assert review["boss_catalog"]["duplicate_stable_boss_id_count"] == 0
    assert review["selection"]["current_phase_selectable"] is True
    assert review["public_release_safe"] is True

    serialized = json.dumps(review)
    assert "Current Raid" not in serialized
    assert "Boss One" not in serialized
    assert '"phase_number": 2' not in serialized
    assert "101" not in serialized


def test_current_phase_selection_fails_closed_when_ambiguous() -> None:
    phases = parse_public_api_phases(
        {
            "success": True,
            "phases": [
                {
                    "phase_number": 2,
                    "is_active": True,
                    "end_date": None,
                    "locations": [],
                },
                {
                    "phase_number": 3,
                    "is_active": True,
                    "end_date": None,
                    "locations": [],
                },
            ],
        }
    )

    with pytest.raises(ValueError, match="exactly one phase"):
        select_current_phase_number(phases)


def test_latest_archived_payload_is_loaded_from_raw_archive(tmp_path: Path) -> None:
    archive = RawArchive(tmp_path)
    payload = _phases_payload()
    archive.capture_bytes(
        json.dumps(payload).encode("utf-8"),
        source_code="test_public_api",
        endpoint_code="public_api_phases",
        request_key="GET:/phases",
        content_type="application/json",
    )

    loaded = load_latest_public_api_payload(
        tmp_path,
        source_code="test_public_api",
        endpoint_code="public_api_phases",
    )

    assert loaded == payload
