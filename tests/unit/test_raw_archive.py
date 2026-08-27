from __future__ import annotations

import base64
import gzip
import json
from datetime import datetime, timezone
from pathlib import Path

from coa_workbench.collector.raw_archive import (
    RawArchive,
    request_key_from_url,
    sanitize_url,
)


def test_capture_is_content_addressed_and_preserves_fetch_observations(tmp_path: Path) -> None:
    archive = RawArchive(tmp_path / "raw")
    arguments = {
        "source_code": "coa_ascension_logs",
        "endpoint_code": "report_metadata",
        "request_key": "report:abc",
        "fetched_at": datetime(2026, 7, 27, tzinfo=timezone.utc),
        "content_type": "application/json",
    }

    first = archive.capture_bytes(b'{"report":1}', **arguments)
    second = archive.capture_bytes(b'{"report":1}', **arguments)

    assert first.payload_hash == second.payload_hash
    assert first.raw_id == second.raw_id
    assert first.observation_id == second.observation_id
    assert first.duplicate_payload is False
    assert second.duplicate_payload is True
    assert first.duplicate_observation is False
    assert second.duplicate_observation is True
    assert gzip.open(first.payload_path, "rb").read() == b'{"report":1}'

    observation = json.loads(Path(first.manifest_path).read_text(encoding="utf-8"))
    assert observation["request_key"] == "report:abc"
    content_path = (tmp_path / "raw" / observation["content_manifest_path"]).resolve()
    content = json.loads(content_path.read_text(encoding="utf-8"))
    assert content["schema_version"] == 2
    assert content["schema_fingerprint"] == first.schema_fingerprint
    assert content["payload_path"].startswith("source=coa_ascension_logs/")
    assert "request_key" not in content
    assert "raw_id" not in content


def test_same_payload_at_a_later_time_keeps_one_payload_and_two_observations(tmp_path: Path) -> None:
    archive = RawArchive(tmp_path / "raw")
    first = archive.capture_bytes(
        b'{"report":1}',
        source_code="coa_ascension_logs",
        endpoint_code="report_metadata",
        request_key="report:abc",
        fetched_at=datetime(2026, 7, 27, 12, tzinfo=timezone.utc),
        content_type="application/json",
    )
    second = archive.capture_bytes(
        b'{"report":1}',
        source_code="coa_ascension_logs",
        endpoint_code="report_metadata",
        request_key="report:abc",
        fetched_at=datetime(2026, 7, 28, 12, tzinfo=timezone.utc),
        content_type="application/json",
    )

    assert first.raw_id == second.raw_id
    assert first.observation_id != second.observation_id
    assert first.payload_path == second.payload_path
    assert first.manifest_path != second.manifest_path


def test_same_payload_can_be_reused_by_different_request_identities(tmp_path: Path) -> None:
    archive = RawArchive(tmp_path / "raw")
    body = b'{"success":true,"statistics":{}}'
    first = archive.capture_bytes(
        body,
        source_code="coa_ascension_logs_public_api",
        endpoint_code="public_api_statistics",
        request_key="GET:/statistics?keys=phase,role#scope-one",
        fetched_at=datetime(2026, 8, 27, 18, 0, tzinfo=timezone.utc),
        content_type="application/json",
        request_url="https://coa.ascensionlogs.gg/api/public/v1/statistics?phase=12&role=dps",
    )
    second = archive.capture_bytes(
        body,
        source_code="coa_ascension_logs_public_api",
        endpoint_code="public_api_statistics",
        request_key="GET:/statistics?keys=phase,role#scope-two",
        fetched_at=datetime(2026, 8, 27, 18, 1, tzinfo=timezone.utc),
        content_type="application/json",
        request_url="https://coa.ascensionlogs.gg/api/public/v1/statistics?phase=12&role=support",
    )

    assert first.payload_hash == second.payload_hash
    assert first.payload_path == second.payload_path
    assert first.raw_id != second.raw_id
    assert first.observation_id != second.observation_id
    assert first.duplicate_payload is False
    assert second.duplicate_payload is True
    assert second.duplicate_observation is False

    first_observation = json.loads(Path(first.manifest_path).read_text(encoding="utf-8"))
    second_observation = json.loads(Path(second.manifest_path).read_text(encoding="utf-8"))
    assert first_observation["request_key"] == first.request_key
    assert second_observation["request_key"] == second.request_key
    assert first_observation["raw_id"] == first.raw_id
    assert second_observation["raw_id"] == second.raw_id
    assert first_observation["content_manifest_path"] == second_observation[
        "content_manifest_path"
    ]

    content_path = tmp_path / "raw" / first_observation["content_manifest_path"]
    content = json.loads(content_path.read_text(encoding="utf-8"))
    assert content["schema_version"] == 2
    assert "request_key" not in content
    assert "raw_id" not in content


