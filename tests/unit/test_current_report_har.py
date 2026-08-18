from __future__ import annotations

import json
from pathlib import Path

import pytest

from coa_workbench.collector.current_report_har import extract_current_report_har_slice


def _entry(path: str, body: dict[str, object], *, timestamp: str) -> dict[str, object]:
    return {
        "startedDateTime": timestamp,
        "_resourceType": "xhr",
        "request": {
            "method": "GET",
            "url": f"https://coa.ascensionlogs.gg{path}",
        },
        "response": {
            "status": 200,
            "content": {
                "mimeType": "application/json",
                "text": json.dumps(body),
            },
        },
    }


def _write_har(path: Path, entries: list[dict[str, object]]) -> None:
    path.write_text(json.dumps({"log": {"entries": entries}}), encoding="utf-8")


def test_extract_current_report_har_slice_uses_one_correlated_report(tmp_path: Path) -> None:
    har = tmp_path / "report.har"
    entries = [
        _entry(
            "/api/reports/123",
            {"success": True, "report": {"id": 123}, "encounters": [], "summary": {}},
            timestamp="2026-08-14T12:00:00.000Z",
        ),
        _entry(
            "/api/reports/123/encounters?includeTrash=false",
            {"success": True, "encounters": [], "summary": {}},
            timestamp="2026-08-14T12:00:00.010Z",
        ),
        _entry(
            "/api/reports/123/combatants-roster?encounterIds=1",
            {"success": True, "roster": []},
            timestamp="2026-08-14T12:00:00.020Z",
        ),
        _entry(
            "/api/reports/123/encounters/1/throughput-timeline?metric=damage",
            {"success": True, "series": {}},
            timestamp="2026-08-14T12:00:00.030Z",
        ),
        _entry(
            "/api/reports/123/character_damage_taken_abilities?encounterIds[]=1",
            {"success": True, "damage_taken_abilities_by_target": {}},
            timestamp="2026-08-14T12:00:00.040Z",
        ),
        _entry(
            "/api/reports/123/character_spell_healing?encounterIds[]=1",
            {"success": True, "spell_healing_by_source": {}},
            timestamp="2026-08-14T12:00:00.050Z",
        ),
        _entry(
            "/api/reports/queue-status",
            {"success": True, "report": "not-a-detail"},
            timestamp="2026-08-14T12:00:00.060Z",
        ),
    ]
    _write_har(har, entries)

    result = extract_current_report_har_slice(har)

    assert result.report_detail.endpoint_code == "report_detail_api"
    assert result.encounter_catalog.endpoint_code == "report_encounters_api"
    assert result.combatants_roster.endpoint_code == "report_combatants_roster_api"
    assert len(result.throughput) == 1
    assert result.public_summary() == {
        "extractor_version": "current-report-har-extractor-v1",
        "report_detail_count": 1,
        "encounter_catalog_count": 1,
        "combatants_roster_count": 1,
        "throughput_count": 1,
        "damage_taken_abilities_count": 1,
        "spell_healing_count": 1,
        "contains_report_ids": False,
        "contains_encounter_ids": False,
        "contains_query_values": False,
        "contains_response_bodies": False,
    }


def test_extract_current_report_har_slice_fails_closed_on_multiple_report_details(
    tmp_path: Path,
) -> None:
    har = tmp_path / "multiple.har"
    _write_har(
        har,
        [
            _entry(
                "/api/reports/123",
                {"report": {}, "encounters": [], "summary": {}},
                timestamp="2026-08-14T12:00:00.000Z",
            ),
            _entry(
                "/api/reports/456",
                {"report": {}, "encounters": [], "summary": {}},
                timestamp="2026-08-14T12:01:00.000Z",
            ),
        ],
    )

    with pytest.raises(ValueError, match="exactly one concrete report detail"):
        extract_current_report_har_slice(har)
