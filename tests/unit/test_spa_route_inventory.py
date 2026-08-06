from __future__ import annotations

import gzip
from pathlib import Path

import pytest

from coa_workbench.collector.raw_archive import RawArchive
from coa_workbench.collector.spa_route_inventory import (
    build_spa_route_inventory,
    normalize_api_route_shape,
)


def _capture_asset(raw_root: Path, body: bytes, *, request_key: str) -> str:
    capture = RawArchive(raw_root).capture_bytes(
        body,
        source_code="coa_ascension_logs",
        endpoint_code="build_page_asset",
        request_key=request_key,
        http_status=200,
        content_type="application/javascript",
        request_url="https://coa.ascensionlogs.gg/assets/index-test.js",
    )
    return capture.payload_hash


def test_normalize_api_route_shape_redacts_dynamic_segments():
    assert (
        normalize_api_route_shape("/api/reports/${reportId}/encounters?limit=<value>")
        == "/api/reports/{template}/encounters?limit=<value>"
    )
    assert normalize_api_route_shape("/api/reports/123/roster") == "/api/reports/{integer}/roster"
    assert (
        normalize_api_route_shape("/api/report/123e4567-e89b-12d3-a456-426614174000")
        == "/api/report/{uuid}"
    )
    assert normalize_api_route_shape("/api/report/:reportId") == "/api/report/{parameter}"


def test_inventory_verifies_archives_and_emits_lexical_candidates(tmp_path: Path):
    first_hash = _capture_asset(
        tmp_path,
        b'fetch("/api/reports/${reportId}/encounters?limit=25");'
        b'fetch("/api/reports/123/roster");fetch("/api/health");',
        request_key="GET:/assets/index-one.js",
    )
    second_hash = _capture_asset(
        tmp_path,
        b'fetch("/api/reports/${other}/encounters?limit=5");'
        b'fetch("/api/events/${encounterId}");',
        request_key="GET:/assets/index-two.js",
    )

    inventory = build_spa_route_inventory(tmp_path)

    assert inventory["schema_version"] == 1
    assert inventory["inventory_kind"] == "archived_spa_api_route_inventory"
    assert inventory["summary"] == {
        "archive_count": 2,
        "route_candidate_count": 4,
        "lexically_relevant_candidate_count": 3,
        "all_archives_verified": True,
        "contains_source_record_scalar_values": False,
        "semantic_verification_required": True,
        "network_requests_performed": False,
    }

    routes = {row["route_shape"]: row for row in inventory["routes"]}
    assert set(routes) == {
        "/api/events/{template}",
        "/api/health",
        "/api/reports/{integer}/roster",
        "/api/reports/{template}/encounters?limit=<value>",
    }
    encounters = routes["/api/reports/{template}/encounters?limit=<value>"]
    assert encounters["archive_count"] == 2
    assert encounters["payload_hashes"] == sorted([first_hash, second_hash])
    assert encounters["lexical_hints"] == ["encounter", "report"]
    assert encounters["semantic_status"] == "unverified_candidate"
    assert routes["/api/health"]["lexical_hints"] == []


def test_inventory_rejects_archive_hash_mismatch(tmp_path: Path):
    payload_hash = _capture_asset(
        tmp_path,
        b'fetch("/api/reports/${reportId}/encounters");',
        request_key="GET:/assets/index-one.js",
    )
    archive_path = next(tmp_path.glob(f"**/{payload_hash}.bin.gz"))
    archive_path.write_bytes(gzip.compress(b"changed", mtime=0))

    with pytest.raises(ValueError, match="payload hash mismatch"):
        build_spa_route_inventory(tmp_path)


def test_inventory_is_bounded_by_archive_count(tmp_path: Path):
    _capture_asset(
        tmp_path,
        b'fetch("/api/reports/${reportId}/encounters");',
        request_key="GET:/assets/index-one.js",
    )
    _capture_asset(
        tmp_path,
        b'fetch("/api/reports/${reportId}/roster");',
        request_key="GET:/assets/index-two.js",
    )

    with pytest.raises(ValueError, match="exceeds bounded maximum"):
        build_spa_route_inventory(tmp_path, max_archives=1)
