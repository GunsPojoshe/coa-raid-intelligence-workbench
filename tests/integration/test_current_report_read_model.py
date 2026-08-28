from __future__ import annotations

import json
from pathlib import Path

import pytest

from coa_workbench.analytics.current_report_read_model import (
    CURRENT_REPORT_COMPARISON_READ_MODEL_VERSION,
    build_current_report_comparison_read_model,
    list_current_report_comparison_reports,
)
from coa_workbench.storage.current_report_analytics import (
    CURRENT_REPORT_ANALYTICS_PERSISTENCE_VERSION,
)
from coa_workbench.storage.current_report_observations import (
    CURRENT_REPORT_PERSISTENCE_VERSION,
)
from coa_workbench.storage.migrations import apply_migrations


duckdb = pytest.importorskip("duckdb")


def _insert_run(
    connection,
    *,
    persistence_run_id: str,
    reconstruction_sha256: str,
    reconstruction_version: str,
    finished_at: str,
) -> None:
    connection.execute(
        """
        INSERT INTO parser_slice_persistence_run (
            persistence_run_id, reconstruction_sha256, reconstruction_version,
            source_code, source_normalization_name, status, input_counts_json,
            persisted_counts_json, source_batch_hashes_json, metadata_json,
            started_at, finished_at
        ) VALUES (?, ?, ?, 'coa_ascension_logs', 'test', 'completed',
                  '{}', '{}', '{}', '{}', ?, ?)
        """,
        [
            persistence_run_id,
            reconstruction_sha256,
            reconstruction_version,
            finished_at,
            finished_at,
        ],
    )


def _insert_entity(
    connection,
    *,
    observation_id: str,
    persistence_run_id: str,
    entity_type: str,
    entity_key: str,
    payload: dict[str, object],
) -> None:
    connection.execute(
        """
        INSERT INTO canonical_entity_observation (
            observation_id, persistence_run_id, entity_type, entity_key, entity_hash,
            source_batch_ids_json, provenance_type, trust_status, entity_json
        ) VALUES (?, ?, ?, ?, ?, '[]', 'test', 'observed', ?)
        """,
        [
            observation_id,
            persistence_run_id,
            entity_type,
            entity_key,
            f"hash-{observation_id}",
            json.dumps(payload, sort_keys=True),
        ],
    )


def _seed(database: Path, migrations: Path) -> None:
    apply_migrations(database, migrations)
    with duckdb.connect(str(database)) as connection:
        _insert_run(
            connection,
            persistence_run_id="report-run",
            reconstruction_sha256="report-artifact",
            reconstruction_version=CURRENT_REPORT_PERSISTENCE_VERSION,
            finished_at="2026-08-14 12:00:00",
        )
        _insert_entity(
            connection,
            observation_id="report",
            persistence_run_id="report-run",
            entity_type="current_report_observation",
            entity_key="canonical-report",
            payload={
                "report_id": "canonical-report",
                "source_report_id": "123",
                "title": "Example Report",
                "zone": "Example Raid",
                "start_time": "2026-08-14T12:00:00Z",
            },
        )
        _insert_entity(
            connection,
            observation_id="encounter",
            persistence_run_id="report-run",
            entity_type="current_encounter_observation",
            entity_key="canonical-encounter",
            payload={
                "encounter_id": "canonical-encounter",
                "report_id": "canonical-report",
                "source_encounter_id": "1",
                "normalized": {
                    "source_report_id": "123",
                    "source_encounter_id": "1",
                    "name": "Boss One",
                },
                "catalog_observation": {"difficulty": "example"},
            },
        )
        for character_id, name, total_snapshots in (
            ("101", "Alpha", 1),
            ("102", "Beta", 2),
        ):
            _insert_entity(
                connection,
                observation_id=f"roster-{character_id}",
                persistence_run_id="report-run",
                entity_type="current_roster_character_observation",
                entity_key=f"character-{character_id}",
                payload={
                    "current_roster_character_id": f"character-{character_id}",
                    "report_id": "canonical-report",
                    "source_character_id": character_id,
                    "name": name,
                    "class": "ExampleClass",
                    "role": "damage",
                    "specs": ["ExampleSpec"],
                    "snapshot_count": total_snapshots,
                },
            )

        _insert_run(
            connection,
            persistence_run_id="analytics-run",
            reconstruction_sha256="analytics-artifact",
            reconstruction_version=CURRENT_REPORT_ANALYTICS_PERSISTENCE_VERSION,
            finished_at="2026-08-14 12:05:00",
        )
        _insert_entity(
            connection,
            observation_id="throughput-request",
            persistence_run_id="analytics-run",
            entity_type="current_throughput_request_observation",
            entity_key="request",
            payload={
                "request_index": 0,
                "source_report_id": "123",
                "source_encounter_id": "1",
                "metric": "damage",
                "perspective": None,
            },
        )
        for character_id, name, total, match in (
            ("101", "Alpha", 100, "matched"),
            ("102", "Beta", 50, "matched"),
            ("999", "Other", 200, "unmatched"),
        ):
            _insert_entity(
                connection,
                observation_id=f"throughput-character-{character_id}",
                persistence_run_id="analytics-run",
                entity_type="current_throughput_character_observation",
                entity_key=f"throughput-character-{character_id}",
                payload={
                    "request_index": 0,
                    "source_report_id": "123",
                    "source_encounter_id": "1",
                    "metric": "damage",
                    "perspective": None,
                    "source_character_id": character_id,
                    "name": name,
                    "class": "ExampleClass",
                    "total_amount": total,
                    "roster_match_status": match,
                },
            )
        for index, status in enumerate(("exact_character_id_match", "opaque_group_key")):
            _insert_entity(
                connection,
                observation_id=f"throughput-point-{index}",
                persistence_run_id="analytics-run",
                entity_type="current_throughput_point_observation",
                entity_key=f"throughput-point-{index}",
                payload={
                    "request_index": 0,
                    "source_report_id": "123",
                    "source_encounter_id": "1",
                    "series_character_link_status": status,
                },
            )

        for index, group_key in enumerate(("101", "opaque")):
            _insert_entity(
                connection,
                observation_id=f"damage-{index}",
                persistence_run_id="analytics-run",
                entity_type="current_damage_taken_ability_observation",
                entity_key=f"damage-{index}",
                payload={
                    "source_report_id": "123",
                    "source_group_key": group_key,
                    "spell_id": "7",
                    "damage": 12,
                },
            )

        for index, character_id in enumerate(("101", "999")):
            _insert_entity(
                connection,
                observation_id=f"healing-spell-{index}",
                persistence_run_id="analytics-run",
                entity_type="current_healing_spell_observation",
                entity_key=f"healing-spell-{index}",
                payload={
                    "source_report_id": "123",
                    "source_group_key": character_id,
                    "source_character_id": character_id,
                    "spell_id": "9",
                    "effective_healing": 18,
                    "roster_match_status": (
                        "matched" if character_id == "101" else "unmatched"
                    ),
                },
            )

        for index, character_id in enumerate(("101", "999")):
            _insert_entity(
                connection,
                observation_id=f"healing-source-{index}",
                persistence_run_id="analytics-run",
                entity_type="current_healing_source_breakdown_observation",
                entity_key=f"healing-source-{index}",
                payload={
                    "source_report_id": "123",
                    "source_group_key": "9",
                    "source_character_id": character_id,
                    "effective_healing": 18,
                },
            )

        _insert_entity(
            connection,
            observation_id="healing-target",
            persistence_run_id="analytics-run",
            entity_type="current_healing_target_breakdown_observation",
            entity_key="healing-target",
            payload={
                "source_report_id": "123",
                "source_group_key": "9",
                "target_character_id": "102",
                "effective_healing": 18,
            },
        )


