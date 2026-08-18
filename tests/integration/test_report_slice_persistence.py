from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from coa_workbench.storage.migrations import apply_migrations
from coa_workbench.storage.report_slice import persist_observed_report_slice


duckdb = pytest.importorskip("duckdb")


REPORT_MAPPING_ID = "coa-report-detail-v1"
ENCOUNTER_MAPPING_ID = "coa-encounter-detail-v1"
REPORT_MAPPING_FILE = "coa_report_detail_v1.json"
ENCOUNTER_MAPPING_FILE = "coa_encounter_detail_v1.json"
REPORT_PAYLOAD_HASH = "1" * 64
ENCOUNTER_PAYLOAD_HASH = "2" * 64
REPORT_SCHEMA = "3" * 64
ENCOUNTER_SCHEMA = "4" * 64
REPORT_BATCH_HASH = "5" * 64
ENCOUNTER_BATCH_HASH = "6" * 64
REPORT_ID = "a" * 64
EXACT_ENCOUNTER_ID = "b" * 64


def _write_json(path: Path, payload: object) -> bytes:
    body = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(body)
    return body


def _mapping(mapping_id: str, schema: str, payload_hash: str) -> dict[str, object]:
    return {
        "mapping_id": mapping_id,
        "source_code": "coa_ascension_logs",
        "schema_fingerprint": schema,
        "mapping_version": "1",
        "status": "verified",
        "reviewed_payload_hash": payload_hash,
        "mechanic_semantics_verified": False,
        "entities": {},
        "event_type_map": {},
    }


