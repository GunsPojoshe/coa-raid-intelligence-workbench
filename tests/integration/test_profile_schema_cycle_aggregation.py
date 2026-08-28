from __future__ import annotations

import json
from pathlib import Path

import pytest

from coa_workbench.collector.profile_schema_cycle import (
    aggregate_profile_schema_observations,
)
from coa_workbench.collector.raw_archive import RawArchive
from coa_workbench.collector.source_acquisition import observe_reviewed_har
from coa_workbench.collector.source_observatory import (
    ReviewedGetContract,
    register_artifact_dependency,
)


duckdb = pytest.importorskip("duckdb")


def _contract() -> ReviewedGetContract:
    return ReviewedGetContract(
        source_code="coa_ascension_logs",
        endpoint_code="report_encounter_throughput_timeline_api",
        base_url="https://coa.ascensionlogs.gg",
        route_template=(
            "/api/reports/{reportId}/encounters/{encounterId}/throughput-timeline"
        ),
        parameter_keys=("bucket_size_ms", "metric", "perspective"),
        schema_profile_keys=("metric", "perspective"),
        auth_state="browser_context_observed",
        discovery_source="test",
        review_state="verified",
        logical_name="throughput",
    )


def _entry(path: str, body: dict[str, object], timestamp: str) -> dict[str, object]:
    return {
        "startedDateTime": timestamp,
        "_resourceType": "xhr",
        "request": {
            "method": "GET",
            "url": f"https://coa.ascensionlogs.gg{path}",
        },
        "response": {
            "status": 200,
            "content": {
                "mimeType": "application/json",
                "text": json.dumps(body),
            },
        },
    }


def _write_har(path: Path, entries: list[dict[str, object]]) -> None:
    path.write_text(json.dumps({"log": {"entries": entries}}), encoding="utf-8")


def _ingest_cycle(
    *,
    har: Path,
    archive: RawArchive,
    database: Path,
    migrations: Path,
) -> dict[str, object]:
    contract = _contract()
    observations = observe_reviewed_har(
        har,
        archive=archive,
        database_path=database,
        migrations_dir=migrations,
        contract=contract,
    )
    summary = aggregate_profile_schema_observations(
        database,
        migrations,
        contract=contract,
        observations=observations,
        metadata={"capture_mode": "browser_har"},
    )
    return summary.public_summary()


