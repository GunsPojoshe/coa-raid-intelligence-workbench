from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from coa_workbench.collector.raw_archive import RawArchive, request_key_from_url
from coa_workbench.collector.source_observatory import (
    ReviewedGetContract,
    observation_profile_key,
    observe_raw_capture,
    register_artifact_dependency,
)
from coa_workbench.collector.source_profile_reanalysis import (
    resolve_profile_reanalysis_requests,
)


duckdb = pytest.importorskip("duckdb")


def _contract(*, expanded: bool = False) -> ReviewedGetContract:
    return ReviewedGetContract(
        source_code="profile_test_source",
        endpoint_code="profiled_statistics",
        base_url="https://example.invalid",
        route_template="/api/statistics",
        parameter_keys=("bracket", "metric") if expanded else ("metric",),
        schema_profile_keys=("metric",),
        auth_state="api_key_header",
        discovery_source="test",
        review_state="verified",
        logical_name="profiled-statistics",
    )


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


def _register_profile_dependency(
    database: Path,
    migrations: Path,
    *,
    artifact_key: str,
    endpoint_code: str,
    profile_key: str,
) -> None:
    register_artifact_dependency(
        database,
        migrations,
        artifact_type="profiled-artifact",
        artifact_key=artifact_key,
        analysis_type="profiled-analysis",
        analysis_version="test-v1",
        dependency_type="source_endpoint_profile",
        dependency_key=endpoint_code,
        dependency_version=profile_key,
        metadata={
            "profile_scoped": True,
            "profile_fingerprint_public": False,
        },
    )


def _pending_artifact_keys(database: Path) -> set[str]:
    with duckdb.connect(str(database), read_only=True) as connection:
        return {
            str(row[0])
            for row in connection.execute(
                """
                SELECT DISTINCT artifact_key
                FROM reanalysis_request
                WHERE status = 'pending'
                ORDER BY artifact_key
                """
            ).fetchall()
        }


def test_profile_reanalysis_matches_only_the_changed_query_profile(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[2]
    migrations = root / "migrations"
    database = tmp_path / "coa.duckdb"
    archive = RawArchive(
        tmp_path / "raw",
        database_path=database,
        migrations_dir=migrations,
    )
    contract = _contract()
    damage_url = "https://example.invalid/api/statistics?metric=damage"
    healing_url = "https://example.invalid/api/statistics?metric=healing"

    _observe(
        archive=archive,
        database=database,
        migrations=migrations,
        contract=contract,
        url=damage_url,
        payload={"rows": [{"value": 10}]},
        observed_at=datetime(2020, 1, 1, tzinfo=timezone.utc),
    )
    _observe(
        archive=archive,
        database=database,
        migrations=migrations,
        contract=contract,
        url=healing_url,
        payload={"rows": [{"healing": 20}]},
        observed_at=datetime(2020, 1, 2, tzinfo=timezone.utc),
    )

    damage_profile = observation_profile_key(contract, damage_url)
    healing_profile = observation_profile_key(contract, healing_url)
    assert damage_profile
    assert healing_profile
    assert damage_profile != healing_profile
    _register_profile_dependency(
        database,
        migrations,
        artifact_key="artifact-damage",
        endpoint_code=contract.endpoint_code,
        profile_key=damage_profile,
    )
    _register_profile_dependency(
        database,
        migrations,
        artifact_key="artifact-healing",
        endpoint_code=contract.endpoint_code,
        profile_key=healing_profile,
    )

    initial = resolve_profile_reanalysis_requests(
        database,
        migrations,
        endpoint_codes=(contract.endpoint_code,),
    )
    assert initial.created_request_count == 0

    changed_healing = _observe(
        archive=archive,
        database=database,
        migrations=migrations,
        contract=contract,
        url=healing_url,
        payload={"rows": [{"healing": "20", "new_field": True}]},
        observed_at=datetime(2099, 1, 1, tzinfo=timezone.utc),
    )
    assert changed_healing.change_event_ids

    resolved = resolve_profile_reanalysis_requests(
        database,
        migrations,
        endpoint_codes=(contract.endpoint_code,),
    )
    assert resolved.profile_dependency_count == 2
    assert resolved.eligible_event_count >= 1
    assert resolved.profile_match_count >= 1
    assert resolved.global_match_count == 0
    assert resolved.created_request_count >= 1
    assert _pending_artifact_keys(database) == {"artifact-healing"}

    public = resolved.public_summary()
    assert public["profile_values_included"] is False
    assert public["profile_fingerprints_included"] is False
    rendered = json.dumps(public, sort_keys=True)
    assert damage_profile not in rendered
    assert healing_profile not in rendered

    replay = resolve_profile_reanalysis_requests(
        database,
        migrations,
        endpoint_codes=(contract.endpoint_code,),
    )
    assert replay.created_request_count == 0
    assert replay.existing_request_count >= 1


def test_request_contract_change_fans_out_across_profile_dependencies(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[2]
    migrations = root / "migrations"
    database = tmp_path / "coa.duckdb"
    archive = RawArchive(
        tmp_path / "raw",
        database_path=database,
        migrations_dir=migrations,
    )
    contract = _contract()
    damage_url = "https://example.invalid/api/statistics?metric=damage"
    healing_url = "https://example.invalid/api/statistics?metric=healing"

    _observe(
        archive=archive,
        database=database,
        migrations=migrations,
        contract=contract,
        url=damage_url,
        payload={"rows": [{"value": 10}]},
        observed_at=datetime(2020, 1, 1, tzinfo=timezone.utc),
    )
    _observe(
        archive=archive,
        database=database,
        migrations=migrations,
        contract=contract,
        url=healing_url,
        payload={"rows": [{"healing": 20}]},
        observed_at=datetime(2020, 1, 2, tzinfo=timezone.utc),
    )
    damage_profile = observation_profile_key(contract, damage_url)
    healing_profile = observation_profile_key(contract, healing_url)
    assert damage_profile
    assert healing_profile
    _register_profile_dependency(
        database,
        migrations,
        artifact_key="artifact-damage",
        endpoint_code=contract.endpoint_code,
        profile_key=damage_profile,
    )
    _register_profile_dependency(
        database,
        migrations,
        artifact_key="artifact-healing",
        endpoint_code=contract.endpoint_code,
        profile_key=healing_profile,
    )

    expanded_contract = _contract(expanded=True)
    changed = _observe(
        archive=archive,
        database=database,
        migrations=migrations,
        contract=expanded_contract,
        url=damage_url,
        payload={"rows": [{"value": 10}]},
        observed_at=datetime(2099, 1, 1, tzinfo=timezone.utc),
    )
    assert changed.change_event_ids

    resolved = resolve_profile_reanalysis_requests(
        database,
        migrations,
        endpoint_codes=(contract.endpoint_code,),
    )
    assert resolved.global_match_count == 2
    assert resolved.created_request_count == 2
    assert _pending_artifact_keys(database) == {"artifact-damage", "artifact-healing"}
