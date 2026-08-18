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
        endpoint_code="dynamic_map_test_api",
        base_url="https://coa.ascensionlogs.gg",
        route_template="/api/reports/{reportId}/series",
        auth_state="browser_context_observed",
        discovery_source="test",
        review_state="verified",
    )


def _capture(
    *,
    archive: RawArchive,
    contract: ReviewedGetContract,
    payload: dict[str, object],
    observed_at: datetime,
    path: str,
):
    body = json.dumps(payload, sort_keys=True).encode()
    url = f"https://coa.ascensionlogs.gg{path}"
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
    return capture, body, url


def test_legacy_literal_numeric_paths_are_compared_as_wildcards(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[2]
    migrations = root / "migrations"
    database = tmp_path / "coa.duckdb"
    archive = RawArchive(
        tmp_path / "raw",
        database_path=database,
        migrations_dir=migrations,
    )
    contract = _contract()

    first_capture, first_body, first_url = _capture(
        archive=archive,
        contract=contract,
        payload={"series": {"123": [{"amount": 1}]}},
        observed_at=datetime(2026, 8, 14, 12, 0, tzinfo=timezone.utc),
        path="/api/reports/1/series",
    )
    first = observe_raw_capture(
        database,
        migrations,
        contract=contract,
        capture=first_capture,
        payload=first_body,
        request_url=first_url,
    )
    assert len(first.change_event_ids) == 1

    with duckdb.connect(str(database)) as connection:
        connection.execute(
            """
            UPDATE source_schema_snapshot
            SET path_types_json = ?, schema_fingerprint = 'legacy-literal-fingerprint',
                metadata_json = '{}'
            WHERE snapshot_id = ?
            """,
            [
                json.dumps(
                    {
                        "/": ["object"],
                        "/series": ["object"],
                        "/series/123": ["array"],
                        "/series/123/*": ["object"],
                        "/series/123/*/amount": ["int"],
                    },
                    sort_keys=True,
                ),
                first.snapshot_id,
            ],
        )

    second_capture, second_body, second_url = _capture(
        archive=archive,
        contract=contract,
        payload={"series": {"999": [{"amount": 2}]}},
        observed_at=datetime(2026, 8, 14, 12, 5, tzinfo=timezone.utc),
        path="/api/reports/9/series",
    )
    second = observe_raw_capture(
        database,
        migrations,
        contract=contract,
        capture=second_capture,
        payload=second_body,
        request_url=second_url,
    )

    assert second.change_event_ids == ()


def test_replaying_same_raw_observation_is_idempotent_across_snapshot_code(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[2]
    migrations = root / "migrations"
    database = tmp_path / "coa.duckdb"
    archive = RawArchive(
        tmp_path / "raw",
        database_path=database,
        migrations_dir=migrations,
    )
    contract = _contract()
    capture, body, url = _capture(
        archive=archive,
        contract=contract,
        payload={"series": {"123": [{"amount": 1}]}},
        observed_at=datetime(2026, 8, 14, 13, 0, tzinfo=timezone.utc),
        path="/api/reports/1/series",
    )

    first = observe_raw_capture(
        database,
        migrations,
        contract=contract,
        capture=capture,
        payload=body,
        request_url=url,
    )
    replay = observe_raw_capture(
        database,
        migrations,
        contract=contract,
        capture=capture,
        payload=body,
        request_url=url,
    )

    assert replay.snapshot_id == first.snapshot_id
    assert replay.change_event_ids == ()
    assert replay.reanalysis_request_ids == ()
