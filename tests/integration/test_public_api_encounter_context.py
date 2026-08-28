from __future__ import annotations

import json
from pathlib import Path

import pytest

from coa_workbench.analytics.public_api_encounter_context import (
    PUBLIC_API_ENCOUNTER_CONTEXT_V1,
    review_public_api_encounter_context,
)
from coa_workbench.normalizer.public_api_statistics import (
    PUBLIC_API_STATISTICS_NORMALIZER_VERSION,
)
from coa_workbench.storage.migrations import apply_migrations


duckdb = pytest.importorskip("duckdb")


def _insert_batch(
    connection,
    *,
    index: int,
    phase: int = 12,
    difficulty: str = "ascended",
    location: str = "Example Raid",
    boss_id: int = 9001,
    provenance_complete: bool = True,
) -> None:
    context_slice = PUBLIC_API_ENCOUNTER_CONTEXT_V1[index]
    suffix = f"{phase}-{difficulty}-{boss_id}-{index}"
    batch_id = f"batch-{suffix}"
    raw_id = f"raw-{suffix}"
    connection.execute(
        """
        INSERT INTO raw_object (
            raw_id, request_key, payload_hash, storage_path, fetched_at
        ) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        """,
        [raw_id, f"request-{suffix}", f"payload-{suffix}", f"private/{raw_id}.gz"],
    )
    connection.execute(
        """
        INSERT INTO public_api_statistics_batch (
            batch_id, raw_id, source_code, endpoint_code, normalizer_version,
            phase_number, difficulty, metric, bracket, location, boss_id,
            damage_mode, role, class_filter, spec_filter, week_number, realm,
            day_number, class_count, spec_record_count, percentile_value_count,
            output_fingerprint, metadata_json
        ) VALUES (?, ?, ?, 'public_api_statistics', ?, ?, ?, ?, 'all', ?, ?,
                  'standard', ?, NULL, NULL, NULL, NULL, NULL, ?, ?, ?, ?, '{}')
        """,
        [
            batch_id,
            raw_id,
            "coa_ascension_logs_public_api",
            PUBLIC_API_STATISTICS_NORMALIZER_VERSION,
            phase,
            difficulty,
            context_slice.metric,
            location,
            boss_id,
            context_slice.role,
            index + 1,
            (index + 1) * 2,
            (index + 1) * 3,
            f"fingerprint-{suffix}",
        ],
    )
    if not provenance_complete:
        return

    connection.execute(
        """
        INSERT INTO analysis_run (
            analysis_run_id, analysis_type, analysis_version, artifact_type,
            artifact_key, target_scope_json, input_fingerprint, output_fingerprint,
            status, metadata_json, finished_at
        ) VALUES (?, 'official_public_api_population_statistics', 'test-v1',
                  'public_api_population_statistics', ?, '{}', ?, ?, 'completed', '{}',
                  CURRENT_TIMESTAMP)
        """,
        [f"analysis-{suffix}", batch_id, raw_id, f"output-{suffix}"],
    )
    connection.execute(
        """
        INSERT INTO artifact_dependency (
            dependency_id, artifact_type, artifact_key, analysis_type, analysis_version,
            dependency_type, dependency_key, dependency_version, active, metadata_json
        ) VALUES (?, 'public_api_population_statistics', ?,
                  'official_public_api_population_statistics', 'test-v1',
                  'raw_object', ?, ?, TRUE, '{}')
        """,
        [
            f"raw-dependency-{suffix}",
            batch_id,
            raw_id,
            PUBLIC_API_STATISTICS_NORMALIZER_VERSION,
        ],
    )
    connection.execute(
        """
        INSERT INTO artifact_dependency (
            dependency_id, artifact_type, artifact_key, analysis_type, analysis_version,
            dependency_type, dependency_key, dependency_version, active, metadata_json
        ) VALUES (?, 'public_api_population_statistics', ?,
                  'official_public_api_population_statistics', 'test-v1',
                  'source_endpoint_profile', 'public_api_statistics', ?, TRUE, '{}')
        """,
        [f"profile-dependency-{suffix}", batch_id, f"private-profile-{suffix}"],
    )


def test_encounter_context_requires_exact_scope_and_complete_provenance(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[2]
    database = tmp_path / "coa.duckdb"
    migrations = root / "migrations"
    apply_migrations(database, migrations)

    empty = review_public_api_encounter_context(
        database,
        migrations,
        phase=12,
        difficulty="ascended",
        location="Example Raid",
        boss_id=9001,
    )
    assert empty.missing_slice_indexes == (0, 1, 2, 3)

    with duckdb.connect(str(database)) as connection:
        _insert_batch(connection, index=0)
        _insert_batch(connection, index=1, difficulty="all")
        _insert_batch(connection, index=2, boss_id=9002)
        _insert_batch(connection, index=3, provenance_complete=False)

    partial = review_public_api_encounter_context(
        database,
        migrations,
        phase=12,
        difficulty="ascended",
        location="Example Raid",
        boss_id=9001,
    )
    assert partial.covered_slice_indexes == (0,)
    assert partial.missing_slice_indexes == (1, 2, 3)

    with duckdb.connect(str(database)) as connection:
        _insert_batch(connection, index=1)
        _insert_batch(connection, index=2)
        connection.execute(
            "DELETE FROM public_api_statistics_batch WHERE batch_id = 'batch-12-ascended-9001-3'"
        )
        connection.execute("DELETE FROM raw_object WHERE raw_id = 'raw-12-ascended-9001-3'")
        _insert_batch(connection, index=3)

    complete = review_public_api_encounter_context(
        database,
        migrations,
        phase=12,
        difficulty="ascended",
        location="Example Raid",
        boss_id=9001,
    )
    assert complete.covered_slice_indexes == (0, 1, 2, 3)
    assert complete.missing_slice_indexes == ()
    assert complete.selected_batch_count == 4
    assert complete.complete is True

    rendered = json.dumps(complete.public_summary(), sort_keys=True)
    for private_value in ("Example Raid", "9001", "ascended", "avg_dps", "support"):
        assert private_value not in rendered
