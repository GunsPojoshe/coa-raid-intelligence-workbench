from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from coa_workbench.collector.raw_archive import RawArchive, request_key_from_url
from coa_workbench.collector.source_observatory import ReviewedGetContract, observe_raw_capture


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


def _observe(
    *,
    archive: RawArchive,
    database: Path,
    migrations: Path,
    url: str,
    payload: dict[str, object],
    observed_at: datetime,
):
    body = json.dumps(payload, sort_keys=True).encode()
    contract = _contract()
    capture = archive.capture_bytes(
        body,
        source_code=contract.source_code,
        endpoint_code=contract.endpoint_code,
        request_key=request_key_from_url("GET", url),
        fetched_at=observed_at,
        http_status=200,
        content_type="application/json",
        request_url=url,
    )
    return observe_raw_capture(
        database,
        migrations,
        contract=contract,
        capture=capture,
        payload=body,
        request_url=url,
    )


def _change_types(database: Path, capture_id: str) -> list[str]:
    with duckdb.connect(str(database), read_only=True) as connection:
        return [
            str(row[0])
            for row in connection.execute(
                """
                SELECT change_type
                FROM source_change_event
                WHERE capture_id = ?
                ORDER BY change_type
                """,
                [capture_id],
            ).fetchall()
        ]


def test_schema_diffs_are_compared_only_within_reviewed_query_profile(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[2]
    migrations = root / "migrations"
    database = tmp_path / "coa.duckdb"
    archive = RawArchive(
        tmp_path / "raw",
        database_path=database,
        migrations_dir=migrations,
    )

    damage = _observe(
        archive=archive,
        database=database,
        migrations=migrations,
        url=(
            "https://coa.ascensionlogs.gg/api/reports/1/encounters/2/throughput-timeline"
            "?bucket_size_ms=1000&metric=damage"
        ),
        payload={"series": [{"damage": 10}]},
        observed_at=datetime(2026, 8, 14, 12, 0, tzinfo=timezone.utc),
    )
    assert _change_types(database, damage.source_capture_id) == ["endpoint_added"]

    healing = _observe(
        archive=archive,
        database=database,
        migrations=migrations,
        url=(
            "https://coa.ascensionlogs.gg/api/reports/1/encounters/2/throughput-timeline"
            "?bucket_size_ms=1000&metric=healing"
        ),
        payload={"series": [{"healing": 20, "targets": []}]},
        observed_at=datetime(2026, 8, 14, 12, 1, tzinfo=timezone.utc),
    )
    assert _change_types(database, healing.source_capture_id) == [
        "observation_profile_added"
    ]

    changed_damage = _observe(
        archive=archive,
        database=database,
        migrations=migrations,
        url=(
            "https://coa.ascensionlogs.gg/api/reports/9/encounters/8/throughput-timeline"
            "?bucket_size_ms=5000&metric=damage"
        ),
        payload={"series": [{"damage": "10", "new_field": True}]},
        observed_at=datetime(2026, 8, 14, 12, 2, tzinfo=timezone.utc),
    )
    changed_types = set(_change_types(database, changed_damage.source_capture_id))
    assert "schema_changed" in changed_types
    assert "field_added" in changed_types
    assert "field_type_changed" in changed_types
    assert "observation_profile_added" not in changed_types

    with duckdb.connect(str(database), read_only=True) as connection:
        metadata_rows = [
            json.loads(str(row[0]))
            for row in connection.execute(
                """
                SELECT metadata_json
                FROM source_schema_snapshot
                WHERE endpoint_code = 'report_encounter_throughput_timeline_api'
                ORDER BY observed_at
                """
            ).fetchall()
        ]
    assert all("observation_profile_key" in row for row in metadata_rows)
    assert all(row["schema_profile_keys"] == ["metric", "perspective"] for row in metadata_rows)
