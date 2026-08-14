from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

from coa_workbench.collector.raw_archive import RawArchive, request_key_from_url
from coa_workbench.collector.source_observatory import ReviewedGetContract, observe_raw_capture


duckdb = pytest.importorskip("duckdb")


def _legacy_contract() -> ReviewedGetContract:
    return ReviewedGetContract(
        source_code="coa_ascension_logs",
        endpoint_code="report_encounter_throughput_timeline_api",
        base_url="https://coa.ascensionlogs.gg",
        route_template=(
            "/api/reports/{reportId}/encounters/{encounterId}/throughput-timeline"
        ),
        parameter_keys=("bucket_size_ms", "metric", "perspective"),
        auth_state="browser_context_observed",
        discovery_source="legacy_test",
        review_state="verified",
    )


def _observe(
    *,
    archive: RawArchive,
    database: Path,
    migrations: Path,
    url: str,
    payload: dict[str, object],
    observed_at: datetime,
) -> None:
    contract = _legacy_contract()
    body = json.dumps(payload, sort_keys=True).encode()
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
    observe_raw_capture(
        database,
        migrations,
        contract=contract,
        capture=capture,
        payload=body,
        request_url=url,
    )


def test_repair_supersedes_only_legacy_profile_churn_and_preserves_evidence(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[2]
    migrations = root / "migrations"
    database = tmp_path / "coa.duckdb"
    archive = RawArchive(
        tmp_path / "raw",
        database_path=database,
        migrations_dir=migrations,
    )

    _observe(
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
    _observe(
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

    with duckdb.connect(str(database), read_only=True) as connection:
        before_raw = connection.execute("SELECT COUNT(*) FROM raw_object").fetchone()[0]
        before_fetch = connection.execute(
            "SELECT COUNT(*) FROM raw_fetch_observation"
        ).fetchone()[0]
        before_capture = connection.execute("SELECT COUNT(*) FROM source_capture").fetchone()[0]
        before_snapshot = connection.execute(
            "SELECT COUNT(*) FROM source_schema_snapshot"
        ).fetchone()[0]
        before_open = connection.execute(
            """
            SELECT COUNT(*) FROM source_change_event
            WHERE endpoint_code = 'report_encounter_throughput_timeline_api'
              AND status = 'open'
            """
        ).fetchone()[0]
    assert before_open > 1

    completed = subprocess.run(
        [
            sys.executable,
            "scripts/repair_throughput_schema_profile_churn.py",
            "--database",
            str(database),
            "--migrations",
            str(migrations),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    result = json.loads(completed.stdout)
    assert result["status"] == "repaired"
    assert result["superseded_change_event_count"] == before_open - 1
    assert result["raw_objects_deleted"] is False
    assert result["source_captures_deleted"] is False
    assert result["schema_snapshots_deleted"] is False

    with duckdb.connect(str(database), read_only=True) as connection:
        assert connection.execute("SELECT COUNT(*) FROM raw_object").fetchone()[0] == before_raw
        assert (
            connection.execute("SELECT COUNT(*) FROM raw_fetch_observation").fetchone()[0]
            == before_fetch
        )
        assert connection.execute("SELECT COUNT(*) FROM source_capture").fetchone()[0] == before_capture
        assert (
            connection.execute("SELECT COUNT(*) FROM source_schema_snapshot").fetchone()[0]
            == before_snapshot
        )
        open_rows = connection.execute(
            """
            SELECT change_type, status
            FROM source_change_event
            WHERE endpoint_code = 'report_encounter_throughput_timeline_api'
              AND status = 'open'
            """
        ).fetchall()
        assert open_rows == [("endpoint_added", "open")]
        superseded_count = connection.execute(
            """
            SELECT COUNT(*)
            FROM source_change_event
            WHERE endpoint_code = 'report_encounter_throughput_timeline_api'
              AND status = 'superseded_profile_partition'
            """
        ).fetchone()[0]
        assert superseded_count == before_open - 1
