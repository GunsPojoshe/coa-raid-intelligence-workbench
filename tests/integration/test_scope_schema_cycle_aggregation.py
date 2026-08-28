from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

from coa_workbench.collector.profile_schema_cycle import aggregate_profile_schema_observations
from coa_workbench.collector.raw_archive import RawArchive, request_key_from_url
from coa_workbench.collector.scope_schema_cycle import aggregate_scope_schema_observations
from coa_workbench.collector.source_observatory import ReviewedGetContract, observe_raw_capture


duckdb = pytest.importorskip("duckdb")


def _capture(
    *,
    archive: RawArchive,
    database: Path,
    migrations: Path,
    contract: ReviewedGetContract,
    url: str,
    payload: dict[str, object],
    observed_at: datetime,
):
    body = json.dumps(payload, sort_keys=True).encode()
    raw = archive.capture_bytes(
        body,
        source_code=contract.source_code,
        endpoint_code=contract.endpoint_code,
        request_key=request_key_from_url("GET", url),
        fetched_at=observed_at,
        http_status=200,
        content_type="application/json",
        request_url=url,
    )
    source_observation = observe_raw_capture(
        database,
        migrations,
        contract=contract,
        capture=raw,
        payload=body,
        request_url=url,
    )
    return SimpleNamespace(source_observation=source_observation)


def _detail_contract() -> ReviewedGetContract:
    return ReviewedGetContract(
        source_code="coa_ascension_logs",
        endpoint_code="report_detail_api",
        base_url="https://coa.ascensionlogs.gg",
        route_template="/api/reports/{reportId}",
        auth_state="browser_context_observed",
        discovery_source="test",
        review_state="verified",
        logical_name="report detail",
    )


def _throughput_contract() -> ReviewedGetContract:
    return ReviewedGetContract(
        source_code="coa_ascension_logs",
        endpoint_code="report_encounter_throughput_timeline_api",
        base_url="https://coa.ascensionlogs.gg",
        route_template="/api/reports/{reportId}/encounters/{encounterId}/throughput-timeline",
        parameter_keys=("bucket_size_ms", "metric", "perspective"),
        schema_profile_keys=("metric", "perspective"),
        auth_state="browser_context_observed",
        discovery_source="test",
        review_state="verified",
        logical_name="throughput",
    )


def _open_events(database: Path, endpoint_code: str) -> list[tuple[str, str | None, str]]:
    with duckdb.connect(str(database), read_only=True) as connection:
        return [
            (str(row[0]), None if row[1] is None else str(row[1]), str(row[2]))
            for row in connection.execute(
                """
                SELECT change_type, subject_path, status
                FROM source_change_event
                WHERE endpoint_code = ?
                  AND status = 'open'
                ORDER BY change_type, subject_path, event_id
                """,
                [endpoint_code],
            ).fetchall()
        ]


def test_scope_cycle_blocks_cross_report_schema_churn_and_keeps_same_scope_changes(
    tmp_path: Path,
) -> None:
    root = Path(__file__).resolve().parents[2]
    migrations = root / "migrations"
    database = tmp_path / "coa.duckdb"
    archive = RawArchive(
        tmp_path / "raw",
        database_path=database,
        migrations_dir=migrations,
    )
    contract = _detail_contract()

    first = _capture(
        archive=archive,
        database=database,
        migrations=migrations,
        contract=contract,
        url="https://coa.ascensionlogs.gg/api/reports/101",
        payload={"success": True, "report": {"id": 101, "stable": True}},
        observed_at=datetime(2026, 8, 15, 1, 0, tzinfo=timezone.utc),
    )
    first_summary = aggregate_scope_schema_observations(
        database,
        migrations,
        contract=contract,
        scope_path_keys=("reportId",),
        observations=(first,),
    )
    assert first_summary.scope_cycle_count == 1
    assert first_summary.aggregate_change_event_count == 0
    assert _open_events(database, contract.endpoint_code) == [
        ("endpoint_added", "/api/reports/{reportId}", "open")
    ]

    second = _capture(
        archive=archive,
        database=database,
        migrations=migrations,
        contract=contract,
        url="https://coa.ascensionlogs.gg/api/reports/202",
        payload={
            "success": True,
            "report": {"id": 202, "stable": True, "other_report_only": {"x": 1}},
        },
        observed_at=datetime(2026, 8, 15, 1, 5, tzinfo=timezone.utc),
    )
    assert second.source_observation.change_event_ids
    second_summary = aggregate_scope_schema_observations(
        database,
        migrations,
        contract=contract,
        scope_path_keys=("reportId",),
        observations=(second,),
    )
    assert second_summary.scope_cycle_count == 1
    assert second_summary.superseded_member_event_count >= 1
    assert second_summary.aggregate_change_event_count == 0
    assert _open_events(database, contract.endpoint_code) == [
        ("endpoint_added", "/api/reports/{reportId}", "open")
    ]

    changed_first = _capture(
        archive=archive,
        database=database,
        migrations=migrations,
        contract=contract,
        url="https://coa.ascensionlogs.gg/api/reports/101",
        payload={
            "success": True,
            "report": {"id": 101, "stable": True, "same_report_new_field": 7},
        },
        observed_at=datetime(2026, 8, 15, 1, 10, tzinfo=timezone.utc),
    )
    changed_summary = aggregate_scope_schema_observations(
        database,
        migrations,
        contract=contract,
        scope_path_keys=("reportId",),
        observations=(changed_first,),
    )
    assert changed_summary.scope_cycle_count == 1
    assert changed_summary.aggregate_change_event_count == 2

    open_events = _open_events(database, contract.endpoint_code)
    assert ("endpoint_added", "/api/reports/{reportId}", "open") in open_events
    assert ("schema_changed", None, "open") in open_events
    assert ("field_added", "/report/same_report_new_field", "open") in open_events

    replay = aggregate_scope_schema_observations(
        database,
        migrations,
        contract=contract,
        scope_path_keys=("reportId",),
        observations=(changed_first,),
    )
    assert replay.scope_cycle_count == 0
    assert replay.aggregate_change_event_count == 0


