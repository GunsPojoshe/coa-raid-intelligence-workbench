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
from coa_workbench.collector.source_registry import load_source_registry
from coa_workbench.collector.source_scope import (
    resolve_scoped_reanalysis_requests,
    scope_fingerprint_from_url,
)


duckdb = pytest.importorskip("duckdb")


def _observe(
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


def test_scoped_reanalysis_matches_only_the_reviewed_report_path_scope(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[2]
    migrations = root / "migrations"
    registry = load_source_registry(root / "config" / "ascension_logs_sources.yaml")
    route = registry.route("report_detail_api")
    contract = ReviewedGetContract(
        source_code=registry.source_code,
        endpoint_code=route.endpoint_code,
        base_url=registry.base_url,
        route_template=str(route.route_template),
        parameter_keys=route.parameter_keys,
        auth_state=route.auth_mode,
        discovery_source="test",
        review_state="verified",
    )
    database = tmp_path / "coa.duckdb"
    archive = RawArchive(
        tmp_path / "raw",
        database_path=database,
        migrations_dir=migrations,
    )

    report_one_url = "https://coa.ascensionlogs.gg/api/reports/123"
    report_two_url = "https://coa.ascensionlogs.gg/api/reports/456"
    baseline = _observe(
        archive=archive,
        database=database,
        migrations=migrations,
        contract=contract,
        url=report_one_url,
        payload={"success": True, "report": {"id": 123}},
        observed_at=datetime(2020, 1, 1, tzinfo=timezone.utc),
    )
    assert baseline.change_event_ids

    report_one_scope = scope_fingerprint_from_url(
        source_code=registry.source_code,
        route_template=str(route.route_template),
        scope_path_keys=route.scope_path_keys,
        request_url=report_one_url,
    )
    register_artifact_dependency(
        database,
        migrations,
        artifact_type="current_report_derived_observations",
        artifact_key="report-one-artifact",
        analysis_type="current_report_runtime_parse",
        analysis_version="test-v1",
        dependency_type="source_endpoint_scope",
        dependency_key=route.endpoint_code,
        dependency_version=report_one_scope,
        metadata={"scope_path_keys": list(route.scope_path_keys)},
    )

    initial = resolve_scoped_reanalysis_requests(
        database,
        migrations,
        registry=registry,
        endpoint_codes=(route.endpoint_code,),
    )
    assert initial.created_request_count == 0

    other_report = _observe(
        archive=archive,
        database=database,
        migrations=migrations,
        contract=contract,
        url=report_two_url,
        payload={"success": True, "report": {"id": 456, "other_only": True}},
        observed_at=datetime(2099, 1, 1, tzinfo=timezone.utc),
    )
    assert other_report.change_event_ids
    other_resolution = resolve_scoped_reanalysis_requests(
        database,
        migrations,
        registry=registry,
        endpoint_codes=(route.endpoint_code,),
    )
    assert other_resolution.eligible_event_count >= 1
    assert other_resolution.scope_match_count == 0
    assert other_resolution.created_request_count == 0

    matching_report = _observe(
        archive=archive,
        database=database,
        migrations=migrations,
        contract=contract,
        url=report_one_url + "?ignored=no",
        payload={"success": True, "report": {"id": 123, "matching_only": True}},
        observed_at=datetime(2099, 1, 2, tzinfo=timezone.utc),
    )
    assert matching_report.change_event_ids
    matching_resolution = resolve_scoped_reanalysis_requests(
        database,
        migrations,
        registry=registry,
        endpoint_codes=(route.endpoint_code,),
    )
    assert matching_resolution.scope_match_count >= 1
    assert matching_resolution.created_request_count >= 1

    replay_resolution = resolve_scoped_reanalysis_requests(
        database,
        migrations,
        registry=registry,
        endpoint_codes=(route.endpoint_code,),
    )
    assert replay_resolution.created_request_count == 0
    assert replay_resolution.existing_request_count >= 1

    with duckdb.connect(str(database), read_only=True) as connection:
        requests = connection.execute(
            """
            SELECT r.status, r.artifact_key, r.target_scope_json
            FROM reanalysis_request AS r
            WHERE r.artifact_key = 'report-one-artifact'
            ORDER BY r.request_id
            """
        ).fetchall()
    assert requests
    assert all(str(row[0]) == "pending" for row in requests)
    assert all(str(row[1]) == "report-one-artifact" for row in requests)
    for _status, _artifact_key, scope_json in requests:
        scope = json.loads(str(scope_json))
        assert scope["scope_path_keys"] == ["reportId"]
        assert "scope_fingerprint" not in scope
        assert "reportId" not in scope
