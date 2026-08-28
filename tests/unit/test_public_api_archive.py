from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from coa_workbench.collector.public_api_archive import load_latest_public_api_capture
from coa_workbench.collector.raw_archive import RawArchive


def test_private_archive_loader_preserves_query_scope_without_publication(tmp_path: Path) -> None:
    raw_root = tmp_path / "raw"
    payload = {
        "success": True,
        "phase": 12,
        "difficulty": "all",
        "metric": "avg_dps",
        "statistics": {},
    }
    payload_bytes = json.dumps(payload).encode("utf-8")
    capture = RawArchive(raw_root).capture_bytes(
        payload_bytes,
        source_code="private_source",
        endpoint_code="public_api_statistics",
        request_key="GET:/statistics?keys=phase,role#private",
        http_status=200,
        content_type="application/json",
        metadata={
            "query_keys": ["phase", "role"],
            "private_query_values": {"phase": "12", "role": "dps"},
        },
    )

    loaded = load_latest_public_api_capture(
        raw_root,
        source_code="private_source",
        endpoint_code="public_api_statistics",
    )

    assert loaded.raw_id == capture.raw_id
    assert loaded.observation_id == capture.observation_id
    assert loaded.request_key == capture.request_key
    assert loaded.query_keys == ("phase", "role")
    assert loaded.query_value_mapping() == {"phase": "12", "role": "dps"}
    assert loaded.payload == payload
    assert loaded.payload_bytes == payload_bytes
    assert loaded.http_status == 200
    assert loaded.content_type == "application/json"

    reconstructed = loaded.as_raw_capture(raw_root)
    assert reconstructed.raw_id == capture.raw_id
    assert reconstructed.observation_id == capture.observation_id
    assert reconstructed.request_key == capture.request_key
    assert reconstructed.payload_hash == capture.payload_hash
    assert reconstructed.schema_fingerprint == capture.schema_fingerprint
    assert reconstructed.http_status == 200


def test_loader_uses_latest_observation_request_identity_for_shared_payload(tmp_path: Path) -> None:
    raw_root = tmp_path / "raw"
    archive = RawArchive(raw_root)
    payload_bytes = json.dumps(
        {"success": True, "phase": 12, "statistics": {}},
        sort_keys=True,
    ).encode("utf-8")
    first = archive.capture_bytes(
        payload_bytes,
        source_code="private_source",
        endpoint_code="public_api_statistics",
        request_key="GET:/statistics?keys=phase,role#first",
        fetched_at=datetime(2026, 8, 27, 18, 0, tzinfo=timezone.utc),
        http_status=200,
        content_type="application/json",
        metadata={
            "query_keys": ["phase", "role"],
            "private_query_values": {"phase": "12", "role": "dps"},
        },
    )
    second = archive.capture_bytes(
        payload_bytes,
        source_code="private_source",
        endpoint_code="public_api_statistics",
        request_key="GET:/statistics?keys=phase,role#second",
        fetched_at=datetime(2026, 8, 27, 18, 1, tzinfo=timezone.utc),
        http_status=200,
        content_type="application/json",
        metadata={
            "query_keys": ["phase", "role"],
            "private_query_values": {"phase": "12", "role": "support"},
        },
    )

    loaded = load_latest_public_api_capture(
        raw_root,
        source_code="private_source",
        endpoint_code="public_api_statistics",
    )

    assert first.payload_hash == second.payload_hash
    assert first.raw_id != second.raw_id
    assert loaded.raw_id == second.raw_id
    assert loaded.request_key == second.request_key
    assert loaded.query_value_mapping() == {"phase": "12", "role": "support"}


def test_private_archive_loader_keeps_legacy_missing_query_values_explicit(tmp_path: Path) -> None:
    raw_root = tmp_path / "raw"
    RawArchive(raw_root).capture_bytes(
        json.dumps({"success": True, "statistics": {}}).encode("utf-8"),
        source_code="private_source",
        endpoint_code="public_api_statistics",
        request_key="legacy",
        content_type="application/json",
        metadata={"query_keys": ["phase", "role"]},
    )

    loaded = load_latest_public_api_capture(
        raw_root,
        source_code="private_source",
        endpoint_code="public_api_statistics",
    )

    assert loaded.query_keys == ("phase", "role")
    assert loaded.query_values == ()


def test_private_archive_loader_reads_legacy_request_identity_from_content_manifest(
    tmp_path: Path,
) -> None:
    raw_root = tmp_path / "raw"
    capture = RawArchive(raw_root).capture_bytes(
        json.dumps({"success": True, "statistics": {}}).encode("utf-8"),
        source_code="private_source",
        endpoint_code="public_api_statistics",
        request_key="legacy-request-key",
        fetched_at=datetime(2026, 8, 27, 18, 0, tzinfo=timezone.utc),
        content_type="application/json",
        metadata={"query_keys": ["phase"]},
    )
    observation_path = Path(capture.manifest_path)
    observation = json.loads(observation_path.read_text(encoding="utf-8"))
    observation.pop("request_key")
    observation_path.write_text(
        json.dumps(observation, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    content_path = raw_root / observation["content_manifest_path"]
    content = json.loads(content_path.read_text(encoding="utf-8"))
    content.update(
        {
            "schema_version": 1,
            "raw_id": capture.raw_id,
            "request_key": capture.request_key,
        }
    )
    content_path.write_text(
        json.dumps(content, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    loaded = load_latest_public_api_capture(
        raw_root,
        source_code="private_source",
        endpoint_code="public_api_statistics",
    )

    assert loaded.raw_id == capture.raw_id
    assert loaded.request_key == "legacy-request-key"
    assert loaded.query_keys == ("phase",)
