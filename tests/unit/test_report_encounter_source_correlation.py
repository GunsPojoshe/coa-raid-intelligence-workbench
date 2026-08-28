from __future__ import annotations

import json
from pathlib import Path

import pytest

from coa_workbench.analytics.public_api_encounter_context import EncounterReference
from coa_workbench.analytics.report_encounter_source_correlation import (
    REPORT_ENCOUNTER_CATALOG_PARSER_VERSION,
    correlate_report_encounter_catalog_payload,
    correlate_report_encounter_payload,
    load_persisted_report_encounter_catalog,
)


def _reference() -> EncounterReference:
    return EncounterReference(report_id=98765431, encounter_id=87654321)


def _catalog_payload(
    *,
    report_id: int = 98765431,
    encounter_id: int = 87654321,
) -> dict[str, object]:
    return {
        "success": True,
        "report": {"id": report_id, "title": "Example Report"},
        "encounters": [
            {
                "id": encounter_id,
                "name": "Example Boss",
                "difficulty": "ascended",
                "is_boss_encounter": True,
                "zone": "Example Raid",
                "boss_id": 76543210,
            }
        ],
        "summary": {"total_encounters": 1},
    }


def _detail_mapping() -> dict[str, object]:
    root = Path(__file__).resolve().parents[2]
    return json.loads(
        (root / "config" / "mappings" / "coa_encounter_detail_v1.json").read_text(
            encoding="utf-8"
        )
    )


