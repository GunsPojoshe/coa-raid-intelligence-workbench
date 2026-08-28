from __future__ import annotations

import json
from pathlib import Path

import pytest

from coa_workbench.collector import RawArchive, load_source_registry
from coa_workbench.collector.report_discovery import (
    capture_public_report_discovery,
    report_discovery_capture_to_dict,
)
from coa_workbench.collector.report_discovery_mapping_review import (
    build_report_discovery_mapping_review,
)


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
        return self._body if size is None or size < 0 else self._body[:size]


def _capture(tmp_path: Path) -> tuple[Path, Path]:
    source_payload = {
        "reports": [
            {
                "id": 987654,
                "guild_name": "Private Guild",
                "owner_name": "Private Player",
                "encounters": [{"id": 123, "duration": 4567}],
            },
            {
                "id": 987655,
                "guild_name": "Another Guild",
                "owner_name": None,
                "encounters": [],
            },
        ],
        "pagination": {"page": 1, "pages": 42},
        "success": True,
    }
    body = json.dumps(source_payload).encode("utf-8")

    def opener(*_args, **_kwargs):
        return _Response(body)

    raw_root = tmp_path / "raw"
    registry = load_source_registry(Path("config/ascension_logs_sources.yaml"))
    result = capture_public_report_discovery(
        registry,
        RawArchive(raw_root),
        opener=opener,
    )
    capture_path = tmp_path / "report-discovery-page.json"
    capture_path.write_text(
        json.dumps(report_discovery_capture_to_dict(result)),
        encoding="utf-8",
    )
    return capture_path, raw_root


def test_mapping_review_profiles_full_root_without_scalar_values(tmp_path):
    capture_path, raw_root = _capture(tmp_path)

    result = build_report_discovery_mapping_review(capture_path, raw_root=raw_root)

    assert result["summary"]["archive_verified"] == 1
    assert result["summary"]["field_path_count"] > 0
    assert result["summary"]["node_occurrence_count"] > 0
    assert result["summary"]["contains_source_scalar_values"] is False
    assert result["summary"]["category_semantics_verified"] is False
    assert result["summary"]["pagination_policy_verified"] is False
    assert result["summary"]["ready_for_manual_mapping_review"] is True
    assert result["payload"]["review_status"] == "candidate"
    paths = {item["path"] for item in result["payload"]["field_shapes"]}
    assert "/reports/*/id" in paths
    assert "/reports/*/encounters/*/duration" in paths

    serialized = json.dumps(result)
    assert "Private Guild" not in serialized
    assert "Private Player" not in serialized
    assert "987654" not in serialized
    assert "4567" not in serialized


def test_mapping_review_records_nullable_and_collection_counts(tmp_path):
    capture_path, raw_root = _capture(tmp_path)

    result = build_report_discovery_mapping_review(capture_path, raw_root=raw_root)
    shapes = {item["path"]: item for item in result["payload"]["field_shapes"]}

    owner = shapes["/reports/*/owner_name"]
    assert owner["nullable"] is True
    assert owner["type_counts"] == {"null": 1, "string": 1}
    reports = shapes["/reports"]
    assert reports["array"]["min_length"] == 2
    assert reports["array"]["max_length"] == 2
    encounters = shapes["/reports/*/encounters"]
    assert encounters["array"]["total_items"] == 1


def test_mapping_review_rejects_non_positive_or_exceeded_node_limit(tmp_path):
    capture_path, raw_root = _capture(tmp_path)

    with pytest.raises(ValueError, match="max_nodes must be positive"):
        build_report_discovery_mapping_review(capture_path, raw_root=raw_root, max_nodes=0)

    with pytest.raises(ValueError, match="exceeded max_nodes=1"):
        build_report_discovery_mapping_review(capture_path, raw_root=raw_root, max_nodes=1)