def test_existing_schema_v1_content_manifest_is_reused_without_rewrite(tmp_path: Path) -> None:
    archive = RawArchive(tmp_path / "raw")
    body = b'{"success":true}'
    first = archive.capture_bytes(
        body,
        source_code="private_source",
        endpoint_code="public_api_statistics",
        request_key="request-one",
        fetched_at=datetime(2026, 8, 27, 18, 0, tzinfo=timezone.utc),
        content_type="application/json",
    )
    observation = json.loads(Path(first.manifest_path).read_text(encoding="utf-8"))
    content_path = tmp_path / "raw" / observation["content_manifest_path"]
    content_v2 = json.loads(content_path.read_text(encoding="utf-8"))
    legacy = {
        **content_v2,
        "schema_version": 1,
        "raw_id": first.raw_id,
        "request_key": first.request_key,
    }
    content_path.write_text(json.dumps(legacy, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    second = archive.capture_bytes(
        body,
        source_code="private_source",
        endpoint_code="public_api_statistics",
        request_key="request-two",
        fetched_at=datetime(2026, 8, 27, 18, 1, tzinfo=timezone.utc),
        content_type="application/json",
    )

    assert second.duplicate_payload is True
    assert second.raw_id != first.raw_id
    assert json.loads(content_path.read_text(encoding="utf-8")) == legacy
    second_observation = json.loads(Path(second.manifest_path).read_text(encoding="utf-8"))
    assert second_observation["request_key"] == "request-two"


def test_sanitize_url_drops_values_and_secrets() -> None:
    value = sanitize_url("https://coa.ascensionlogs.gg/api/report/7?token=secret&page=2")
    assert "secret" not in value
    assert "page=2" not in value
    assert "token=<redacted>" in value
    assert "page=<value>" in value
    assert request_key_from_url(
        "GET", "https://coa.ascensionlogs.gg/api/report/7?page=2"
    ).startswith("GET:/api/report/7?keys=page#")


def test_har_import_filters_host_decodes_base64_and_drops_query_values(tmp_path: Path) -> None:
    body = b'{"events":[1]}'
    har = {
        "log": {
            "entries": [
                {
                    "startedDateTime": "2026-07-27T00:00:00Z",
                    "request": {
                        "method": "GET",
                        "url": "https://coa.ascensionlogs.gg/api/events?report=abc&token=secret",
                    },
                    "response": {
                        "status": 200,
                        "headers": [{"name": "content-type", "value": "application/json"}],
                        "content": {
                            "mimeType": "application/json",
                            "encoding": "base64",
                            "text": base64.b64encode(body).decode(),
                        },
                    },
                },
                {
                    "request": {"method": "GET", "url": "https://tracker.invalid/pixel"},
                    "response": {
                        "status": 200,
                        "content": {"mimeType": "text/plain", "text": "x"},
                    },
                },
            ]
        }
    }
    path = tmp_path / "session.har"
    path.write_text(json.dumps(har), encoding="utf-8")

    captures = RawArchive(tmp_path / "raw").import_har(
        path,
        source_code="coa_ascension_logs",
        allowed_host="coa.ascensionlogs.gg",
    )

    assert len(captures) == 1
    assert gzip.open(captures[0].payload_path, "rb").read() == body
    manifest = Path(captures[0].manifest_path).read_text(encoding="utf-8")
    assert "report=abc" not in manifest
    assert "secret" not in manifest
    assert "token=<redacted>" in manifest
