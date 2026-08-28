from __future__ import annotations

import json
from pathlib import Path

import pytest

from coa_workbench.analytics.current_roster_build_provenance import (
    CURRENT_ROSTER_BUILD_PROVENANCE_VERSION,
    review_current_roster_build_provenance,
)
from coa_workbench.analytics.public_api_encounter_context import EncounterReference

_PROVENANCE = "source_observatory_current_report_runtime_v1"


def _reference() -> EncounterReference:
    return EncounterReference(report_id=123456, encounter_id=654321)


def _create_table(database: Path) -> object:
    duckdb = pytest.importorskip("duckdb")
    connection = duckdb.connect(str(database))
    connection.execute(
        """
        CREATE TABLE canonical_entity_observation (
            observation_id VARCHAR,
            entity_type VARCHAR,
            entity_key VARCHAR,
            entity_json VARCHAR,
            source_batch_ids_json VARCHAR,
            provenance_type VARCHAR,
            trust_status VARCHAR
        )
        """
    )
    return connection


def _insert(
    connection: object,
    *,
    observation_id: str,
    entity_type: str,
    entity_key: str,
    entity: dict[str, object],
) -> None:
    connection.execute(
        "INSERT INTO canonical_entity_observation VALUES (?, ?, ?, ?, ?, ?, 'observed')",
        [
            observation_id,
            entity_type,
            entity_key,
            json.dumps(entity),
            json.dumps(["private-source-capture"]),
            _PROVENANCE,
        ],
    )


def _populate_complete(database: Path, *, shared_guid: bool = False) -> None:
    connection = _create_table(database)
    try:
        _insert(
            connection,
            observation_id="report",
            entity_type="current_report_observation",
            entity_key="report-canonical",
            entity={
                "report_id": "report-canonical",
                "source_report_id": 123456,
            },
        )
        for index, name in enumerate(("Alpha", "Beta"), start=1):
            character_key = f"character-{index}"
            source_character_id = f"source-{index}"
            snapshot_hash = f"snapshot-{index}"
            _insert(
                connection,
                observation_id=f"character-observation-{index}",
                entity_type="current_roster_character_observation",
                entity_key=character_key,
                entity={
                    "current_roster_character_id": character_key,
                    "report_id": "report-canonical",
                    "source_character_id": source_character_id,
                    "name": name,
                },
            )
            _insert(
                connection,
                observation_id=f"snapshot-observation-{index}",
                entity_type="current_roster_snapshot_observation",
                entity_key=snapshot_hash,
                entity={
                    "current_roster_character_id": character_key,
                    "report_id": "report-canonical",
                    "source_character_id": source_character_id,
                    "snapshot_hash": snapshot_hash,
                    "captured_at": f"2026-08-28T10:0{index}:00Z",
                    "outer_character": {"name": name},
                    "player": {
                        "guid": "shared-guid" if shared_guid else f"guid-{index}",
                        "name": name,
                        "realm": "Example Realm",
                    },
                    "specialization": {"active_spec_name": f"Spec {index}"},
                },
            )
            _insert(
                connection,
                observation_id=f"talent-observation-{index}",
                entity_type="current_talent_entry_observation",
                entity_key=f"talent-{index}",
                entity={
                    "current_roster_character_id": character_key,
                    "report_id": "report-canonical",
                    "snapshot_hash": snapshot_hash,
                    "entry_id": str(index),
                },
            )
            _insert(
                connection,
                observation_id=f"gear-observation-{index}",
                entity_type="current_gear_slot_observation",
                entity_key=f"gear-{index}",
                entity={
                    "current_roster_character_id": character_key,
                    "report_id": "report-canonical",
                    "snapshot_hash": snapshot_hash,
                    "slot_key": str(index),
                },
            )
    finally:
        connection.close()


def test_complete_report_scoped_identity_and_build_provenance(tmp_path: Path) -> None:
    database = tmp_path / "coa.duckdb"
    _populate_complete(database)

    review = review_current_roster_build_provenance(database, reference=_reference())
    assert review.character_count == 2
    assert review.snapshot_count == 2
    assert review.talent_entry_count == 2
    assert review.gear_slot_observation_count == 2
    assert review.report_scoped_player_identity_complete is True
    assert review.observed_build_linkage_complete is True
    assert review.source_provenance_complete is True
    assert review.observed_build_provenance_complete is True
    assert review.observed_timestamp_coverage_complete is True

    summary = review.public_summary()
    assert summary["review_version"] == CURRENT_ROSTER_BUILD_PROVENANCE_VERSION
    assert summary["current_build_freshness_verified"] is False
    assert summary["latest_snapshot_semantics_verified"] is False
    assert summary["cross_report_identity_verified"] is False
    assert summary["planner_scoring_allowed"] is False
    assert summary["player_names_included"] is False
    assert summary["player_guids_included"] is False
    assert summary["build_values_included"] is False
    assert summary["public_release_safe"] is True


def test_missing_gear_fails_build_linkage_without_promoting_identity(tmp_path: Path) -> None:
    database = tmp_path / "coa.duckdb"
    _populate_complete(database)
    duckdb = pytest.importorskip("duckdb")
    with duckdb.connect(str(database)) as connection:
        connection.execute(
            "DELETE FROM canonical_entity_observation WHERE observation_id = 'gear-observation-2'"
        )

    review = review_current_roster_build_provenance(database, reference=_reference())
    assert review.report_scoped_player_identity_complete is True
    assert review.observed_build_linkage_complete is False
    assert review.observed_build_provenance_complete is False


def test_guid_reused_across_characters_fails_report_scoped_identity(tmp_path: Path) -> None:
    database = tmp_path / "coa.duckdb"
    _populate_complete(database, shared_guid=True)

    review = review_current_roster_build_provenance(database, reference=_reference())
    assert review.cross_character_guid_conflict_count == 1
    assert review.report_scoped_player_identity_complete is False
    assert review.observed_build_provenance_complete is False


def test_duplicate_source_character_identity_fails_closed(tmp_path: Path) -> None:
    database = tmp_path / "coa.duckdb"
    _populate_complete(database)
    duckdb = pytest.importorskip("duckdb")
    with duckdb.connect(str(database)) as connection:
        row = connection.execute(
            "SELECT entity_json FROM canonical_entity_observation "
            "WHERE observation_id = 'character-observation-2'"
        ).fetchone()
        assert row is not None
        entity = json.loads(str(row[0]))
        entity["source_character_id"] = "source-1"
        connection.execute(
            "UPDATE canonical_entity_observation SET entity_json = ? "
            "WHERE observation_id = 'character-observation-2'",
            [json.dumps(entity)],
        )

    with pytest.raises(ValueError, match="duplicate source_character_id"):
        review_current_roster_build_provenance(database, reference=_reference())


def test_unknown_report_reference_fails_closed(tmp_path: Path) -> None:
    database = tmp_path / "coa.duckdb"
    _populate_complete(database)

    with pytest.raises(ValueError, match="exactly one persisted report identity; found 0"):
        review_current_roster_build_provenance(
            database,
            reference=EncounterReference(report_id=999999, encounter_id=654321),
        )
