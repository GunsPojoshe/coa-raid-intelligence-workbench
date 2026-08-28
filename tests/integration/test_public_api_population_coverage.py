from __future__ import annotations

import json
from pathlib import Path

import pytest

from coa_workbench.analytics.public_api_population_coverage import (
    PUBLIC_API_POPULATION_COVERAGE_V1,
    review_public_api_population_coverage,
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
    provenance_complete: bool = True,
) -> None:
    coverage_slice = PUBLIC_API_POPULATION_COVERAGE_V1[index]
    batch_id = f"batch-{phase}-{index}"
    raw_id = f"raw-{phase}-{index}"
    connection.execute(
        """
        INSERT INTO raw_object (
            raw_id, request_key, payload_hash, storage_path, fetched_at
        ) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        """,
        [raw_id, f"request-{phase}-{index}", f"payload-{phase}-{index}", f"private/{raw_id}.gz"],
    )
    connection.execute(
        """
        INSERT INTO public_api_statistics_batch (
            batch_id, raw_id, source_code, endpoint_code, normalizer_version,
            phase_number, difficulty, metric, bracket, location, boss_id,
            damage_mode, role, class_filter, spec_filter, week_number, realm,
            day_number, class_count, spec_record_count, percentile_value_count,
            output_fingerprint, metadata_json
        ) VALUES (?, ?, ?, 'public_api_statistics', ?, ?, ?, ?, ?, NULL, NULL,
                  ?, ?, NULL, NULL, NULL, NULL, NULL, ?, ?, ?, ?, '{}')
        """,
        [
            batch_id,
            raw_id,
            "coa_ascension_logs_public_api",
            PUBLIC_API_STATISTICS_NORMALIZER_VERSION,
            phase,
            coverage_slice.difficulty,
            coverage_slice.metric,
            coverage_slice.bracket,
            coverage_slice.damage_mode,
            coverage_slice.role,
            index + 1,
            (index + 1) * 2,
            (index + 1) * 3,
            f"fingerprint-{phase}-{index}",
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
        [
            f"analysis-{phase}-{index}",
            batch_id,
            raw_id,
            f"output-{phase}-{index}",
        ],
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
            f"raw-dependency-{phase}-{index}",
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
        [
            f"profile-dependency-{phase}-{index}",
            batch_id,
            f"private-profile-{phase}-{index}",
        ],
    )


def test_population_coverage_counts_only_provenance_complete_current_phase_plan(
    tmp_path: Path,
) -> None:
    root = Path(__file__).resolve().parents[2]
    database = tmp_path / "coa.duckdb"
    migrations = root / "migrations"
    apply_migrations(database, migrations)

    empty = review_public_api_population_coverage(database, migrations, phase=12)
    assert empty.required_slice_count == 4
    assert empty.covered_slice_indexes == ()
    assert empty.missing_slice_indexes == (0, 1, 2, 3)
    assert empty.complete is False

    with duckdb.connect(str(database)) as connection:
        _insert_batch(connection, index=0)
        _insert_batch(connection, index=2)
        _insert_batch(connection, index=1, phase=11)
        _insert_batch(connection, index=3, provenance_complete=False)

    partial = review_public_api_population_coverage(database, migrations, phase=12)
    assert partial.covered_slice_indexes == (0, 2)
    assert partial.missing_slice_indexes == (1, 3)
    assert partial.selected_batch_count == 2
    assert partial.aggregate_class_count == 4
    assert partial.aggregate_spec_record_count == 8
    assert partial.aggregate_percentile_value_count == 12

    with duckdb.connect(str(database)) as connection:
        _insert_batch(connection, index=1)
        connection.execute(
            "DELETE FROM public_api_statistics_batch WHERE batch_id = 'batch-12-3'"
        )
        connection.execute("DELETE FROM raw_object WHERE raw_id = 'raw-12-3'")
        _insert_batch(connection, index=3)

    complete = review_public_api_population_coverage(database, migrations, phase=12)
    assert complete.covered_slice_indexes == (0, 1, 2, 3)
    assert complete.missing_slice_indexes == ()
    assert complete.selected_batch_count == 4
    assert complete.complete is True

    public = complete.public_summary()
    assert public["required_slice_count"] == 4
    assert public["covered_slice_count"] == 4
    assert public["missing_slice_count"] == 0
    assert public["metric_family_count"] == 3
    assert public["role_qualified_required_slice_count"] == 3
    assert public["role_omitted_required_slice_count"] == 1
    assert public["bounded_capture_plan"] is True
    assert public["bulk_dataset_mode"] is False
    assert public["provenance_complete_batches_required"] is True
    assert public["phase_values_included"] is False
    assert public["difficulty_values_included"] is False
    assert public["metric_values_included"] is False
    assert public["role_values_included"] is False
    assert public["planner_scoring_allowed"] is False

    rendered = json.dumps(public, sort_keys=True)
    for private_value in ("avg_dps", "avg_hps", "avg_dtps", "support", "tank"):
        assert private_value not in rendered
