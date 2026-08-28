from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from coa_workbench.collector import RawArchive
from coa_workbench.collector.report_slice_capture import (
    COMBATANTS_INFO_ROUTE_SHAPE,
    ENCOUNTER_DETAIL_ROUTE_SHAPE,
    REPORT_DETAIL_ROUTE_SHAPE,
)
from coa_workbench.collector.report_slice_review import (
    review_observed_report_slice_capture,
)


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _route_inventory(path: Path) -> str:
    routes = [
        REPORT_DETAIL_ROUTE_SHAPE,
        ENCOUNTER_DETAIL_ROUTE_SHAPE,
        COMBATANTS_INFO_ROUTE_SHAPE,
    ]
    payload = {
        "schema_version": 1,
        "inventory_kind": "archived_spa_api_route_inventory",
        "endpoint_code": "build_page_asset",
        "archives": [],
        "routes": [
            {
                "route_shape": route,
                "archive_count": 1,
                "payload_hashes": ["a" * 64],
                "lexical_hints": ["report"],
                "semantic_status": "unverified_candidate",
            }
            for route in routes
        ],
        "summary": {
            "archive_count": 1,
            "route_candidate_count": len(routes),
            "lexically_relevant_candidate_count": len(routes),
            "all_archives_verified": True,
            "contains_source_record_scalar_values": False,
            "semantic_verification_required": True,
            "network_requests_performed": False,
        },
    }
    _write_json(path, payload)
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _capture_row(archive, payload: object, endpoint_kind: str, route: str) -> dict[str, object]:
    body = json.dumps(payload, sort_keys=True).encode("utf-8")
    capture = archive.capture_bytes(
        body,
        source_code="ascension_logs",
        endpoint_code=f"{endpoint_kind}_observed",
        request_key=f"GET:{route}",
        http_status=200,
        content_type="application/json",
    )
    return {
        "endpoint_kind": endpoint_kind,
        "route_template": route,
        "status": 200,
        "content_type": "application/json",
        "top_level_kind": "object",
        "top_level_keys": sorted(payload),
        "capture": {
            "raw_id": capture.raw_id,
            "observation_id": capture.observation_id,
            "payload_hash": capture.payload_hash,
            "bytes_uncompressed": capture.bytes_uncompressed,
            "content_type": capture.content_type,
            "schema_fingerprint": capture.schema_fingerprint,
            "duplicate_payload": capture.duplicate_payload,
            "duplicate_observation": capture.duplicate_observation,
            "http_status": capture.http_status,
        },
        "complete": True,
        "error": None,
    }


def _fixture(tmp_path: Path) -> tuple[Path, Path, Path]:
    raw_root = tmp_path / "raw"
    inventory_path = tmp_path / "spa-api-route-inventory.json"
    inventory_hash = _route_inventory(inventory_path)
    archive = RawArchive(raw_root)

    endpoints = [
        _capture_row(
            archive,
            {
                "report": {"id": 987654, "title": "Private Report"},
                "encounters": [{"id": 123456}],
                "summary": {},
                "success": True,
            },
            "report_detail",
            REPORT_DETAIL_ROUTE_SHAPE,
        ),
        _capture_row(
            archive,
            {
                "damage_by_character": [{"name": "Private Player"}],
                "rankings": [],
                "success": True,
            },
            "encounter_detail",
            ENCOUNTER_DETAIL_ROUTE_SHAPE,
        ),
        _capture_row(
            archive,
            {
                "combatants": [{"name": "Private Player", "guid": 123456789}],
                "success": True,
            },
            "combatants_info",
            COMBATANTS_INFO_ROUTE_SHAPE,
        ),
    ]
    capture_path = tmp_path / "observed-report-slice-capture.json"
    _write_json(
        capture_path,
        {
            "schema_version": 1,
            "capture_kind": "observed_report_slice",
            "provenance": {
                "route_inventory_hash": inventory_hash,
                "route_inventory_verified": True,
                "route_shapes": [
                    REPORT_DETAIL_ROUTE_SHAPE,
                    ENCOUNTER_DETAIL_ROUTE_SHAPE,
                    COMBATANTS_INFO_ROUTE_SHAPE,
                ],
                "http_profile_version": "coa-fetch-context-v1",
            },
            "endpoints": endpoints,
            "summary": {
                "expected_endpoint_count": 3,
                "attempted_endpoint_count": 3,
                "complete_endpoint_count": 3,
                "all_complete": True,
                "contains_source_scalar_values": False,
                "semantic_verification_required": True,
                "normalization_allowed": False,
            },
        },
    )
    return capture_path, inventory_path, raw_root


def test_review_verifies_three_archives_without_source_scalars(tmp_path):
    capture_path, inventory_path, raw_root = _fixture(tmp_path)

    review = review_observed_report_slice_capture(
        capture_path,
        route_inventory_path=inventory_path,
        raw_root=raw_root,
    )

    assert review["summary"]["raw_archive_count"] == 3
    assert review["summary"]["all_archives_consistent"] is True
    assert review["summary"]["normalization_allowed"] is False
    assert {item["endpoint_kind"] for item in review["endpoints"]} == {
        "report_detail",
        "encounter_detail",
        "combatants_info",
    }
    assert all(
        all(item["archive_verification"].values()) for item in review["endpoints"]
    )

    rendered = json.dumps(review)
    assert "Private Report" not in rendered
    assert "Private Player" not in rendered
    assert "987654" not in rendered
    assert "123456789" not in rendered


def test_review_rejects_route_inventory_hash_change(tmp_path):
    capture_path, inventory_path, raw_root = _fixture(tmp_path)
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    inventory["summary"]["route_candidate_count"] = 4
    _write_json(inventory_path, inventory)

    with pytest.raises(ValueError, match="route inventory hash mismatch"):
        review_observed_report_slice_capture(
            capture_path,
            route_inventory_path=inventory_path,
            raw_root=raw_root,
        )


def test_review_rejects_manifest_privacy_gate_change(tmp_path):
    capture_path, inventory_path, raw_root = _fixture(tmp_path)
    manifest = json.loads(capture_path.read_text(encoding="utf-8"))
    manifest["summary"]["contains_source_scalar_values"] = True
    _write_json(capture_path, manifest)

    with pytest.raises(ValueError, match="contains source scalar values"):
        review_observed_report_slice_capture(
            capture_path,
            route_inventory_path=inventory_path,
            raw_root=raw_root,
        )


def test_review_rejects_archive_metadata_mismatch(tmp_path):
    capture_path, inventory_path, raw_root = _fixture(tmp_path)
    manifest = json.loads(capture_path.read_text(encoding="utf-8"))
    manifest["endpoints"][0]["capture"]["bytes_uncompressed"] += 1
    _write_json(capture_path, manifest)

    with pytest.raises(ValueError, match="archive verification failed"):
        review_observed_report_slice_capture(
            capture_path,
            route_inventory_path=inventory_path,
            raw_root=raw_root,
        )