def _fixture(tmp_path: Path) -> dict[str, Path]:
    root = Path(__file__).resolve().parents[2]
    migrations = root / "migrations"
    database = tmp_path / "coa.duckdb"
    mapping_dir = tmp_path / "mappings"
    mapping_dir.mkdir()

    report_mapping_body = _write_json(
        mapping_dir / REPORT_MAPPING_FILE,
        _mapping(REPORT_MAPPING_ID, REPORT_SCHEMA, REPORT_PAYLOAD_HASH),
    )
    encounter_mapping_body = _write_json(
        mapping_dir / ENCOUNTER_MAPPING_FILE,
        _mapping(ENCOUNTER_MAPPING_ID, ENCOUNTER_SCHEMA, ENCOUNTER_PAYLOAD_HASH),
    )

    normalization = {
        "schema_version": 1,
        "normalization_kind": "observed_report_slice_selected_parser_normalization",
        "generated_at": "2026-07-29T15:48:11Z",
        "normalized_batches": [
            {
                "mapping_id": ENCOUNTER_MAPPING_ID,
                "mapping_file": ENCOUNTER_MAPPING_FILE,
                "mapping_content_sha256": hashlib.sha256(encounter_mapping_body).hexdigest(),
                "source_payload_hash": ENCOUNTER_PAYLOAD_HASH,
                "schema_fingerprint": ENCOUNTER_SCHEMA,
                "normalized_batch_file": "coa_encounter_detail_v1.normalized.json",
                "normalized_batch_sha256": ENCOUNTER_BATCH_HASH,
                "counts": {
                    "reports": 1,
                    "encounters": 1,
                    "actors": 31,
                    "participants": 31,
                    "aura_events": 0,
                    "rejects": 0,
                },
                "mapping_hash_verified": True,
                "raw_archive_verified": True,
            },
            {
                "mapping_id": REPORT_MAPPING_ID,
                "mapping_file": REPORT_MAPPING_FILE,
                "mapping_content_sha256": hashlib.sha256(report_mapping_body).hexdigest(),
                "source_payload_hash": REPORT_PAYLOAD_HASH,
                "schema_fingerprint": REPORT_SCHEMA,
                "normalized_batch_file": "coa_report_detail_v1.normalized.json",
                "normalized_batch_sha256": REPORT_BATCH_HASH,
                "counts": {
                    "reports": 1,
                    "encounters": 14,
                    "actors": 0,
                    "participants": 0,
                    "aura_events": 0,
                    "rejects": 0,
                },
                "mapping_hash_verified": True,
                "raw_archive_verified": True,
            },
        ],
        "cross_payload_checks": {
            "exact_encounter_present_in_report_batch": True,
            "participant_actor_references_resolved": True,
            "participant_encounter_references_resolved": True,
            "participant_pairs_unique": True,
            "report_id_consistent": True,
            "single_report_id_in_each_batch": True,
        },
        "decision_boundary": {
            "status": "normalized_parser_slice",
            "selected_parser_normalization_completed": True,
            "ready_for_deterministic_reconstruction": True,
            "automatic_commit": False,
            "mechanic_semantics_verified": False,
            "combatants_info_enrichment_available": False,
            "aura_normalization_available": False,
            "full_report_slice_complete": False,
            "normalized_batch_files_contain_source_scalar_values": True,
        },
        "summary": {
            "mapping_count": 2,
            "field_contract_count": 54,
            "exact_raw_archive_count": 2,
            "aggregate_counts": {
                "reports": 2,
                "encounters": 15,
                "actors": 31,
                "participants": 31,
                "aura_events": 0,
                "rejects": 0,
            },
            "all_mapping_hashes_verified": True,
            "all_raw_archives_verified": True,
            "all_normalization_counts_match": True,
            "cross_payload_consistent": True,
            "contains_source_scalar_values": False,
            "normalized_batch_files_contain_source_scalar_values": True,
            "ready_for_deterministic_reconstruction": True,
            "mechanic_semantics_verified": False,
            "full_report_slice_complete": False,
        },
    }
    normalization_path = tmp_path / "observed-report-slice-normalization.json"
    _write_json(normalization_path, normalization)

    encounters = []
    for index in range(14):
        encounter_id = EXACT_ENCOUNTER_ID if index == 4 else f"{index + 10:064x}"
        row: dict[str, object] = {
            "encounter_id": encounter_id,
            "report_id": REPORT_ID,
            "source_encounter_id": str(index + 1),
            "name": f"PRIVATE ENCOUNTER {index + 1}",
            "start_time": f"2026-07-29T12:{index:02d}:00Z",
            "end_time": f"2026-07-29T12:{index:02d}:30Z",
            "success": index == 4,
        }
        if index == 4:
            row.update(
                {
                    "boss_id": 9001,
                    "creature_id": 9002,
                    "difficulty": "PRIVATE DIFFICULTY",
                    "duration_seconds": "30.0",
                    "is_boss_encounter": True,
                    "player_count": 31,
                    "zone": "PRIVATE ZONE",
                }
            )
        encounters.append(row)

    actors = [
        {
            "actor_id": f"{index + 100:064x}",
            "source_actor_id": str(index + 1),
            "name": f"PRIVATE ACTOR {index + 1}",
            "actor_type": "Player",
            "class": "PRIVATE CLASS",
            "spec": "PRIVATE SPEC",
            "level": None,
        }
        for index in range(31)
    ]
    participants = [
        {
            "encounter_id": EXACT_ENCOUNTER_ID,
            "actor_id": actor["actor_id"],
            "source_encounter_id": "5",
            "source_actor_id": str(index + 1),
            "avg_dps": 1000.5 + index,
            "avg_hps": index,
            "damage_taken": index,
            "deaths": 0,
            "effective_healing": index,
            "encounter_duration": 30.0,
            "is_consolidated": False,
            "total_absorbs": 0,
            "total_damage": 30000 + index,
            "total_healing": index,
        }
        for index, actor in enumerate(actors)
    ]
    reconstructed_payload = {
        "schema_version": 1,
        "reconstruction_kind": "observed_report_slice_canonical_reconstruction",
        "reconstruction_version": "report-slice-reconstruction-v1",
        "source_normalization_name": normalization_path.name,
        "source_normalized_batch_sha256": {
            ENCOUNTER_MAPPING_ID: ENCOUNTER_BATCH_HASH,
            REPORT_MAPPING_ID: REPORT_BATCH_HASH,
        },
        "canonical_slice": {
            "source_code": "coa_ascension_logs",
            "reports": [
                {
                    "report_id": REPORT_ID,
                    "source_report_id": "77",
                    "title": "PRIVATE REPORT",
                    "created_at": "2026-07-29T12:00:00Z",
                    "start_time": "2026-07-29T12:00:00Z",
                    "end_time": "2026-07-29T13:00:00Z",
                    "visibility": "public",
                    "timezone": "UTC",
                    "realm": "PRIVATE REALM",
                    "zone": "PRIVATE ZONE",
                    "status": "processed",
                    "has_telemetry": True,
                }
            ],
            "encounters": encounters,
            "actors": actors,
            "participants": participants,
            "aura_events": [],
            "rejects": [],
        },
    }
    reconstructed_output_path = tmp_path / "observed-report-slice.reconstructed.json"
    reconstructed_body = _write_json(reconstructed_output_path, reconstructed_payload)
    reconstructed_hash = hashlib.sha256(reconstructed_body).hexdigest()

    reconstruction = {
        "schema_version": 1,
        "reconstruction_kind": "observed_report_slice_deterministic_reconstruction",
        "reconstruction_version": "report-slice-reconstruction-v1",
        "generated_at": "2026-07-29T15:58:23Z",
        "source_normalization_name": normalization_path.name,
        "source_normalized_batches": [
            {
                "mapping_id": ENCOUNTER_MAPPING_ID,
                "normalized_batch_file": "coa_encounter_detail_v1.normalized.json",
                "normalized_batch_sha256": ENCOUNTER_BATCH_HASH,
                "counts": normalization["normalized_batches"][0]["counts"],
                "batch_hash_verified": True,
            },
            {
                "mapping_id": REPORT_MAPPING_ID,
                "normalized_batch_file": "coa_report_detail_v1.normalized.json",
                "normalized_batch_sha256": REPORT_BATCH_HASH,
                "counts": normalization["normalized_batches"][1]["counts"],
                "batch_hash_verified": True,
            },
        ],
        "reconstructed_output_file": reconstructed_output_path.name,
        "reconstructed_output_sha256": reconstructed_hash,
        "merge_statistics": {
            "input_counts": normalization["summary"]["aggregate_counts"],
            "output_counts": {
                "reports": 1,
                "encounters": 14,
                "actors": 31,
                "participants": 31,
                "aura_events": 0,
                "rejects": 0,
            },
            "duplicate_records_merged": {
                "reports": 1,
                "encounters": 1,
                "actors": 0,
                "participants": 0,
            },
            "complementary_fields_filled": {
                "reports": 9,
                "encounters": 1,
                "actors": 0,
                "participants": 0,
            },
            "field_conflict_count": 0,
        },
        "linkage_checks": {
            "all_encounters_reference_report": True,
            "exact_encounter_fields_preserved": True,
            "exact_encounter_reconstructed": True,
            "participant_actor_references_resolved": True,
            "participant_encounter_references_resolved": True,
            "participant_pairs_unique": True,
            "report_fields_preserved": True,
            "single_participant_encounter": True,
            "single_report_reconstructed": True,
        },
        "decision_boundary": {
            "status": "reconstructed_parser_slice",
            "deterministic_reconstruction_completed": True,
            "ready_for_selected_parser_persistence": True,
            "automatic_commit": False,
            "mechanic_semantics_verified": False,
            "combatants_info_enrichment_available": False,
            "aura_reconstruction_available": False,
            "full_report_slice_complete": False,
            "reconstructed_file_contains_source_scalar_values": True,
        },
        "summary": {
            "source_batch_count": 2,
            "input_counts": normalization["summary"]["aggregate_counts"],
            "output_counts": {
                "reports": 1,
                "encounters": 14,
                "actors": 31,
                "participants": 31,
                "aura_events": 0,
                "rejects": 0,
            },
            "duplicate_report_count": 1,
            "duplicate_encounter_count": 1,
            "field_conflict_count": 0,
            "all_input_batch_hashes_verified": True,
            "all_linkage_checks_passed": True,
            "contains_source_scalar_values": False,
            "reconstructed_file_contains_source_scalar_values": True,
            "ready_for_selected_parser_persistence": True,
            "mechanic_semantics_verified": False,
            "full_report_slice_complete": False,
        },
    }
    reconstruction_path = tmp_path / "observed-report-slice-reconstruction.json"
    _write_json(reconstruction_path, reconstruction)

    apply_migrations(database, migrations)
    with duckdb.connect(str(database)) as connection:
        for raw_id, payload_hash in (("7" * 64, REPORT_PAYLOAD_HASH), ("8" * 64, ENCOUNTER_PAYLOAD_HASH)):
            connection.execute(
                """
                INSERT INTO raw_object (
                    raw_id, endpoint_id, request_key, payload_hash, storage_path,
                    fetched_at, http_status, normalizer_status, metadata_json
                ) VALUES (?, NULL, ?, ?, ?, ?, 200, 'pending', '{}')
                """,
                [
                    raw_id,
                    f"fixture:{payload_hash}",
                    payload_hash,
                    f"fixture/{payload_hash}.json.gz",
                    "2026-07-29T12:00:00Z",
                ],
            )

    return {
        "migrations": migrations,
        "database": database,
        "mapping_dir": mapping_dir,
        "normalization": normalization_path,
        "reconstruction": reconstruction_path,
        "reconstructed_output": reconstructed_output_path,
    }


