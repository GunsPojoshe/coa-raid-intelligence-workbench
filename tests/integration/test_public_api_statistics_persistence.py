from __future__ import annotations

from pathlib import Path

import pytest

from coa_workbench.analytics.public_api_population_priors import (
    population_prior_public_summary,
    read_public_api_population_priors,
)
from coa_workbench.normalizer.public_api_statistics import parse_public_api_statistics
from coa_workbench.storage.migrations import apply_migrations
from coa_workbench.storage.public_api_statistics import persist_public_api_statistics


duckdb = pytest.importorskip("duckdb")


def _metric(base: float, parses: int) -> dict[str, object]:
    return {
        "avg": base,
        "median": base - 1,
        "max": base + 5,
        "min": base - 5,
        "total_parses": parses,
        "percentiles": {"50": base - 1, "95": base + 4},
    }


def _batch():
    return parse_public_api_statistics(
        {
            "success": True,
            "phase": 12,
            "difficulty": "all",
            "metric": "avg_dps",
            "bracket": "all",
            "location": None,
            "boss_id": None,
            "damage_mode": "standard",
            "week_number": None,
            "day_number": None,
            "statistics": {
                "PrivateClass": {
                    "total_parses": 30,
                    "summary_a": 1,
                    "summary_b": 2.0,
                    "summary_c": 3,
                    "specs": {
                        "PrivateSpecOne": _metric(100.0, 20),
                        "PrivateSpecTwo": _metric(80.0, 10),
                    },
                }
            },
        },
        query_keys=("phase", "difficulty", "metric", "bracket", "damageMode", "role"),
        query_values={
            "phase": "12",
            "difficulty": "all",
            "metric": "avg_dps",
            "bracket": "all",
            "damageMode": "standard",
            "role": "dps",
        },
    )


def test_public_api_statistics_persistence_replays_idempotently_and_reads_priors(
    tmp_path: Path,
) -> None:
    root = Path(__file__).resolve().parents[2]
    database = tmp_path / "coa.duckdb"
    migrations = root / "migrations"
    apply_migrations(database, migrations)
    raw_id = "private-raw-id"
    with duckdb.connect(str(database)) as connection:
        connection.execute(
            """
            INSERT INTO raw_object (
                raw_id, request_key, payload_hash, storage_path, fetched_at
            ) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            [raw_id, "private-request", "private-payload-hash", "private/path.json.gz"],
        )

    first = persist_public_api_statistics(
        database_path=database,
        migrations_path=migrations,
        source_raw_id=raw_id,
        source_code="private_source",
        batch=_batch(),
    )
    second = persist_public_api_statistics(
        database_path=database,
        migrations_path=migrations,
        source_raw_id=raw_id,
        source_code="private_source",
        batch=_batch(),
    )

    assert first["batch_inserted"] is True
    assert first["class_rows_inserted"] == 1
    assert first["spec_rows_inserted"] == 2
    assert second["batch_matched"] is True
    assert second["class_rows_inserted"] == 0
    assert second["class_rows_matched"] == 1
    assert second["spec_rows_inserted"] == 0
    assert second["spec_rows_matched"] == 2
    assert second["contains_source_scalar_values"] is False
    assert second["contains_source_raw_id"] is False

    snapshot = read_public_api_population_priors(
        database,
        phase=12,
        difficulty="all",
        metric="avg_dps",
        damage_mode="standard",
        role="dps",
    )
    assert len(snapshot.records) == 2
    assert sum(row.local_parse_share or 0.0 for row in snapshot.records) == pytest.approx(1.0)
    assert snapshot.records[0].total_parses == 20
    assert snapshot.records[0].local_parse_share == pytest.approx(2 / 3)

    public_summary = population_prior_public_summary(snapshot)
    assert public_summary["record_count"] == 2
    assert public_summary["derived_local_parse_share_available"] is True
    assert public_summary["contains_dimension_values"] is False
    assert public_summary["contains_class_names"] is False
    assert public_summary["contains_spec_names"] is False
    assert public_summary["contains_metric_scalar_values"] is False
    assert public_summary["planner_scoring_allowed"] is False

    with duckdb.connect(str(database)) as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM public_api_statistics_batch"
        ).fetchone()[0] == 1
        assert connection.execute(
            "SELECT COUNT(*) FROM analysis_run WHERE analysis_type = ?",
            ["official_public_api_population_statistics"],
        ).fetchone()[0] == 1
        assert connection.execute(
            "SELECT COUNT(*) FROM artifact_dependency WHERE dependency_type = 'raw_object'"
        ).fetchone()[0] >= 1
