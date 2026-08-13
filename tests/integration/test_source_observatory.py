from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from coa_workbench.collector.raw_archive import RawArchive, request_key_from_url
from coa_workbench.collector.source_observatory import (
    ReviewedGetContract,
    observe_raw_capture,
    register_artifact_dependency,
)


duckdb = pytest.importorskip("duckdb")


def _contract() -> ReviewedGetContract:
    return ReviewedGetContract(
        source_code="coa_logs",
        endpoint_code="guild_progression_rankings",
        base_url="https://coa.ascensionlogs.gg",
        route_template="/api/guilds/progression/rankings",
        parameter_keys=("bracket", "difficulty", "location", "phaseId", "realm"),
        auth_state="none",
        discovery_source="archived_spa_review",
        review_state="verified",
        logical_name="Guild progression rankings",
    )


def _observe(
    *,
    archive: RawArchive,
    database: Path,
    migrations: Path,
    contract: ReviewedGetContract,
    payload: dict[str, object],
    observed_at: datetime,
):
    body = json.dumps(payload, sort_keys=True).encode()
    url = "https://coa.ascensionlogs.gg/api/guilds/progression/rankings"
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
        dimension_keys=("bossId",),
    )


def test_observatory_records_changes_and_queues_scoped_reanalysis(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[2]
    migrations = root / "migrations"
    database = tmp_path / "coa.duckdb"
    archive = RawArchive(
        tmp_path / "raw",
        database_path=database,
        migrations_dir=migrations,
    )
    contract = _contract()

    dependency_id = register_artifact_dependency(
        database,
        migrations,
        artifact_type="analysis_dataset",
        artifact_key="guild_progression_rankings",
        analysis_type="guild_progression_analysis",
        analysis_version="v1",
        dependency_type="source_endpoint",
        dependency_key=contract.endpoint_code,
    )

    first = _observe(
        archive=archive,
        database=database,
        migrations=migrations,
        contract=contract,
        payload={
            "rows": [
                {"bossId": 1, "name": "A", "score": 10},
                {"bossId": 2, "name": "B", "score": 12},
            ]
        },
        observed_at=datetime(2026, 8, 14, 0, 0, tzinfo=timezone.utc),
    )
    assert len(first.change_event_ids) == 1
    assert len(first.reanalysis_request_ids) == 1

    second = _observe(
        archive=archive,
        database=database,
        migrations=migrations,
        contract=contract,
        payload={
            "rows": [
                {"bossId": 1, "name": "A", "score": 20},
                {"bossId": 2, "name": "B", "score": 22},
            ]
        },
        observed_at=datetime(2026, 8, 14, 0, 5, tzinfo=timezone.utc),
    )
    assert second.change_event_ids == ()
    assert second.reanalysis_request_ids == ()

    third = _observe(
        archive=archive,
        database=database,
        migrations=migrations,
        contract=contract,
        payload={
            "rows": [
                {"bossId": 1, "name": "A", "score": 20, "difficulty": "heroic"},
                {"bossId": 3, "name": "C", "score": 25, "difficulty": "heroic"},
            ]
        },
        observed_at=datetime(2026, 8, 14, 0, 10, tzinfo=timezone.utc),
    )
    assert len(third.change_event_ids) >= 3
    assert len(third.reanalysis_request_ids) == len(third.change_event_ids)

    with duckdb.connect(str(database)) as connection:
        endpoint = connection.execute(
            """
            SELECT source_code, method, route_template, schema_fingerprint
            FROM source_endpoint
            WHERE endpoint_code = ?
            """,
            [contract.endpoint_code],
        ).fetchone()
        assert endpoint is not None
        assert endpoint[0:3] == (
            "coa_logs",
            "GET",
            "/api/guilds/progression/rankings",
        )
        assert endpoint[3]

        assert connection.execute(
            "SELECT COUNT(*) FROM source_contract_version"
        ).fetchone()[0] == 1
        assert connection.execute("SELECT COUNT(*) FROM source_capture").fetchone()[0] == 3
        assert connection.execute(
            "SELECT COUNT(*) FROM source_schema_snapshot"
        ).fetchone()[0] == 3

        change_types = {
            row[0]
            for row in connection.execute(
                "SELECT change_type FROM source_change_event"
            ).fetchall()
        }
        assert {
            "endpoint_added",
            "schema_changed",
            "field_added",
            "new_dimension_value",
        } <= change_types

        requests = connection.execute(
            """
            SELECT dependency_id, analysis_type, status
            FROM reanalysis_request
            ORDER BY requested_at, request_id
            """
        ).fetchall()
        assert requests
        assert {row[0] for row in requests} == {dependency_id}
        assert {row[1] for row in requests} == {"guild_progression_analysis"}
        assert {row[2] for row in requests} == {"pending"}

        raw_count = connection.execute("SELECT COUNT(*) FROM raw_object").fetchone()[0]
        observation_count = connection.execute(
            "SELECT COUNT(*) FROM raw_fetch_observation"
        ).fetchone()[0]
        assert raw_count == 3
        assert observation_count == 3
