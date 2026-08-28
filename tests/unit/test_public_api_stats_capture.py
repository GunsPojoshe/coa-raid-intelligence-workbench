from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import pytest

from coa_workbench.collector.public_api_stats_capture import (
    PUBLIC_API_HTTP_PROFILE_VERSION,
    capture_public_api_stats,
    public_api_stats_capture_to_dict,
)
from coa_workbench.collector.raw_archive import RawArchive
from coa_workbench.collector.source_registry import load_source_registry


class _Headers:
    def get_content_type(self) -> str:
        return "application/json"


class _Response:
    def __init__(self, body: bytes, *, status: int = 200) -> None:
        self.status = status
        self.headers = _Headers()
        self._body = body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        return None

    def read(self, size: int = -1) -> bytes:
        if size is None or size < 0:
            return self._body
        return self._body[:size]


class _RecordingOpener:
    def __init__(self, payload: object) -> None:
        self.payload = payload
        self.requests = []

    def __call__(self, request, **_kwargs):
        self.requests.append(request)
        body = json.dumps(self.payload).encode("utf-8")
        return _Response(body)


def _registry():
    return load_source_registry(Path("config/coa_public_api_sources.yaml"))


def test_statistics_capture_uses_header_auth_and_archives_before_interpretation(tmp_path) -> None:
    secret = "super-secret-local-key"
    source_payload = {
        "success": True,
        "statistics": {
            "PrivateClass": {
                "specs": {"PrivateSpec": {"avg": 12345.6, "total_parses": 99}}
            }
        },
    }
    opener = _RecordingOpener(source_payload)

    result = capture_public_api_stats(
        _registry(),
        RawArchive(tmp_path / "raw"),
        endpoint_code="public_api_statistics",
        api_key=secret,
        query={
            "phase": 2,
            "difficulty": "ascended",
            "metric": "avg_dps",
            "role": "dps",
        },
        opener=opener,
    )
    rendered = public_api_stats_capture_to_dict(result)

    assert result.complete is True
    assert len(opener.requests) == 1
    request = opener.requests[0]
    assert request.get_header("Authorization") == f"Bearer {secret}"
    parts = urlsplit(request.full_url)
    assert parts.path == "/api/public/v1/statistics"
    assert parse_qs(parts.query) == {
        "phase": ["2"],
        "difficulty": ["ascended"],
        "metric": ["avg_dps"],
        "role": ["dps"],
    }
    assert secret not in request.full_url

    assert result.capture is not None
    manifest_text = Path(result.capture.manifest_path).read_text(encoding="utf-8")
    assert secret not in manifest_text
    manifest = json.loads(manifest_text)
    assert manifest["request_url"].endswith(
        "?phase=<value>&difficulty=<value>&metric=<value>&role=<value>"
    )
    assert manifest["metadata"]["access_scope"] == "stats:read"
    assert manifest["metadata"]["credential_header_name"] == "Authorization"
    assert manifest["metadata"]["query_keys"] == ["phase", "difficulty", "metric", "role"]

    safe_output = json.dumps(rendered)
    assert secret not in safe_output
    assert "PrivateClass" not in safe_output
    assert "PrivateSpec" not in safe_output
    assert "12345.6" not in safe_output
    assert rendered["request"]["http_profile_version"] == PUBLIC_API_HTTP_PROFILE_VERSION
    assert rendered["summary"] == {
        "complete": True,
        "contains_api_key": False,
        "contains_query_values": False,
        "contains_source_scalar_values": False,
        "raw_capture_ids_included": False,
        "events_read_used": False,
        "planner_scoring_allowed": False,
    }


def test_phases_capture_allows_empty_query(tmp_path) -> None:
    opener = _RecordingOpener({"success": True, "phases": []})
    result = capture_public_api_stats(
        _registry(),
        RawArchive(tmp_path / "raw"),
        endpoint_code="public_api_phases",
        api_key="local-key",
        opener=opener,
    )

    assert result.complete is True
    assert urlsplit(opener.requests[0].full_url).path == "/api/public/v1/phases"
    assert urlsplit(opener.requests[0].full_url).query == ""
    assert result.query_keys == ()


def test_statistics_requires_phase(tmp_path) -> None:
    with pytest.raises(ValueError, match="requires the documented phase"):
        capture_public_api_stats(
            _registry(),
            RawArchive(tmp_path / "raw"),
            endpoint_code="public_api_statistics",
            api_key="local-key",
            query={"difficulty": "ascended"},
            opener=_RecordingOpener({}),
        )


def test_statistics_rejects_values_outside_documented_enums(tmp_path) -> None:
    with pytest.raises(ValueError, match="outside the documented enum"):
        capture_public_api_stats(
            _registry(),
            RawArchive(tmp_path / "raw"),
            endpoint_code="public_api_statistics",
            api_key="local-key",
            query={"phase": 2, "difficulty": "unknown"},
            opener=_RecordingOpener({}),
        )


def test_stats_collector_refuses_experimental_events_scope(tmp_path) -> None:
    with pytest.raises(ValueError, match="only self-serve stats:read"):
        capture_public_api_stats(
            _registry(),
            RawArchive(tmp_path / "raw"),
            endpoint_code="public_api_encounter_events",
            api_key="local-key",
            opener=_RecordingOpener({}),
        )


def test_api_key_cannot_be_empty_or_multiline(tmp_path) -> None:
    with pytest.raises(ValueError, match="environment variable"):
        capture_public_api_stats(
            _registry(),
            RawArchive(tmp_path / "raw"),
            endpoint_code="public_api_bosses",
            api_key="",
            opener=_RecordingOpener({}),
        )

    with pytest.raises(ValueError, match="line breaks"):
        capture_public_api_stats(
            _registry(),
            RawArchive(tmp_path / "raw"),
            endpoint_code="public_api_bosses",
            api_key="abc\ndef",
            opener=_RecordingOpener({}),
        )
