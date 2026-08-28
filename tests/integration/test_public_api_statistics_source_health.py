from __future__ import annotations

import json
from pathlib import Path

import pytest

from coa_workbench.collector.public_api_archive import load_latest_public_api_capture
from coa_workbench.collector.public_api_source_health import (
    observe_archived_public_api_statistics,
    private_public_api_statistics_profile_key,
    review_public_api_statistics_health,
)
from coa_workbench.collector.raw_archive import RawArchive, request_key_from_url
from coa_workbench.collector.source_registry import load_source_registry
from coa_workbench.normalizer.public_api_statistics import parse_public_api_statistics
from coa_workbench.storage.public_api_statistics import persist_public_api_statistics


duckdb = pytest.importorskip("duckdb")


def _payload() -> dict[str, object]:
    return {
        "success": True,
        "phase": 12,
        "phase_name": "PrivatePhase",
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
                "total_parses": 20,
                "summary_a": 1,
                "summary_b": 2.0,
                "summary_c": 3,
                "specs": {
                    "PrivateSpec": {
                        "avg": 100.0,
                        "median": 99.0,
                        "max": 110.0,
                        "min": 80.0,
                        "total_parses": 20,
                        "percentiles": {"50": 99.0, "95": 108.0},
                    }
                },
            }
        },
    }


def test_archived_statistics_integrates_with_source_health_without_public_scalars(
    tmp_path: Path,
) -> None:
    root = Path(__file__).resolve().parents[2]
    registry = load_source_registry(root / "config" / "coa_public_api_sources.yaml")
    raw_root = tmp_path / "raw"
    database = tmp_path / "coa.duckdb"
    migrations = root / "migrations"
    query = {
        "phase": "12",
        "difficulty": "all",
        "metric": "avg_dps",
        "bracket": "all",
        "damageMode": "standard",
        "role": "dps",
    }
    request_url = (
        f"{registry.base_url}/statistics?phase=12&difficulty=all&metric=avg_dps"
        "&bracket=all&damageMode=standard&role=dps"
    )
    body = json.dumps(_payload(), sort_keys=True).encode("utf-8")
    RawArchive(
        raw_root,
        database_path=database,
        migrations_dir=migrations,
    ).capture_bytes(
        body,
        source_code=registry.source_code,
        endpoint_code="public_api_statistics",
        request_key=request_key_from_url("GET", request_url),
        http_status=200,
        content_type="application/json",
        request_url=request_url,
        metadata={
            "capture_mode": "official_public_api_stats",
            "access_scope": "stats:read",
            "query_keys": list(query),
            "private_query_values": query,
            "credential_header_name": "Authorization",
        },
    )

    capture = load_latest_public_api_capture(
        raw_root,
        source_code=registry.source_code,
        endpoint_code="public_api_statistics",
    )
    acquisition = observe_archived_public_api_statistics(
        database_path=database,
        migrations_path=migrations,
        raw_root=raw_root,
        registry=registry,
        capture=capture,
    )
    profile_key = private_public_api_statistics_profile_key(registry, capture)
    batch = parse_public_api_statistics(
        capture.payload,
        query_keys=capture.query_keys,
        query_values=capture.query_value_mapping(),
    )
    persist_public_api_statistics(
        database_path=database,
        migrations_path=migrations,
        source_raw_id=capture.raw_id,
        source_code=registry.source_code,
        source_profile_key=profile_key,
        batch=batch,
    )

    health = review_public_api_statistics_health(database)

    assert acquisition.outcome == "schema_candidate"
    assert acquisition.source_observation is not None
    assert health["source_observatory"]["endpoint_registered"] is True
    assert health["source_observatory"]["capture_count"] == 1
    assert health["source_observatory"]["schema_snapshot_observed"] is True
    assert health["source_observatory"]["latest_acquisition_outcome"] == "schema_candidate"
    assert health["source_observatory"]["open_change_event_count"] == 1
    assert health["source_observatory"]["actionable_open_change_event_count"] == 0
    assert health["analysis"]["source_endpoint_profile_dependency_count"] == 1
    assert health["analysis"]["legacy_unscoped_source_endpoint_dependency_count"] == 0
    assert health["analysis"]["raw_dependency_count"] == 1
    assert health["analysis"]["completed_analysis_run_count"] == 1
    assert health["analysis"]["pending_reanalysis_request_count"] == 0
    assert health["verification"]["source_observatory_integrated"] is True
    assert health["verification"]["source_endpoint_profile_dependency_registered"] is True
    assert health["verification"]["no_legacy_unscoped_source_dependency"] is True
    assert health["verification"]["attention_required"] is False
    assert health["verification"]["planner_scoring_allowed"] is False
    assert health["privacy"]["profile_fingerprints_included"] is False
    assert health["privacy"]["request_fingerprints_included"] is False
    assert health["privacy"]["schema_fingerprints_included"] is False

    rendered = json.dumps(health, ensure_ascii=False, sort_keys=True)
    assert "PrivatePhase" not in rendered
    assert "PrivateClass" not in rendered
    assert "PrivateSpec" not in rendered
    assert '"phase": "12"' not in rendered
    assert profile_key not in rendered
