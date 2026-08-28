from __future__ import annotations

import json
from pathlib import Path

import pytest

from coa_workbench.analytics.public_api_encounter_comparator import (
    PUBLIC_API_LOCATION_COMPARATOR_V1,
    build_public_api_encounter_location_comparator,
    review_public_api_location_comparator,
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
    boss_id: int | None,
    day_number: int = 4,
) -> None:
    context_slice = PUBLIC_API_LOCATION_COMPARATOR_V1[index]
    scope = "encounter" if boss_id is not None else "location"
    batch_id = f"batch-{scope}-{index}"
    raw_id = f"raw-{scope}-{index}"
    profile_key = f"private-profile-{scope}-{index}"
    connection.execute(
        """
        INSERT INTO raw_object (
            raw_id, request_key, payload_hash, storage_path, fetched_at
        ) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        """,
        [raw_id, f"request-{scope}-{index}", f"payload-{scope}-{index}", f"private/{raw_id}.gz"],
    )
    connection.execute(
        """
        INSERT INTO public_api_statistics_batch (
            batch_id, raw_id, source_code, endpoint_code, normalizer_version,
            phase_number, difficulty, metric, bracket, location, boss_id,
            damage_mode, role, class_filter, spec_filter, week_number, realm,
            day_number, class_count, spec_record_count, percentile_value_count,
            output_fingerprint, metadata_json
        ) VALUES (?, ?, 'coa_ascension_logs_public_api', 'public_api_statistics', ?,
                  12, 'ascended', ?, 'all', 'Example Raid', ?, 'standard', ?,
                  NULL, NULL, NULL, NULL, ?, 2, 2, 2, ?, '{}')
        """,
        [
            batch_id,
            raw_id,
            PUBLIC_API_STATISTICS_NORMALIZER_VERSION,
            context_slice.metric,
            boss_id,
            context_slice.role,
            day_number,
            f"output-{scope}-{index}",
        ],
    )
    if boss_id is None:
        rows = (
            ("Alpha", "One", 80.0, 75.0, 90.0, 60.0, 50),
            ("Gamma", "Three", 300.0, 250.0, 350.0, 200.0, 50),
        )
    else:
        rows = (
            ("Alpha", "One", 100.0, 90.0, 120.0, 70.0, 30),
            ("Beta", "Two", 200.0, 180.0, 240.0, 150.0, 70),
        )
    for class_name, spec_name, avg, median, maximum, minimum, total_parses in rows:
        connection.execute(
            """
            INSERT INTO public_api_statistics_spec (
                batch_id, class_name, spec_name, avg, median, max, min,
                total_parses, percentiles_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, '{"p50": 1.0}')
            """,
            [
                batch_id,
                class_name,
                spec_name,
                avg,
                median,
                maximum,
                minimum,
                total_parses,
            ],
        )
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
        [f"analysis-{scope}-{index}", batch_id, raw_id, f"analysis-output-{scope}-{index}"],
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
            f"raw-dependency-{scope}-{index}",
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
        [f"profile-dependency-{scope}-{index}", batch_id, profile_key],
    )


def _database(tmp_path: Path) -> tuple[Path, Path]:
    root = Path(__file__).resolve().parents[2]
    database = tmp_path / "coa.duckdb"
    migrations = root / "migrations"
    apply_migrations(database, migrations)
    return database, migrations


def test_location_comparator_and_differential_require_exact_provenance_complete_slices(
    tmp_path: Path,
) -> None:
    database, migrations = _database(tmp_path)

    empty = review_public_api_location_comparator(
        database,
        migrations,
        phase=12,
        difficulty="ascended",
        location="Example Raid",
    )
    assert empty.missing_slice_indexes == (0, 1, 2, 3)

    with duckdb.connect(str(database)) as connection:
        for index in range(4):
            _insert_batch(connection, index=index, boss_id=501)
            _insert_batch(connection, index=index, boss_id=None)

    complete = review_public_api_location_comparator(
        database,
        migrations,
        phase=12,
        difficulty="ascended",
        location="Example Raid",
    )
    assert complete.covered_slice_indexes == (0, 1, 2, 3)
    assert complete.complete is True

    comparator = build_public_api_encounter_location_comparator(
        database,
        migrations,
        phase=12,
        difficulty="ascended",
        location="Example Raid",
        boss_id=501,
    )
    assert comparator.slice_count == 4
    assert comparator.matched_record_count == 4
    assert comparator.encounter_only_record_count == 4
    assert comparator.location_only_record_count == 4

    first = comparator.records[0]
    assert first.class_name == "Alpha"
    assert first.spec_name == "One"
    assert first.parse_share_delta == pytest.approx(-0.2)
    assert first.parse_share_ratio == pytest.approx(0.6)
    assert first.avg_delta == pytest.approx(20.0)
    assert first.avg_ratio == pytest.approx(1.25)
    assert first.median_delta == pytest.approx(15.0)
    assert first.median_ratio == pytest.approx(1.2)

    public = comparator.public_summary()
    assert public["exact_dimension_match_required"] is True
    assert public["temporal_scope_match_required"] is True
    assert public["missing_spec_treated_as_zero"] is False
    assert public["planner_scoring_allowed"] is False
    rendered = json.dumps(public, sort_keys=True)
    for private_value in ("Alpha", "One", "Example Raid", "ascended", "0.6", "20.0"):
        assert private_value not in rendered


def test_comparator_fails_closed_when_capture_day_differs(tmp_path: Path) -> None:
    database, migrations = _database(tmp_path)
    with duckdb.connect(str(database)) as connection:
        for index in range(4):
            _insert_batch(connection, index=index, boss_id=501, day_number=4)
            _insert_batch(
                connection,
                index=index,
                boss_id=None,
                day_number=5 if index == 2 else 4,
            )

    with pytest.raises(ValueError, match="day_number"):
        build_public_api_encounter_location_comparator(
            database,
            migrations,
            phase=12,
            difficulty="ascended",
            location="Example Raid",
            boss_id=501,
        )
