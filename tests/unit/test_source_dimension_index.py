from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import duckdb

from coa_workbench.collector.raw_archive import RawArchive, request_key_from_url
from coa_workbench.collector.source_dimension_index import rebuild_source_dimension_index
from coa_workbench.collector.source_observatory import ReviewedGetContract, observe_raw_capture


def _contract() -> ReviewedGetContract:
    return ReviewedGetContract(
        source_code="test_source",
        endpoint_code="bosses_api",
        base_url="https://example.test",
        route_template="/api/bosses",
        parameter_keys=(),
        auth_state="browser_context_observed",
        discovery_source="unit_test",
        review_state="verified",
        logical_name="boss_catalog",
    )


def _observe(
    archive: RawArchive,
    database: Path,
    migrations: Path,
    *,
    boss_ids: list[int],
    observed_at: datetime,
):
    contract = _contract()
    url = "https://example.test/api/bosses"
    payload = json.dumps({"rows": [{"bossId": value} for value in boss_ids]}).encode()
    capture = archive.capture_bytes(
        payload,
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
        payload=payload,
        request_url=url,
        dimension_keys=("bossId",),
    )


def test_dimension_index_turns_source_change_into_scoped_reanalysis(tmp_path: Path) -> None:
    database = tmp_path / "observatory.duckdb"
    migrations = Path("migrations")
    archive = RawArchive(tmp_path / "raw", database_path=database, migrations_dir=migrations)
    first_at = datetime(2026, 8, 14, 9, 0, tzinfo=timezone.utc)

    first_observation = _observe(
        archive,
        database,
        migrations,
        boss_ids=[1, 2],
        observed_at=first_at,
    )
    assert first_observation.reanalysis_request_ids == ()

    first_index = rebuild_source_dimension_index(
        database,
        migrations,
        source_code="test_source",
        endpoint_codes=("bosses_api",),
    )
    assert first_index["status"] == "completed"
    assert first_index["dependency_count"] == 1
    assert first_index["dimension_name_count"] == 1
    assert first_index["dimension_value_count"] == 2

    second_observation = _observe(
        archive,
        database,
        migrations,
        boss_ids=[1, 2, 3],
        observed_at=first_at + timedelta(hours=1),
    )
    assert len(second_observation.reanalysis_request_ids) == 1

    with duckdb.connect(str(database)) as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM reanalysis_request WHERE status = 'pending'"
        ).fetchone()[0] == 1

    second_index = rebuild_source_dimension_index(
        database,
        migrations,
        source_code="test_source",
        endpoint_codes=("bosses_api",),
    )
    assert second_index["dimension_value_count"] == 3
    assert second_index["completed_reanalysis_request_count"] == 1

    with duckdb.connect(str(database)) as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM reanalysis_request WHERE status = 'pending'"
        ).fetchone()[0] == 0
        assert connection.execute(
            "SELECT COUNT(*) FROM reanalysis_request WHERE status = 'completed'"
        ).fetchone()[0] == 1
        assert connection.execute(
            "SELECT COUNT(*) FROM source_dimension_index_value WHERE analysis_run_id = ?",
            [second_index["analysis_run_id"]],
        ).fetchone()[0] == 3
        assert connection.execute(
            "SELECT COUNT(*) FROM artifact_dependency WHERE active = TRUE"
        ).fetchone()[0] == 1
