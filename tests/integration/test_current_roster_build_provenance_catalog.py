from __future__ import annotations

import json
from pathlib import Path

import pytest

from coa_workbench.analytics.current_roster_build_provenance_catalog import (
    CURRENT_ROSTER_BUILD_PROVENANCE_CATALOG_VERSION,
    review_current_roster_build_provenance_catalog,
)
from coa_workbench.analytics.public_api_encounter_context import EncounterReference

_PROVENANCE = "source_observatory_current_report_runtime_v1"


def _create_complete_report(database: Path) -> None:
    duckdb = pytest.importorskip("duckdb")
    with duckdb.connect(str(database)) as connection:
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

        def insert(
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

        insert(
            "report",
            "current_report_observation",
            "report-canonical",
            {"report_id": "report-canonical", "source_report_id": 123456},
        )
        insert(
            "character",
            "current_roster_character_observation",
            "character-1",
            {
                "current_roster_character_id": "character-1",
                "report_id": "report-canonical",
                "source_character_id": "source-1",
                "name": "Alpha",
            },
        )
        insert(
            "snapshot",
            "current_roster_snapshot_observation",
            "snapshot-1",
            {
                "current_roster_character_id": "character-1",
                "report_id": "report-canonical",
                "source_character_id": "source-1",
                "snapshot_hash": "snapshot-1",
                "captured_at": "2026-08-28T10:01:00Z",
                "outer_character": {"name": "Alpha"},
                "player": {
                    "guid": "private-guid",
                    "name": "Alpha",
                    "realm": "Example Realm",
                },
                "specialization": {"active_spec_name": "Example Spec"},
            },
        )
        insert(
            "talent",
            "current_talent_entry_observation",
            "talent-1",
            {
                "current_roster_character_id": "character-1",
                "report_id": "report-canonical",
                "snapshot_hash": "snapshot-1",
                "entry_id": "1",
            },
        )
        insert(
            "gear",
            "current_gear_slot_observation",
            "gear-1",
            {
                "current_roster_character_id": "character-1",
                "report_id": "report-canonical",
                "snapshot_hash": "snapshot-1",
                "slot_key": "1",
            },
        )


def test_catalog_review_keeps_unknown_selected_reference_separate(tmp_path: Path) -> None:
    database = tmp_path / "coa.duckdb"
    _create_complete_report(database)

    review = review_current_roster_build_provenance_catalog(
        database,
        reference=EncounterReference(report_id=999999, encounter_id=1),
    )

    assert review.persisted_report_count == 1
    assert review.reviewed_report_scope_count == 1
    assert review.observed_build_provenance_complete_count == 1
    assert review.all_persisted_report_build_provenance_complete is True
    assert review.selected_reference_present is False
    assert review.selected_reference_same_report_build_binding_proven is False

    summary = review.public_summary()
    assert summary["catalog_version"] == CURRENT_ROSTER_BUILD_PROVENANCE_CATALOG_VERSION
    assert summary["report_ids_included"] is False
    assert summary["player_names_included"] is False
    assert summary["build_values_included"] is False
    assert summary["public_release_safe"] is True


def test_catalog_review_marks_selected_reference_when_present(tmp_path: Path) -> None:
    database = tmp_path / "coa.duckdb"
    _create_complete_report(database)

    review = review_current_roster_build_provenance_catalog(
        database,
        reference=EncounterReference(report_id=123456, encounter_id=1),
    )

    assert review.selected_reference_present is True
    assert review.selected_reference_report_scoped_player_identity_complete is True
    assert review.selected_reference_observed_build_provenance_complete is True
    assert review.selected_reference_same_report_build_binding_proven is True


def test_catalog_review_fails_closed_on_duplicate_report_identity(tmp_path: Path) -> None:
    database = tmp_path / "coa.duckdb"
    _create_complete_report(database)
    duckdb = pytest.importorskip("duckdb")
    with duckdb.connect(str(database)) as connection:
        connection.execute(
            """
            INSERT INTO canonical_entity_observation VALUES (?, ?, ?, ?, ?, ?, 'observed')
            """,
            [
                "report-duplicate",
                "current_report_observation",
                "report-canonical-duplicate",
                json.dumps({"report_id": "report-canonical-duplicate", "source_report_id": 123456}),
                json.dumps(["private-source-capture"]),
                _PROVENANCE,
            ],
        )

    with pytest.raises(ValueError, match="duplicate source_report_id"):
        review_current_roster_build_provenance_catalog(
            database,
            reference=EncounterReference(report_id=123456, encounter_id=1),
        )
