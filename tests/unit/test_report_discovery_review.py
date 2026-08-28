from __future__ import annotations

import json
from pathlib import Path

import pytest

from coa_workbench.collector import RawArchive, load_source_registry
from coa_workbench.collector.report_discovery import (
    capture_public_report_discovery,
    report_discovery_capture_to_dict,
)
from coa_workbench.collector.report_discovery_review import review_report_discovery_capture


class _Headers:
    def get_content_type(self) -> str:
        return "application/json"


class _Response:
    def __init__(self, body: bytes) -> None:
        self.status = 200
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


class _Opener:
    def __init__(self, payload: object) -> None:
        self._body = json.dumps(payload).encode("utf-8")

    def __call__(self, _request, **_kwargs):
        return _Response(self._body)


def _capture_manifest(tmp_path: Path) -> tuple[Path, Path]:
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
    raw_root = tmp_path / "raw"
    registry = load_source_registry(Path("config/ascension_logs_sources.yaml"))
    result = capture_public_report_discovery(
        registry,
        RawArchive(raw_root),
        opener=_Opener(source_payload),
    )
    assert result.complete is True

    manifest_path = tmp_path / "report-discovery-page.json"
    manifest_path.write_text(
        json.dumps(report_discovery_capture_to_dict(result)),
        encoding="utf-8",
    )
    return manifest_path, raw_root


def test_review_verifies_exact_archive_without_source_values(tmp_path):
    manifest_path, raw_root = _capture_manifest(tmp_path)

    result = review_report_discovery_capture(manifest_path, raw_root=raw_root)

    assert result["summary"]["archive_verified"] == 1
    assert result["summary"]["all_consistent"] is True
    assert result["summary"]["contains_source_scalar_values"] is False
    assert result["request"]["limit"] == 5
    assert result["response"]["top_level_kind"] == "object"
    assert result["response"]["top_level_keys"] == ["pagination", "reports", "success"]
    assert all(result["response"]["archive_verification"].values())

    serialized = json.dumps(result)
    assert "Private Guild" not in serialized
    assert "Private Player" not in serialized
    assert "987654" not in serialized


def test_review_rejects_missing_hash_archive(tmp_path):
    manifest_path, raw_root = _capture_manifest(tmp_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["response"]["capture"]["payload_hash"] = "0" * 64
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(FileNotFoundError, match="archived JSON payload hash not found"):
        review_report_discovery_capture(manifest_path, raw_root=raw_root)


def test_review_rejects_fingerprint_mismatch(tmp_path):
    manifest_path, raw_root = _capture_manifest(tmp_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["response"]["capture"]["schema_fingerprint"] = "0" * 64
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(ValueError, match="schema_fingerprint"):
        review_report_discovery_capture(manifest_path, raw_root=raw_root)


def test_review_rejects_manifest_shape_mismatch(tmp_path):
    manifest_path, raw_root = _capture_manifest(tmp_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["response"]["top_level_keys"] = ["reports"]
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(ValueError, match="top_level_keys"):
        review_report_discovery_capture(manifest_path, raw_root=raw_root)


def test_review_rejects_scalar_leakage_flag(tmp_path):
    manifest_path, raw_root = _capture_manifest(tmp_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["summary"]["contains_source_scalar_values"] = True
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(ValueError, match="contains source scalar values"):
        review_report_discovery_capture(manifest_path, raw_root=raw_root)