def test_scope_cycle_supersedes_legacy_profile_cycle_cross_report_events(
    tmp_path: Path,
) -> None:
    root = Path(__file__).resolve().parents[2]
    migrations = root / "migrations"
    database = tmp_path / "coa.duckdb"
    archive = RawArchive(
        tmp_path / "raw",
        database_path=database,
        migrations_dir=migrations,
    )
    contract = _throughput_contract()

    report_one = (
        _capture(
            archive=archive,
            database=database,
            migrations=migrations,
            contract=contract,
            url=(
                "https://coa.ascensionlogs.gg/api/reports/101/encounters/1/"
                "throughput-timeline?metric=damage"
            ),
            payload={"success": True, "series": {"1": [{"amount": 1}]}},
            observed_at=datetime(2026, 8, 15, 2, 0, tzinfo=timezone.utc),
        ),
        _capture(
            archive=archive,
            database=database,
            migrations=migrations,
            contract=contract,
            url=(
                "https://coa.ascensionlogs.gg/api/reports/101/encounters/2/"
                "throughput-timeline?metric=damage"
            ),
            payload={"success": True, "series": {"2": [{"amount": 2}]}},
            observed_at=datetime(2026, 8, 15, 2, 0, 1, tzinfo=timezone.utc),
        ),
    )
    legacy_first = aggregate_profile_schema_observations(
        database,
        migrations,
        contract=contract,
        observations=report_one,
    )
    assert legacy_first.profile_cycle_count == 1

    report_two = (
        _capture(
            archive=archive,
            database=database,
            migrations=migrations,
            contract=contract,
            url=(
                "https://coa.ascensionlogs.gg/api/reports/202/encounters/3/"
                "throughput-timeline?metric=damage"
            ),
            payload={
                "success": True,
                "series": {"3": [{"amount": 3, "report_two_only": True}]},
            },
            observed_at=datetime(2026, 8, 15, 2, 5, tzinfo=timezone.utc),
        ),
        _capture(
            archive=archive,
            database=database,
            migrations=migrations,
            contract=contract,
            url=(
                "https://coa.ascensionlogs.gg/api/reports/202/encounters/4/"
                "throughput-timeline?metric=damage"
            ),
            payload={
                "success": True,
                "series": {"4": [{"amount": 4, "report_two_only": False}]},
            },
            observed_at=datetime(2026, 8, 15, 2, 5, 1, tzinfo=timezone.utc),
        ),
    )
    legacy_second = aggregate_profile_schema_observations(
        database,
        migrations,
        contract=contract,
        observations=report_two,
    )
    assert legacy_second.aggregate_change_event_count >= 1
    legacy_open = _open_events(database, contract.endpoint_code)
    assert any(event[0] == "field_added" for event in legacy_open)

    scoped = aggregate_scope_schema_observations(
        database,
        migrations,
        contract=contract,
        scope_path_keys=("reportId",),
        observations=report_two,
    )
    assert scoped.scope_cycle_count == 1
    assert scoped.aggregate_change_event_count == 0
    assert scoped.superseded_legacy_profile_event_count >= 1

    open_events = _open_events(database, contract.endpoint_code)
    assert open_events == [
        ("endpoint_added", contract.route_template, "open")
    ]
