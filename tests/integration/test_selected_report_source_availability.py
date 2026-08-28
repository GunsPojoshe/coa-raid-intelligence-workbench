from __future__ import annotations

import json
from pathlib import Path

import pytest

from coa_workbench.analytics.public_api_encounter_context import EncounterReference
from coa_workbench.analytics.selected_report_source_availability import (
    SELECTED_REPORT_SOURCE_AVAILABILITY_VERSION,
    review_selected_report_source_availability,
)

_REPORT_ID = 123456


def _reference() -> EncounterReference:
    return EncounterReference(report_id=_REPORT_ID, encounter_id=654321)


def _create_database(database: Path) -> object:
    duckdb = pytest.importorskip("duckdb")
    connection = duckdb.connect(str(database))
    connection.execute(
        """
        CREATE TABLE raw_object (
            raw_id VARCHAR PRIMARY KEY,
            request_key VARCHAR NOT NULL,
            storage_path VARCHAR NOT NULL
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE raw_fetch_observation (
            observation_id VARCHAR PRIMARY KEY,
            raw_id VARCHAR NOT NULL,
            request_url_sanitized VARCHAR
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE source_capture (
            capture_id VARCHAR PRIMARY KEY,
            raw_observation_id VARCHAR NOT NULL,
            endpoint_code VARCHAR NOT NULL
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE source_acquisition_observation (
            acquisition_id VARCHAR PRIMARY KEY,
            source_capture_id VARCHAR,
            observed_at TIMESTAMP NOT NULL,
            outcome VARCHAR NOT NULL
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE canonical_entity_observation (
            observation_id VARCHAR PRIMARY KEY,
            entity_type VARCHAR NOT NULL,
            entity_key VARCHAR NOT NULL,
            entity_json VARCHAR NOT NULL,
            trust_status VARCHAR NOT NULL
        )
        """
    )
    return connection


def _write_raw(raw_root: Path, storage_path: str) -> None:
    path = raw_root / storage_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"archived")


def _insert_source(
    connection: object,
    raw_root: Path,
    *,
    key: str,
    request_url_sanitized: str | None,
    request_key: str,
    endpoint_code: str,
    write_payload: bool = True,
    outcome: str = "schema_candidate",
) -> None:
    raw_id = f"raw-{key}"
    observation_id = f"observation-{key}"
    capture_id = f"capture-{key}"
    storage_path = f"archive/{key}.json.gz"
    connection.execute(
        "INSERT INTO raw_object VALUES (?, ?, ?)",
        [raw_id, request_key, storage_path],
    )
    connection.execute(
        "INSERT INTO raw_fetch_observation VALUES (?, ?, ?)",
        [observation_id, raw_id, request_url_sanitized],
    )
    connection.execute(
        "INSERT INTO source_capture VALUES (?, ?, ?)",
        [capture_id, observation_id, endpoint_code],
    )
    connection.execute(
        "INSERT INTO source_acquisition_observation VALUES (?, ?, ?, ?)",
        [f"acquisition-{key}", capture_id, "2026-08-28 10:00:00", outcome],
    )
    if write_payload:
        _write_raw(raw_root, storage_path)


def _insert_complete_selected_report(connection: object, raw_root: Path) -> None:
    _insert_source(
        connection,
        raw_root,
        key="detail",
        request_url_sanitized=f"https://coa.ascensionlogs.gg/api/reports/{_REPORT_ID}",
        request_key=f"GET:/api/reports/{_REPORT_ID}#detail",
        endpoint_code="report_detail_api",
    )
    _insert_source(
        connection,
        raw_root,
        key="encounters",
        request_url_sanitized=(
            f"https://coa.ascensionlogs.gg/api/reports/{_REPORT_ID}/encounters"
            "?includeTrash=%3Credacted%3E"
        ),
        request_key=(
            f"GET:/api/reports/{_REPORT_ID}/encounters?keys=includeTrash#encounters"
        ),
        endpoint_code="report_encounters_api",
    )
    _insert_source(
        connection,
        raw_root,
        key="roster",
        request_url_sanitized=(
            f"https://coa.ascensionlogs.gg/api/reports/{_REPORT_ID}/combatants-roster"
            "?encounterIds=%3Credacted%3E"
        ),
        request_key=(
            f"GET:/api/reports/{_REPORT_ID}/combatants-roster?keys=encounterIds#roster"
        ),
        endpoint_code="report_combatants_roster_api",
    )