def test_profile_cycle_aggregates_optional_fields_and_reanalysis(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[2]
    migrations = root / "migrations"
    database = tmp_path / "coa.duckdb"
    archive = RawArchive(
        tmp_path / "raw",
        database_path=database,
        migrations_dir=migrations,
    )
    first_har = tmp_path / "first.har"
    second_har = tmp_path / "second.har"

    _write_har(
        first_har,
        [
            _entry(
                "/api/reports/1/encounters/1/throughput-timeline?metric=damage",
                {
                    "success": True,
                    "series": {"10": [{"value": 1, "optional": None}]},
                },
                "2026-08-14T12:00:00.000Z",
            ),
            _entry(
                "/api/reports/1/encounters/2/throughput-timeline?metric=damage",
                {
                    "success": True,
                    "series": {"20": [{"value": 2}]},
                },
                "2026-08-14T12:00:01.000Z",
            ),
        ],
    )

    first = _ingest_cycle(
        har=first_har,
        archive=archive,
        database=database,
        migrations=migrations,
    )
    assert first["profile_cycle_count"] == 1
    assert first["member_capture_count"] == 2
    assert first["superseded_member_event_count"] >= 1
    assert first["aggregate_change_event_count"] == 0

    with duckdb.connect(str(database), read_only=True) as connection:
        open_types = [
            str(row[0])
            for row in connection.execute(
                """
                SELECT change_type
                FROM source_change_event
                WHERE endpoint_code = 'report_encounter_throughput_timeline_api'
                  AND status = 'open'
                ORDER BY change_type
                """
            ).fetchall()
        ]
        assert open_types == ["endpoint_added"]

        cycle_row = connection.execute(
            """
            SELECT member_capture_count, path_types_json
            FROM source_profile_schema_cycle
            WHERE endpoint_code = 'report_encounter_throughput_timeline_api'
            """
        ).fetchone()
        assert cycle_row is not None
        assert int(cycle_row[0]) == 2
        cycle_paths = json.loads(str(cycle_row[1]))
        assert "/series/{integer-key}/*/optional" in cycle_paths

    register_artifact_dependency(
        database,
        migrations,
        artifact_type="test_profile_artifact",
        artifact_key="report-scope",
        analysis_type="test_profile_analysis",
        analysis_version="v1",
        dependency_type="source_endpoint",
        dependency_key="report_encounter_throughput_timeline_api",
    )

    _write_har(
        second_har,
        [
            _entry(
                "/api/reports/1/encounters/3/throughput-timeline?metric=damage",
                {
                    "success": True,
                    "series": {
                        "30": [
                            {
                                "value": 3,
                                "optional": "present",
                                "new_field": True,
                            }
                        ]
                    },
                },
                "2026-08-14T13:00:00.000Z",
            ),
            _entry(
                "/api/reports/1/encounters/4/throughput-timeline?metric=damage",
                {
                    "success": True,
                    "series": {"40": [{"value": 4, "new_field": False}]},
                },
                "2026-08-14T13:00:01.000Z",
            ),
        ],
    )

    second = _ingest_cycle(
        har=second_har,
        archive=archive,
        database=database,
        migrations=migrations,
    )
    assert second["profile_cycle_count"] == 1
    assert second["member_capture_count"] == 2
    assert second["superseded_member_event_count"] >= 1
    assert second["superseded_reanalysis_request_count"] >= 1
    assert second["aggregate_change_event_count"] == 3
    assert second["aggregate_reanalysis_request_count"] == 3

    with duckdb.connect(str(database), read_only=True) as connection:
        aggregate_open = connection.execute(
            """
            SELECT change_type, subject_path
            FROM source_change_event
            WHERE endpoint_code = 'report_encounter_throughput_timeline_api'
              AND status = 'open'
              AND json_extract_string(metadata_json, '$.schema_cycle_aggregated') = 'true'
            ORDER BY change_type, subject_path
            """
        ).fetchall()
        assert aggregate_open == [
            ("field_added", "/series/{integer-key}/*/new_field"),
            ("field_type_changed", "/series/{integer-key}/*/optional"),
            ("schema_changed", None),
        ]

        pending = connection.execute(
            """
            SELECT COUNT(*)
            FROM reanalysis_request AS r
            JOIN source_change_event AS e ON e.event_id = r.reason_event_id
            WHERE r.status = 'pending'
              AND json_extract_string(e.metadata_json, '$.schema_cycle_aggregated') = 'true'
            """
        ).fetchone()[0]
        assert int(pending) == 3

        superseded_requests = connection.execute(
            """
            SELECT COUNT(*)
            FROM reanalysis_request
            WHERE status = 'superseded_profile_cycle_aggregation'
            """
        ).fetchone()[0]
        assert int(superseded_requests) >= 1

    replay = _ingest_cycle(
        har=second_har,
        archive=archive,
        database=database,
        migrations=migrations,
    )
    assert replay["profile_cycle_count"] == 0
    assert replay["aggregate_change_event_count"] == 0
    assert replay["aggregate_reanalysis_request_count"] == 0

    with duckdb.connect(str(database), read_only=True) as connection:
        assert (
            connection.execute(
                "SELECT COUNT(*) FROM source_profile_schema_cycle"
            ).fetchone()[0]
            == 2
        )
        assert (
            connection.execute(
                "SELECT COUNT(*) FROM reanalysis_request WHERE status = 'pending'"
            ).fetchone()[0]
            == 3
        )