def test_current_report_comparison_read_model_ranks_only_exact_roster_matches(
    tmp_path: Path,
) -> None:
    root = Path(__file__).resolve().parents[2]
    database = tmp_path / "coa.duckdb"
    migrations = root / "migrations"
    _seed(database, migrations)

    model = build_current_report_comparison_read_model(
        database,
        migrations,
        report_id="canonical-report",
    )

    assert model["read_model_version"] == CURRENT_REPORT_COMPARISON_READ_MODEL_VERSION
    assert model["report"]["title"] == "Example Report"
    assert model["encounter_count"] == 1
    assert model["roster_character_count"] == 2
    assert len(model["throughput_profiles"]) == 1

    profile = model["throughput_profiles"][0]
    assert profile["encounter_name"] == "Boss One"
    assert profile["ranking_basis"] == "upstream_characters_total_amount_desc"
    assert [row["source_character_id"] for row in profile["rows"]] == ["101", "102"]
    assert [row["rank"] for row in profile["rows"]] == [1, 2]
    assert [row["total_amount"] for row in profile["rows"]] == [100, 50]

    players = {row["source_character_id"]: row for row in model["players"]}
    assert players["101"]["throughput_character_observation_count"] == 1
    assert players["101"]["damage_taken_ability_exact_key_match_count"] == 1
    assert players["101"]["healing_spell_observation_count"] == 1
    assert players["101"]["healing_source_breakdown_observation_count"] == 1
    assert players["102"]["healing_target_breakdown_observation_count"] == 1

    assert model["summary"]["matched_ranked_character_rows"] == 2
    assert model["summary"]["unmatched_character_rows"] == 1
    assert model["summary"]["throughput_point_exact_character_link_count"] == 1
    assert model["summary"]["throughput_point_opaque_group_count"] == 1
    assert model["summary"]["damage_taken_exact_roster_key_match_row_count"] == 1
    assert model["summary"]["healing_spell_explicit_roster_match_row_count"] == 1
    assert model["summary"]["healing_source_explicit_roster_match_row_count"] == 1
    assert model["summary"]["healing_target_explicit_roster_match_row_count"] == 1

    assert model["interpretation"]["damage_group_key_target_semantics_verified"] is False
    assert model["interpretation"]["mechanic_semantics_verified"] is False
    assert model["interpretation"]["planner_scoring_allowed"] is False
    assert model["local_private_payload"] is True
    assert model["public_release_safe"] is False


def test_current_report_comparison_catalog_uses_latest_completed_analytics_run(
    tmp_path: Path,
) -> None:
    root = Path(__file__).resolve().parents[2]
    database = tmp_path / "coa.duckdb"
    migrations = root / "migrations"
    _seed(database, migrations)

    catalog = list_current_report_comparison_reports(database, migrations)

    assert catalog["report_count"] == 1
    assert catalog["reports"][0]["report_id"] == "canonical-report"
    assert catalog["reports"][0]["analytics_artifact_key"] == "analytics-artifact"
    assert catalog["reports"][0]["encounter_count"] == 1
    assert catalog["reports"][0]["roster_character_count"] == 2
    assert catalog["planner_scoring_allowed"] is False


def test_current_report_comparison_read_model_returns_not_found_for_unknown_report(
    tmp_path: Path,
) -> None:
    root = Path(__file__).resolve().parents[2]
    database = tmp_path / "coa.duckdb"
    migrations = root / "migrations"
    _seed(database, migrations)

    with pytest.raises(KeyError):
        build_current_report_comparison_read_model(
            database,
            migrations,
            report_id="missing",
        )