def test_complete_archived_source_set_is_offline_ready(tmp_path: Path) -> None:
    database = tmp_path / "coa.duckdb"
    raw_root = tmp_path / "raw"
    connection = _create_database(database)
    try:
        _insert_complete_selected_report(connection, raw_root)
    finally:
        connection.close()

    review = review_selected_report_source_availability(
        database,
        raw_root=raw_root,
        reference=_reference(),
    )

    assert review.required_source_family_count == 3
    assert review.archived_required_source_family_count == 3
    assert review.observatory_ready_required_source_family_count == 3
    assert review.missing_required_source_family_count == 0
    assert review.offline_source_reuse_candidate is True
    assert review.offline_source_observatory_reuse_ready is True
    assert review.offline_current_report_runtime_reconstruction_possible is True
    assert review.selected_report_current_runtime_persisted is False
    assert all(family.archived_payload_available for family in review.families)
    assert all(family.source_observatory_ready for family in review.families)


def test_other_report_does_not_satisfy_selected_report_scope(tmp_path: Path) -> None:
    database = tmp_path / "coa.duckdb"
    raw_root = tmp_path / "raw"
    connection = _create_database(database)
    try:
        other_report = 999999
        _insert_source(
            connection,
            raw_root,
            key="other-detail",
            request_url_sanitized=f"https://coa.ascensionlogs.gg/api/reports/{other_report}",
            request_key=f"GET:/api/reports/{other_report}#detail",
            endpoint_code="report_detail_api",
        )
    finally:
        connection.close()

    review = review_selected_report_source_availability(
        database,
        raw_root=raw_root,
        reference=_reference(),
    )

    assert review.archived_required_source_family_count == 0
    assert review.observatory_ready_required_source_family_count == 0
    assert review.missing_required_source_family_count == 3
    assert review.offline_source_reuse_candidate is False


def test_wrong_query_shape_does_not_promote_roster_source(tmp_path: Path) -> None:
    database = tmp_path / "coa.duckdb"
    raw_root = tmp_path / "raw"
    connection = _create_database(database)
    try:
        _insert_source(
            connection,
            raw_root,
            key="roster-wrong-query",
            request_url_sanitized=(
                f"https://coa.ascensionlogs.gg/api/reports/{_REPORT_ID}/combatants-roster"
            ),
            request_key=f"GET:/api/reports/{_REPORT_ID}/combatants-roster#roster",
            endpoint_code="report_combatants_roster_api",
        )
    finally:
        connection.close()

    review = review_selected_report_source_availability(
        database,
        raw_root=raw_root,
        reference=_reference(),
    )
    roster = next(
        family for family in review.families if family.endpoint_code == "report_combatants_roster_api"
    )

    assert roster.raw_observation_count == 1
    assert roster.reviewed_query_keys_match_count == 0
    assert roster.archived_payload_available is False
    assert roster.source_observatory_ready is False


def test_legacy_missing_sanitized_url_uses_request_key_scope(tmp_path: Path) -> None:
    database = tmp_path / "coa.duckdb"
    raw_root = tmp_path / "raw"
    connection = _create_database(database)
    try:
        _insert_source(
            connection,
            raw_root,
            key="legacy-roster",
            request_url_sanitized=None,
            request_key=(
                f"GET:/api/reports/{_REPORT_ID}/combatants-roster?keys=encounterIds#legacy"
            ),
            endpoint_code="report_combatants_roster_api",
        )
    finally:
        connection.close()

    review = review_selected_report_source_availability(
        database,
        raw_root=raw_root,
        reference=_reference(),
    )
    roster = next(
        family for family in review.families if family.endpoint_code == "report_combatants_roster_api"
    )

    assert roster.reviewed_query_keys_match_count == 1
    assert roster.archived_payload_available is True
    assert roster.source_observatory_ready is True


def test_selected_runtime_identity_is_detected_without_public_identity_leak(tmp_path: Path) -> None:
    database = tmp_path / "coa.duckdb"
    raw_root = tmp_path / "raw"
    connection = _create_database(database)
    try:
        connection.execute(
            "INSERT INTO canonical_entity_observation VALUES (?, ?, ?, ?, ?)",
            [
                "report-observation",
                "current_report_observation",
                "canonical-report",
                json.dumps({"source_report_id": _REPORT_ID}),
                "observed",
            ],
        )
    finally:
        connection.close()

    review = review_selected_report_source_availability(
        database,
        raw_root=raw_root,
        reference=_reference(),
    )
    summary = review.public_summary()
    serialized = json.dumps(summary, sort_keys=True)

    assert review.selected_report_current_runtime_persisted is True
    assert summary["review_version"] == SELECTED_REPORT_SOURCE_AVAILABILITY_VERSION
    assert summary["report_ids_included"] is False
    assert summary["request_urls_included"] is False
    assert summary["query_values_included"] is False
    assert summary["raw_ids_included"] is False
    assert summary["raw_paths_included"] is False
    assert summary["public_release_safe"] is True
    assert str(_REPORT_ID) not in serialized
    assert "coa.ascensionlogs.gg" not in serialized
    assert "archive/" not in serialized
