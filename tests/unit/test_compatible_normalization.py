from __future__ import annotations

import json
from pathlib import Path

import pytest

from coa_workbench.collector.compatible_normalization import (
    normalize_verified_compatible_payload,
)


def _mapping_path() -> Path:
    return Path(__file__).resolve().parents[2] / "config" / "mappings" / "coa_report_detail_v1.json"


def _payload() -> dict[str, object]:
    return {
        "success": True,
        "report": {
            "id": 123,
            "title": "Example Report",
            "created_at": "2026-08-14T00:00:00Z",
            "start_time": "2026-08-14T00:00:00Z",
            "end_time": "2026-08-14T01:00:00Z",
            "visibility": "public",
            "timezone": "UTC",
            "realm": "Example",
            "zone": "Example Zone",
            "status": "complete",
            "has_telemetry": True,
            "new_additive_upstream_field": {"ignored": True},
        },
        "encounters": [
            {
                "id": 1,
                "name": "Boss One",
                "start_time": "2026-08-14T00:01:00Z",
                "end_time": "2026-08-14T00:05:00Z",
                "success": True,
                "kill_time": {"minutes": 4},
                "wipe_percent": None,
                "new_encounter_field": 123,
            },
            {
                "id": 2,
                "name": "Boss Two",
                "start_time": "2026-08-14T00:10:00Z",
                "end_time": "2026-08-14T00:15:00Z",
                "success": False,
                "kill_time": None,
                "wipe_percent": "12.5",
            },
        ],
        "summary": {
            "total_encounters": 2,
            "successful_encounters": 1,
            "duration": 3600,
        },
    }


def test_verified_report_mapping_accepts_additive_runtime_fields() -> None:
    mapping = json.loads(_mapping_path().read_text(encoding="utf-8"))
    result = normalize_verified_compatible_payload(_payload(), mapping)
    summary = result.public_summary()

    assert summary["mapping_id"] == "coa-report-detail-v1"
    assert summary["verified_field_contract_count"] == 19
    assert summary["counts"] == {
        "reports": 1,
        "encounters": 2,
        "actors": 0,
        "participants": 0,
        "aura_events": 0,
        "rejects": 0,
    }
    assert summary["ignored_additive_fields_allowed"] is True
    assert summary["mechanic_semantics_verified"] is False


def test_verified_report_mapping_fails_closed_when_mapped_type_changes() -> None:
    mapping = json.loads(_mapping_path().read_text(encoding="utf-8"))
    payload = _payload()
    payload["report"]["title"] = 123

    with pytest.raises(ValueError, match="parser field type mismatch"):
        normalize_verified_compatible_payload(payload, mapping)