def test_persistence_writes_core_entities_and_private_observations(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    receipt = persist_observed_report_slice(
        fixture["reconstruction"],
        fixture["reconstructed_output"],
        fixture["normalization"],
        mapping_dir=fixture["mapping_dir"],
        database_path=fixture["database"],
        migrations_dir=fixture["migrations"],
    )

    assert receipt["persisted_counts"] == {
        "reports": 1,
        "encounters": 14,
        "actors": 31,
        "participants": 31,
        "aura_events": 0,
        "rejects": 0,
    }
    assert receipt["summary"]["canonical_entity_observation_count"] == 77
    assert all(receipt["integrity_checks"].values())
    serialized = json.dumps(receipt)
    assert "PRIVATE REPORT" not in serialized
    assert "PRIVATE ACTOR" not in serialized

    with duckdb.connect(str(fixture["database"])) as connection:
        assert connection.execute("SELECT COUNT(*) FROM report").fetchone()[0] == 1
        assert connection.execute("SELECT COUNT(*) FROM encounter").fetchone()[0] == 14
        assert connection.execute("SELECT COUNT(*) FROM actor").fetchone()[0] == 31
        assert connection.execute("SELECT COUNT(*) FROM participant").fetchone()[0] == 31
        assert connection.execute("SELECT COUNT(*) FROM observation_batch").fetchone()[0] == 2
        assert connection.execute("SELECT COUNT(*) FROM normalization_run").fetchone()[0] == 2
        assert connection.execute("SELECT COUNT(*) FROM normalization_mapping").fetchone()[0] == 2
        assert connection.execute(
            "SELECT COUNT(*) FROM canonical_entity_observation"
        ).fetchone()[0] == 77
        private_json = connection.execute(
            "SELECT entity_json FROM canonical_entity_observation WHERE entity_type = 'reports'"
        ).fetchone()[0]
        assert "PRIVATE REPORT" in private_json
        assert connection.execute(
            "SELECT COUNT(*) FROM parser_slice_persistence_run"
        ).fetchone()[0] == 1


def test_persistence_rolls_back_on_existing_core_conflict(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    with duckdb.connect(str(fixture["database"])) as connection:
        connection.execute(
            """
            INSERT INTO report (
                report_id, source_report_id, raid_date, created_at, status, payload_hash, raw_id
            ) VALUES (?, '77', DATE '2026-07-29', TIMESTAMP '2026-07-29 12:00:00',
                      'conflicting', ?, ?)
            """,
            [REPORT_ID, REPORT_PAYLOAD_HASH, "7" * 64],
        )

    with pytest.raises(ValueError, match="report.status conflicts"):
        persist_observed_report_slice(
            fixture["reconstruction"],
            fixture["reconstructed_output"],
            fixture["normalization"],
            mapping_dir=fixture["mapping_dir"],
            database_path=fixture["database"],
            migrations_dir=fixture["migrations"],
        )

    with duckdb.connect(str(fixture["database"])) as connection:
        assert connection.execute("SELECT COUNT(*) FROM observation_batch").fetchone()[0] == 0
        assert connection.execute("SELECT COUNT(*) FROM normalization_run").fetchone()[0] == 0
        assert connection.execute("SELECT COUNT(*) FROM normalization_mapping").fetchone()[0] == 0
        assert connection.execute(
            "SELECT COUNT(*) FROM canonical_entity_observation"
        ).fetchone()[0] == 0
        assert connection.execute(
            "SELECT COUNT(*) FROM parser_slice_persistence_run"
        ).fetchone()[0] == 0
