from __future__ import annotations

import gzip
import json
from pathlib import Path
from urllib.parse import urlsplit

import pytest

from coa_workbench.collector import RawArchive, load_source_registry
from coa_workbench.collector.report_discovery import (
    capture_public_report_discovery,
    report_discovery_capture_to_dict,
)


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
        body = self.payload if isinstance(self.payload, bytes) else json.dumps(self.payload).encode()
        return _Response(body)


def _registry():
    return load_source_registry(Path("config/ascension_logs_sources.yaml"))


def test_default_capture_is_bounded_and_archives_before_interpretation(tmp_path):
    source_payload = {
        "reports": [
            {
                "id": 987654,
                "guild_name": "Private Guild",
                "owner_name": "Private Player",
            }
        ],
        "pagination": {"page": 1, "pages": 42},
        "success": True,
    }
    opener = _RecordingOpener(source_payload)
    raw_root = tmp_path / "raw"

    result = capture_public_report_discovery(
        _registry(),
        RawArchive(raw_root),
        opener=opener,
    )
    rendered = report_discovery_capture_to_dict(result)

    assert result.complete is True
    assert result.page == 1
    assert result.limit == 5
    assert result.top_level_kind == "object"
    assert result.top_level_keys == ("pagination", "reports", "success")
    assert len(opener.requests) == 1
    parts = urlsplit(opener.requests[0].full_url)
    assert parts.path == "/api/reports/public"
    assert parts.query == "page=1&limit=5&sortBy=created_at&sortOrder=desc"

    assert result.capture is not None
    archived = json.loads(gzip.decompress(Path(result.capture.payload_path).read_bytes()))
    assert archived == source_payload

    safe_output = json.dumps(rendered)
    assert "Private Guild" not in safe_output
    assert "Private Player" not in safe_output
    assert "987654" not in safe_output
    assert rendered["summary"] == {
        "complete": True,
        "contains_source_scalar_values": False,
        "category_semantics_verified": False,
        "pagination_policy_verified": False,
    }


def test_capture_metadata_contains_profile_names_but_not_header_values(tmp_path):
    opener = _RecordingOpener({"reports": [], "success": True})
    result = capture_public_report_discovery(
        _registry(),
        RawArchive(tmp_path / "raw"),
        local_category="public_recent",
        opener=opener,
    )

    assert result.capture is not None
    manifest = json.loads(Path(result.capture.manifest_path).read_text(encoding="utf-8"))
    metadata = manifest["metadata"]
    assert metadata["capture_mode"] == "bounded_report_discovery"
    assert metadata["local_category"] == "public_recent"
    assert metadata["limit"] == 5
    assert metadata["limit_contract"] == "verified_bounded"
    serialized = json.dumps(metadata).casefold()
    assert "mozilla/5.0" not in serialized
    assert "same-origin" not in serialized
    assert "application/json, text/plain" not in serialized


@pytest.mark.parametrize("limit", [0, 6])
def test_capture_rejects_unbounded_limit(limit, tmp_path):
    with pytest.raises(ValueError, match="between 1 and 5"):
        capture_public_report_discovery(
            _registry(),
            RawArchive(tmp_path / "raw"),
            limit=limit,
            opener=lambda *_args, **_kwargs: None,
        )


def test_capture_allows_larger_limit_only_for_explicit_probe(tmp_path):
    payload = {
        "reports": [{"id": value} for value in range(25)],
        "pagination": {
            "page": 1,
            "limit": 25,
            "offset": 0,
            "hasPrevious": False,
            "hasMore": True,
        },
        "success": True,
    }
    opener = _RecordingOpener(payload)

    result = capture_public_report_discovery(
        _registry(),
        RawArchive(tmp_path / "raw"),
        limit=25,
        allow_unverified_limit_probe=True,
        opener=opener,
    )

    assert result.complete is True
    assert urlsplit(opener.requests[0].full_url).query == (
        "page=1&limit=25&sortBy=created_at&sortOrder=desc"
    )
    assert result.capture is not None
    manifest = json.loads(Path(result.capture.manifest_path).read_text(encoding="utf-8"))
    assert manifest["metadata"]["limit_contract"] == "unverified_probe"


def test_capture_rejects_limit_above_probe_ceiling(tmp_path):
    with pytest.raises(ValueError, match="between 1 and 500"):
        capture_public_report_discovery(
            _registry(),
            RawArchive(tmp_path / "raw"),
            limit=501,
            allow_unverified_limit_probe=True,
            opener=lambda *_args, **_kwargs: None,
        )


def test_capture_rejects_unobserved_sort_values(tmp_path):
    with pytest.raises(ValueError, match="observed value"):
        capture_public_report_discovery(
            _registry(),
            RawArchive(tmp_path / "raw"),
            sort_by="duration",
            opener=lambda *_args, **_kwargs: None,
        )

    with pytest.raises(ValueError, match="observed value"):
        capture_public_report_discovery(
            _registry(),
            RawArchive(tmp_path / "raw"),
            sort_order="asc",
            opener=lambda *_args, **_kwargs: None,
        )


def test_invalid_json_is_archived_and_not_marked_complete(tmp_path):
    result = capture_public_report_discovery(
        _registry(),
        RawArchive(tmp_path / "raw"),
        opener=_RecordingOpener(b"{broken"),
    )

    assert result.capture is not None
    assert Path(result.capture.payload_path).is_file()
    assert result.complete is False
    assert result.error == "response was not valid JSON"
    assert report_discovery_capture_to_dict(result)["summary"]["complete"] is False


def test_transport_failure_does_not_create_capture(tmp_path):
    def timeout(*_args, **_kwargs):
        raise TimeoutError

    result = capture_public_report_discovery(
        _registry(),
        RawArchive(tmp_path / "raw"),
        timeout_seconds=1,
        opener=timeout,
    )

    assert result.capture is None
    assert result.complete is False
    assert "timeout" in (result.error or "")
