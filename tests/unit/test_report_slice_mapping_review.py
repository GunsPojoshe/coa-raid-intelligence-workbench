from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path

import pytest

from coa_workbench.collector import report_slice_mapping_review as mapping_review
from coa_workbench.collector.report_slice_capture import (
    COMBATANTS_INFO_ROUTE_SHAPE,
    ENCOUNTER_DETAIL_ROUTE_SHAPE,
    REPORT_DETAIL_ROUTE_SHAPE,
)


def _endpoint(
    raw_root: Path,
    endpoint_kind: str,
    route_template: str,
    payload: object,
) -> dict[str, object]:
    body = json.dumps(payload, sort_keys=True).encode("utf-8")
    payload_hash = hashlib.sha256(body).hexdigest()
    relative_path = Path(endpoint_kind) / f"{payload_hash}.json.gz"
    path = raw_root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(gzip.compress(body))
    return {
        "endpoint_kind": endpoint_kind,
        "route_template": route_template,
        "payload_hash": payload_hash,
        "schema_fingerprint": "f" * 64,
        "bytes_uncompressed": len(body),
        "payload_path": relative_path.as_posix(),
        "top_level_kind": "object",
        "top_level_keys": sorted(payload),
        "candidate_collections": [{"path": "/items", "length": 1}],
        "archive_verification": {
            "payload_hash": True,
            "schema_fingerprint": True,
            "bytes_uncompressed": True,
            "top_level_kind": True,
            "top_level_keys": True,
            "http_status": True,
            "content_type": True,
        },
    }


def _structural(raw_root: Path) -> dict[str, object]:
    endpoints = [
        _endpoint(
            raw_root,
            "report_detail",
            REPORT_DETAIL_ROUTE_SHAPE,
            {
                "report": {"id": 987654, "title": "Private Report"},
                "encounters": [{"id": 123456, "name": "Private Encounter"}],
                "success": True,
            },
        ),
        _endpoint(
            raw_root,
            "encounter_detail",
            ENCOUNTER_DETAIL_ROUTE_SHAPE,
            {
                "actors": {
                    "123456": {"name": "Private Player", "amount": 42},
                    "987654": {"name": "Second Player", "amount": None},
                },
                "events": [{"source": 123456, "target": 987654}],
                "success": True,
            },
        ),
        _endpoint(
            raw_root,
            "combatants_info",
            COMBATANTS_INFO_ROUTE_SHAPE,
            {
                "combatants": [
                    {"name": "Private Player", "guid": 123456789, "spec": "Secret"}
                ],
                "success": True,
            },
        ),
    ]
    return {
        "schema_version": 1,
        "review_kind": "observed_report_slice_structural_review",
        "provenance": {
            "route_inventory_hash": "a" * 64,
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
            "raw_archive_count": 3,
            "candidate_collection_count": 3,
            "all_archives_consistent": True,
            "contains_source_scalar_values": False,
            "semantic_verification_required": True,
            "normalization_allowed": False,
        },
    }


def test_mapping_review_is_full_root_scalar_free_and_candidate(monkeypatch, tmp_path):
    raw_root = tmp_path / "raw"
    structural = _structural(raw_root)
    monkeypatch.setattr(
        mapping_review,
        "review_observed_report_slice_capture",
        lambda *_args, **_kwargs: structural,
    )

    review = mapping_review.build_observed_report_slice_mapping_review(
        tmp_path / "capture.json",
        route_inventory_path=tmp_path / "inventory.json",
        raw_root=raw_root,
    )

    assert review["summary"]["endpoint_count"] == 3
    assert review["summary"]["raw_archive_count"] == 3
    assert review["summary"]["all_archives_consistent"] is True
    assert review["summary"]["contains_source_scalar_values"] is False
    assert review["summary"]["semantic_verification_required"] is True
    assert review["summary"]["normalization_allowed"] is False
    assert review["summary"]["ready_for_manual_mapping_review"] is True
    assert all(endpoint["scope"] == "/" for endpoint in review["endpoints"])
    assert all(endpoint["review_status"] == "candidate" for endpoint in review["endpoints"])

    encounter = next(
        endpoint
        for endpoint in review["endpoints"]
        if endpoint["endpoint_kind"] == "encounter_detail"
    )
    paths = {shape["path"] for shape in encounter["field_shapes"]}
    assert "/actors/*/name" in paths
    assert "/actors/123456/name" not in paths
    assert encounter["summary"]["numeric_map_path_count"] == 1
    assert encounter["summary"]["nullable_path_count"] == 1

    rendered = json.dumps(review)
    assert "Private Report" not in rendered
    assert "Private Encounter" not in rendered
    assert "Private Player" not in rendered
    assert "Second Player" not in rendered
    assert "123456789" not in rendered
    assert '"123456"' not in rendered
    assert '"987654"' not in rendered


def test_mapping_review_rejects_non_positive_node_limit(monkeypatch, tmp_path):
    monkeypatch.setattr(
        mapping_review,
        "review_observed_report_slice_capture",
        lambda *_args, **_kwargs: _structural(tmp_path / "raw"),
    )

    with pytest.raises(ValueError, match="must be positive"):
        mapping_review.build_observed_report_slice_mapping_review(
            tmp_path / "capture.json",
            route_inventory_path=tmp_path / "inventory.json",
            raw_root=tmp_path / "raw",
            max_nodes_per_endpoint=0,
        )


def test_mapping_review_enforces_bounded_node_walk(monkeypatch, tmp_path):
    raw_root = tmp_path / "raw"
    structural = _structural(raw_root)
    monkeypatch.setattr(
        mapping_review,
        "review_observed_report_slice_capture",
        lambda *_args, **_kwargs: structural,
    )

    with pytest.raises(ValueError, match="max_nodes_per_endpoint=2"):
        mapping_review.build_observed_report_slice_mapping_review(
            tmp_path / "capture.json",
            route_inventory_path=tmp_path / "inventory.json",
            raw_root=raw_root,
            max_nodes_per_endpoint=2,
        )


def test_mapping_review_detects_payload_change_after_structural_review(
    monkeypatch,
    tmp_path,
):
    raw_root = tmp_path / "raw"
    structural = _structural(raw_root)
    endpoint = structural["endpoints"][0]
    path = raw_root / endpoint["payload_path"]
    path.write_bytes(gzip.compress(b'{"changed":true}'))
    monkeypatch.setattr(
        mapping_review,
        "review_observed_report_slice_capture",
        lambda *_args, **_kwargs: structural,
    )

    with pytest.raises(ValueError, match="hash changed"):
        mapping_review.build_observed_report_slice_mapping_review(
            tmp_path / "capture.json",
            route_inventory_path=tmp_path / "inventory.json",
            raw_root=raw_root,
        )
