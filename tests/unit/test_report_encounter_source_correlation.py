from __future__ import annotations

import json
from pathlib import Path

import pytest

from coa_workbench.analytics.public_api_encounter_context import EncounterReference
from coa_workbench.analytics.report_encounter_source_correlation import (
    correlate_report_encounter_payload,
)


def _mapping() -> dict[str, object]:
    root = Path(__file__).resolve().parents[2]
    return json.loads(
        (root / "config" / "mappings" / "coa_encounter_detail_v1.json").read_text(
            encoding="utf-8"
        )
    )


def _payload(*, report_id: int = 98765431, encounter_id: int = 87654321) -> dict[str, object]:
    return {
        "encounter": {
            "report_id": report_id,
            "report_realm": "Example Realm",
            "id": encounter_id,
            "name": "Example Boss",
            "start_time": "2026-08-28T10:00:00Z",
            "end_time": "2026-08-28T10:01:00Z",
            "success": True,
            "difficulty": "ascended",
            "duration_seconds": "60.0",
            "player_count": 25,
            "zone": "Example Raid",
            "is_boss_encounter": True,
            "boss_id": 76543210,
            "creature_id": 65432109,
        },
        "character_stats": [],
    }


def _reference() -> EncounterReference:
    return EncounterReference(report_id=98765431, encounter_id=87654321)


def test_exact_first_party_encounter_correlates_boss_and_difficulty() -> None:
    result = correlate_report_encounter_payload(
        _payload(),
        _mapping(),
        reference=_reference(),
        expected_boss_name="Example Boss",
        expected_difficulty="ascended",
    )

    assert result.exact_reference_identity_verified is True
    assert result.boss_encounter_flag_verified is True
    assert result.boss_source_correlated is True
    assert result.difficulty_source_correlated is True
    assert result.complete is True

    summary = result.public_summary()
    assert summary["report_encounter_boss_source_correlated"] is True
    assert summary["report_encounter_difficulty_source_correlated"] is True
    assert summary["planner_scoring_allowed"] is False
    assert summary["public_release_safe"] is True
    assert summary["report_ids_included"] is False
    assert summary["encounter_ids_included"] is False
    assert summary["boss_names_included"] is False
    assert summary["difficulty_values_included"] is False
    assert summary["source_scalar_values_included"] is False


def test_boss_and_difficulty_mismatches_remain_separate_fail_closed_results() -> None:
    boss_mismatch = correlate_report_encounter_payload(
        _payload(),
        _mapping(),
        reference=_reference(),
        expected_boss_name="Other Boss",
        expected_difficulty="ascended",
    )
    assert boss_mismatch.boss_source_correlated is False
    assert boss_mismatch.difficulty_source_correlated is True
    assert boss_mismatch.complete is False

    difficulty_mismatch = correlate_report_encounter_payload(
        _payload(),
        _mapping(),
        reference=_reference(),
        expected_boss_name="Example Boss",
        expected_difficulty="heroic",
    )
    assert difficulty_mismatch.boss_source_correlated is True
    assert difficulty_mismatch.difficulty_source_correlated is False
    assert difficulty_mismatch.complete is False


def test_reference_identity_mismatch_blocks_both_correlations() -> None:
    result = correlate_report_encounter_payload(
        _payload(report_id=98765432),
        _mapping(),
        reference=_reference(),
        expected_boss_name="Example Boss",
        expected_difficulty="ascended",
    )

    assert result.exact_reference_identity_verified is False
    assert result.boss_source_correlated is False
    assert result.difficulty_source_correlated is False
    assert result.complete is False


def test_non_boss_flag_blocks_boss_correlation_only() -> None:
    payload = _payload()
    encounter = payload["encounter"]
    assert isinstance(encounter, dict)
    encounter["is_boss_encounter"] = False

    result = correlate_report_encounter_payload(
        payload,
        _mapping(),
        reference=_reference(),
        expected_boss_name="Example Boss",
        expected_difficulty="ascended",
    )

    assert result.exact_reference_identity_verified is True
    assert result.boss_encounter_flag_verified is False
    assert result.boss_source_correlated is False
    assert result.difficulty_source_correlated is True
    assert result.complete is False


def test_verified_parser_field_change_fails_before_correlation() -> None:
    payload = _payload()
    encounter = payload["encounter"]
    assert isinstance(encounter, dict)
    encounter["difficulty"] = 4

    with pytest.raises(ValueError, match="parser field type mismatch"):
        correlate_report_encounter_payload(
            payload,
            _mapping(),
            reference=_reference(),
            expected_boss_name="Example Boss",
            expected_difficulty="ascended",
        )