def _detail_payload() -> dict[str, object]:
    return {
        "encounter": {
            "report_id": 98765431,
            "report_realm": "Example Realm",
            "id": 87654321,
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


def test_exact_first_party_catalog_correlates_boss_and_difficulty() -> None:
    result = correlate_report_encounter_catalog_payload(
        _catalog_payload(),
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
    assert summary["parser_version"] == REPORT_ENCOUNTER_CATALOG_PARSER_VERSION
    assert summary["report_encounter_boss_source_correlated"] is True
    assert summary["report_encounter_difficulty_source_correlated"] is True
    assert summary["planner_scoring_allowed"] is False
    assert summary["public_release_safe"] is True
    assert summary["report_ids_included"] is False
    assert summary["encounter_ids_included"] is False
    assert summary["boss_names_included"] is False
    assert summary["difficulty_values_included"] is False
    assert summary["source_scalar_values_included"] is False


def test_catalog_boss_and_difficulty_mismatches_remain_separate() -> None:
    boss_mismatch = correlate_report_encounter_catalog_payload(
        _catalog_payload(),
        reference=_reference(),
        expected_boss_name="Other Boss",
        expected_difficulty="ascended",
    )
    assert boss_mismatch.boss_source_correlated is False
    assert boss_mismatch.difficulty_source_correlated is True
    assert boss_mismatch.complete is False

    difficulty_mismatch = correlate_report_encounter_catalog_payload(
        _catalog_payload(),
        reference=_reference(),
        expected_boss_name="Example Boss",
        expected_difficulty="heroic",
    )
    assert difficulty_mismatch.boss_source_correlated is True
    assert difficulty_mismatch.difficulty_source_correlated is False
    assert difficulty_mismatch.complete is False


def test_catalog_report_identity_mismatch_blocks_both_correlations() -> None:
    result = correlate_report_encounter_catalog_payload(
        _catalog_payload(report_id=98765432),
        reference=_reference(),
        expected_boss_name="Example Boss",
        expected_difficulty="ascended",
    )

    assert result.exact_reference_identity_verified is False
    assert result.boss_source_correlated is False
    assert result.difficulty_source_correlated is False
    assert result.complete is False


def test_catalog_requires_exactly_one_selected_encounter() -> None:
    payload = _catalog_payload(encounter_id=87654322)
    with pytest.raises(ValueError, match="exactly one selected encounter row"):
        correlate_report_encounter_catalog_payload(
            payload,
            reference=_reference(),
            expected_boss_name="Example Boss",
            expected_difficulty="ascended",
        )


def test_catalog_non_boss_flag_blocks_boss_correlation_only() -> None:
    payload = _catalog_payload()
    encounters = payload["encounters"]
    assert isinstance(encounters, list)
    encounter = encounters[0]
    assert isinstance(encounter, dict)
    encounter["is_boss_encounter"] = False

    result = correlate_report_encounter_catalog_payload(
        payload,
        reference=_reference(),
        expected_boss_name="Example Boss",
        expected_difficulty="ascended",
    )

    assert result.exact_reference_identity_verified is True
    assert result.boss_encounter_flag_verified is False
    assert result.boss_source_correlated is False
    assert result.difficulty_source_correlated is True
    assert result.complete is False


def test_catalog_selected_field_type_change_fails_closed() -> None:
    payload = _catalog_payload()
    encounters = payload["encounters"]
    assert isinstance(encounters, list)
    encounter = encounters[0]
    assert isinstance(encounter, dict)
    encounter["difficulty"] = 4

    with pytest.raises(ValueError, match="difficulty must be a non-empty string"):
        correlate_report_encounter_catalog_payload(
            payload,
            reference=_reference(),
            expected_boss_name="Example Boss",
            expected_difficulty="ascended",
        )


def test_persisted_catalog_lookup_reuses_exact_current_encounter_observation(
    tmp_path: Path,
) -> None:
    duckdb = pytest.importorskip("duckdb")
    database = tmp_path / "coa.duckdb"
    entity = {
        "normalized": {
            "source_report_id": 98765431,
            "source_encounter_id": 87654321,
        },
        "catalog_observation": _catalog_payload()["encounters"][0],
    }
    with duckdb.connect(str(database)) as connection:
        connection.execute(
            "CREATE TABLE canonical_entity_observation (entity_type VARCHAR, entity_json VARCHAR)"
        )
        connection.execute(
            "INSERT INTO canonical_entity_observation VALUES (?, ?)",
            ["current_encounter_observation", json.dumps(entity)],
        )

    evidence = load_persisted_report_encounter_catalog(database, reference=_reference())
    assert evidence is not None
    assert evidence.matching_observation_count == 1

    result = correlate_report_encounter_catalog_payload(
        evidence.payload,
        reference=_reference(),
        expected_boss_name="Example Boss",
        expected_difficulty="ascended",
        source_kind="persisted_first_party_encounter_catalog",
    )
    assert result.complete is True
    assert result.public_summary()["source_kind"] == "persisted_first_party_encounter_catalog"


def test_persisted_catalog_lookup_fails_when_observations_disagree(tmp_path: Path) -> None:
    duckdb = pytest.importorskip("duckdb")
    database = tmp_path / "coa.duckdb"
    first_catalog = dict(_catalog_payload()["encounters"][0])
    second_catalog = dict(first_catalog)
    second_catalog["difficulty"] = "heroic"

    with duckdb.connect(str(database)) as connection:
        connection.execute(
            "CREATE TABLE canonical_entity_observation (entity_type VARCHAR, entity_json VARCHAR)"
        )
        for catalog in (first_catalog, second_catalog):
            entity = {
                "normalized": {
                    "source_report_id": 98765431,
                    "source_encounter_id": 87654321,
                },
                "catalog_observation": catalog,
            }
            connection.execute(
                "INSERT INTO canonical_entity_observation VALUES (?, ?)",
                ["current_encounter_observation", json.dumps(entity)],
            )

    with pytest.raises(ValueError, match="observations disagree"):
        load_persisted_report_encounter_catalog(database, reference=_reference())


def test_legacy_encounter_detail_correlation_remains_compatible() -> None:
    result = correlate_report_encounter_payload(
        _detail_payload(),
        _detail_mapping(),
        reference=_reference(),
        expected_boss_name="Example Boss",
        expected_difficulty="ascended",
    )

    assert result.complete is True
    assert result.public_summary()["source_kind"] == "legacy_first_party_encounter_detail"
