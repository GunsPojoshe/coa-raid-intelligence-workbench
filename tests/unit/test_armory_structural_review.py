from __future__ import annotations

import json
from pathlib import Path

import pytest

from coa_workbench.collector import RawArchive
from coa_workbench.collector.armory_structural_review import review_armory_capture_manifest


def _capture_manifest(tmp_path: Path) -> tuple[Path, Path]:
    raw_root = tmp_path / "raw"
    archive = RawArchive(raw_root)
    payloads = {
        "character": {"success": True, "capture": {"id": 156120}, "stats_summary": {}},
        "talent_grid": {"success": True, "class_name": "Felsworn", "trees": []},
    }
    endpoints = {}
    for endpoint_kind, payload in payloads.items():
        body = json.dumps(payload).encode("utf-8")
        capture = archive.capture_bytes(
            body,
            source_code="coa_ascension_logs",
            endpoint_code=f"armory_api_{endpoint_kind}",
            request_key=f"GET:/api/armory/{endpoint_kind}",
            http_status=200,
            content_type="application/json",
        )
        endpoints[endpoint_kind] = {
            "state": "captured",
            "route": f"https://coa.ascensionlogs.gg/api/armory/{endpoint_kind}",
            "status": 200,
            "content_type": "application/json",
            "capture": {
                "payload_hash": capture.payload_hash,
                "schema_fingerprint": capture.schema_fingerprint,
                "bytes_uncompressed": capture.bytes_uncompressed,
                "payload_path": Path(capture.payload_path).relative_to(raw_root).as_posix(),
            },
        }

    manifest = {
        "schema_version": 1,
        "capture_mode": "endpoint_isolated_armory_api",
        "http_profile_version": "coa-fetch-context-v1",
        "subject": {"character_id": "156120", "class_slug": "felsworn"},
        "endpoint_order": ["character", "talent_grid"],
        "endpoints": endpoints,
    }
    manifest_path = tmp_path / "capture.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    return manifest_path, raw_root


def test_review_verifies_archive_and_reports_structure_without_values(tmp_path):
    manifest_path, raw_root = _capture_manifest(tmp_path)

    result = review_armory_capture_manifest(manifest_path, raw_root=raw_root)

    assert result["summary"] == {
        "endpoint_count": 2,
        "archive_verified": 2,
        "all_consistent": True,
    }
    assert result["endpoint_order"] == ["character", "talent_grid"]
    character = result["endpoints"][0]
    assert character["top_level_keys"] == ["capture", "stats_summary", "success"]
    assert all(character["archive_verification"].values())
    serialized = json.dumps(result)
    assert "Felsworn" not in serialized
    assert "156120" in serialized


def test_review_rejects_manifest_hash_mismatch(tmp_path):
    manifest_path, raw_root = _capture_manifest(tmp_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["endpoints"]["character"]["capture"]["payload_hash"] = "0" * 64
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(FileNotFoundError, match="archived JSON payload hash not found"):
        review_armory_capture_manifest(manifest_path, raw_root=raw_root)
