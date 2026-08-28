from __future__ import annotations

import json
from pathlib import Path

import pytest

from coa_workbench.analytics.public_api_encounter_context import EncounterReference
from coa_workbench.analytics.report_encounter_source_correlation import (
    correlate_report_encounter_catalog_payload,
    load_archived_report_encounter_catalog,
)
from coa_workbench.collector.raw_archive import RawArchive, request_key_from_url


pytest.importorskip("duckdb")

_SOURCE_CODE = "coa_ascension_logs"
_BASE_URL = "https://coa.ascensionlogs.gg"


def _reference() -> EncounterReference:
    return EncounterReference(report_id=98765431, encounter_id=87654321)


def _payload(*, difficulty: str = "ascended") -> dict[str, object]:
    return {
        "success": True,
        "report": {"id": 98765431, "title": "Example Report"},
        "encounters": [
            {
                "id": 87654321,
                "name": "Example Boss",
                "difficulty": difficulty,
                "is_boss_encounter": True,
                "zone": "Example Raid",
                "boss_id": 76543210,
            }
        ],
        "summary": {"total_encounters": 1},
    }


def _capture(
    *,
    raw_root: Path,
    database: Path,
    migrations: Path,
    payload: dict[str, object],
) -> None:
    url = f"{_BASE_URL}/api/reports/98765431/encounters?includeTrash=false"
    archive = RawArchive(raw_root, database_path=database, migrations_dir=migrations)
    archive.capture_bytes(
        json.dumps(payload).encode("utf-8"),
        source_code=_SOURCE_CODE,
        endpoint_code="report_encounters_api",
        request_key=request_key_from_url("GET", url),
        http_status=200,
        content_type="application/json",
        request_url=url,
        metadata={"capture_mode": "test"},
    )


def test_archived_catalog_is_reused_without_network(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[2]
    raw_root = tmp_path / "raw"
    database = tmp_path / "coa.duckdb"
    _capture(
        raw_root=raw_root,
        database=database,
        migrations=root / "migrations",
        payload=_payload(),
    )

    evidence = load_archived_report_encounter_catalog(
        raw_root,
        database,
        reference=_reference(),
        source_code=_SOURCE_CODE,
        base_url=_BASE_URL,
    )
    assert evidence is not None
    assert evidence.matching_observation_count == 1

    correlation = correlate_report_encounter_catalog_payload(
        evidence.payload,
        reference=_reference(),
        expected_boss_name="Example Boss",
        expected_difficulty="ascended",
        source_kind="archived_first_party_encounter_catalog",
    )
    assert correlation.complete is True
    assert correlation.source_kind == "archived_first_party_encounter_catalog"


def test_archived_catalog_conflict_fails_closed(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[2]
    raw_root = tmp_path / "raw"
    database = tmp_path / "coa.duckdb"
    for difficulty in ("ascended", "heroic"):
        _capture(
            raw_root=raw_root,
            database=database,
            migrations=root / "migrations",
            payload=_payload(difficulty=difficulty),
        )

    with pytest.raises(ValueError, match="archived report encounter catalog observations disagree"):
        load_archived_report_encounter_catalog(
            raw_root,
            database,
            reference=_reference(),
            source_code=_SOURCE_CODE,
            base_url=_BASE_URL,
        )
