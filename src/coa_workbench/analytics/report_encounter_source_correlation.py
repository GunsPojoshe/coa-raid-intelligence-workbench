from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from coa_workbench.analytics.public_api_encounter_context import EncounterReference
from coa_workbench.collector.compatible_normalization import (
    COMPATIBLE_NORMALIZATION_VERSION,
    normalize_verified_compatible_payload,
)

REPORT_ENCOUNTER_SOURCE_CORRELATION_VERSION = "report-encounter-source-correlation-v2"
REPORT_ENCOUNTER_CATALOG_PARSER_VERSION = "report-encounter-catalog-parser-v1"
_EXPECTED_MAPPING_ID = "coa-encounter-detail-v1"
_EXPECTED_ROUTE_TEMPLATE = "/api/reports/{template}/encounters/{template}"


@dataclass(frozen=True, slots=True)
class PersistedEncounterCatalogEvidence:
    payload: dict[str, Any]
    matching_observation_count: int


@dataclass(frozen=True, slots=True)
class ReportEncounterSourceCorrelation:
    exact_reference_identity_verified: bool
    boss_name_field_verified: bool
    difficulty_field_verified: bool
    boss_source_correlated: bool
    difficulty_source_correlated: bool
    boss_encounter_flag_verified: bool
    normalized_encounter_count: int
    reject_count: int
    verified_field_contract_count: int
    source_kind: str
    parser_version: str
    mapping_id: str | None = None
    mapping_version: str | None = None

    @property
    def complete(self) -> bool:
        return self.boss_source_correlated and self.difficulty_source_correlated

    def public_summary(self) -> dict[str, Any]:
        return {
            "correlation_version": REPORT_ENCOUNTER_SOURCE_CORRELATION_VERSION,
            "source_kind": self.source_kind,
            "parser_version": self.parser_version,
            "mapping_id": self.mapping_id,
            "mapping_version": self.mapping_version,
            "compatible_normalization_version": COMPATIBLE_NORMALIZATION_VERSION,
            "normalized_encounter_count": self.normalized_encounter_count,
            "reject_count": self.reject_count,
            "verified_field_contract_count": self.verified_field_contract_count,
            "exact_reference_identity_verified": self.exact_reference_identity_verified,
            "boss_name_field_verified": self.boss_name_field_verified,
            "difficulty_field_verified": self.difficulty_field_verified,
            "boss_encounter_flag_verified": self.boss_encounter_flag_verified,
            "report_encounter_boss_source_correlated": self.boss_source_correlated,
            "report_encounter_difficulty_source_correlated": self.difficulty_source_correlated,
            "complete": self.complete,
            "route_template_included": False,
            "report_ids_included": False,
            "encounter_ids_included": False,
            "boss_names_included": False,
            "difficulty_values_included": False,
            "location_values_included": False,
            "boss_ids_included": False,
            "creature_ids_included": False,
            "source_scalar_values_included": False,
            "source_structure_fingerprints_included": False,
            "raw_ids_included": False,
            "raw_paths_included": False,
            "query_values_included": False,
            "mechanic_semantics_verified": False,
            "planner_scoring_allowed": False,
            "public_release_safe": True,
        }


def _positive_integer(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{field} must be a positive integer")
    return value


def _required_nonempty_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value


def correlate_report_encounter_catalog_payload(
    payload: Any,
    *,
    reference: EncounterReference,
    expected_boss_name: str,
    expected_difficulty: str,
    source_kind: str = "live_first_party_encounter_catalog",
) -> ReportEncounterSourceCorrelation:
    """Correlate one report encounter through the reviewed current encounter catalog.

    The catalog is the small first-party response already observed by the current report UI. Only
    the selected row is promoted: report id, encounter id, name, difficulty and boss flag. Values
    remain private and the public result exposes booleans/counts only.
    """
    expected_name = _required_nonempty_string(expected_boss_name, "expected boss name")
    expected_mode = _required_nonempty_string(expected_difficulty, "expected difficulty")
    if not isinstance(payload, dict):
        raise ValueError("encounter catalog response must be an object")
    if payload.get("success") is not True:
        raise ValueError("encounter catalog response was not successful")

    report = payload.get("report")
    if not isinstance(report, dict):
        raise ValueError("encounter catalog response must contain a report object")
    source_report_id = _positive_integer(report.get("id"), "encounter catalog report.id")

    encounters = payload.get("encounters")
    if not isinstance(encounters, list):
        raise ValueError("encounter catalog response must contain an encounters array")

    matches: list[dict[str, Any]] = []
    for index, raw_row in enumerate(encounters):
        if not isinstance(raw_row, dict):
            raise ValueError(f"encounters[{index}] must be an object")
        row_id = _positive_integer(raw_row.get("id"), f"encounters[{index}].id")
        if row_id == reference.encounter_id:
            matches.append(raw_row)

    if len(matches) != 1:
        raise ValueError(
            "encounter catalog requires exactly one selected encounter row; "
            f"found {len(matches)}"
        )

    row = matches[0]
    row_name = _required_nonempty_string(row.get("name"), "selected encounter name")
    row_difficulty = _required_nonempty_string(
        row.get("difficulty"),
        "selected encounter difficulty",
    )
    boss_flag = row.get("is_boss_encounter")
    if not isinstance(boss_flag, bool):
        raise ValueError("selected encounter is_boss_encounter must be boolean")

    exact_identity = source_report_id == reference.report_id
    boss_name_matches = row_name == expected_name
    difficulty_matches = row_difficulty == expected_mode
    boss_flag_verified = boss_flag is True

    return ReportEncounterSourceCorrelation(
        exact_reference_identity_verified=exact_identity,
        boss_name_field_verified=boss_name_matches,
        difficulty_field_verified=difficulty_matches,
        boss_source_correlated=exact_identity and boss_flag_verified and boss_name_matches,
        difficulty_source_correlated=exact_identity and difficulty_matches,
        boss_encounter_flag_verified=boss_flag_verified,
        normalized_encounter_count=1,
        reject_count=0,
        verified_field_contract_count=5,
        source_kind=source_kind,
        parser_version=REPORT_ENCOUNTER_CATALOG_PARSER_VERSION,
    )


def load_persisted_report_encounter_catalog(
    database_path: Path,
    *,
    reference: EncounterReference,
) -> PersistedEncounterCatalogEvidence | None:
    """Resolve exact current-report catalog evidence already persisted in local DuckDB.

    The function reads only current encounter observations. If multiple observations exist, their
    selected catalog rows must be byte-for-byte equivalent as JSON or the lookup fails closed.
    """
    if not database_path.is_file():
        return None

    try:
        import duckdb
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("DuckDB is required to inspect persisted report evidence") from exc

    with duckdb.connect(str(database_path), read_only=True) as connection:
        tables = {str(row[0]) for row in connection.execute("SHOW TABLES").fetchall()}
        if "canonical_entity_observation" not in tables:
            return None
        rows = connection.execute(
            """
            SELECT entity_json
            FROM canonical_entity_observation
            WHERE entity_type = 'current_encounter_observation'
            """
        ).fetchall()

    matches: list[dict[str, Any]] = []
    for (raw_entity,) in rows:
        try:
            entity = json.loads(str(raw_entity))
        except json.JSONDecodeError as exc:
            raise ValueError("persisted current encounter observation is not valid JSON") from exc
        if not isinstance(entity, dict):
            raise ValueError("persisted current encounter observation must be an object")
        normalized = entity.get("normalized")
        catalog = entity.get("catalog_observation")
        if not isinstance(normalized, dict) or not isinstance(catalog, dict):
            continue
        source_report_id = normalized.get("source_report_id")
        source_encounter_id = normalized.get("source_encounter_id")
        if (
            isinstance(source_report_id, int)
            and not isinstance(source_report_id, bool)
            and source_report_id == reference.report_id
            and isinstance(source_encounter_id, int)
            and not isinstance(source_encounter_id, bool)
            and source_encounter_id == reference.encounter_id
        ):
            matches.append(catalog)

    if not matches:
        return None

    signatures = {
        json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        for row in matches
    }
    if len(signatures) != 1:
        raise ValueError("persisted report encounter catalog observations disagree")

    return PersistedEncounterCatalogEvidence(
        payload={
            "success": True,
            "report": {"id": reference.report_id},
            "encounters": [matches[0]],
        },
        matching_observation_count=len(matches),
    )


def correlate_report_encounter_payload(
    payload: Any,
    mapping_payload: Mapping[str, Any],
    *,
    reference: EncounterReference,
    expected_boss_name: str,
    expected_difficulty: str,
) -> ReportEncounterSourceCorrelation:
    """Retained v1 encounter-detail correlation for deterministic compatibility tests.

    The operator path no longer uses this heavier endpoint; current execution prefers persisted
    encounter-catalog evidence and otherwise fetches the small reviewed encounter catalog.
    """
    if mapping_payload.get("mapping_id") != _EXPECTED_MAPPING_ID:
        raise ValueError(f"expected verified mapping {_EXPECTED_MAPPING_ID}")
    if mapping_payload.get("route_template") != _EXPECTED_ROUTE_TEMPLATE:
        raise ValueError("encounter-detail mapping route template is not the reviewed route")
    if mapping_payload.get("status") != "verified":
        raise ValueError("encounter-detail mapping must be verified")
    expected_name = _required_nonempty_string(expected_boss_name, "expected boss name")
    expected_mode = _required_nonempty_string(expected_difficulty, "expected difficulty")

    normalized = normalize_verified_compatible_payload(payload, mapping_payload)
    batch = normalized.batch
    encounter_count = len(batch.encounters)
    reject_count = len(batch.rejects)

    exact_identity = False
    boss_name_matches = False
    difficulty_matches = False
    boss_flag_verified = False

    if encounter_count == 1 and reject_count == 0:
        row = batch.encounters[0]
        source_report_id = row.get("source_report_id")
        source_encounter_id = row.get("source_encounter_id")
        exact_identity = (
            isinstance(source_report_id, int)
            and not isinstance(source_report_id, bool)
            and source_report_id == reference.report_id
            and isinstance(source_encounter_id, int)
            and not isinstance(source_encounter_id, bool)
            and source_encounter_id == reference.encounter_id
        )
        boss_name_matches = isinstance(row.get("name"), str) and row["name"] == expected_name
        difficulty_matches = (
            isinstance(row.get("difficulty"), str) and row["difficulty"] == expected_mode
        )
        boss_flag_verified = row.get("is_boss_encounter") is True

    return ReportEncounterSourceCorrelation(
        exact_reference_identity_verified=exact_identity,
        boss_name_field_verified=boss_name_matches,
        difficulty_field_verified=difficulty_matches,
        boss_source_correlated=exact_identity and boss_flag_verified and boss_name_matches,
        difficulty_source_correlated=exact_identity and difficulty_matches,
        boss_encounter_flag_verified=boss_flag_verified,
        normalized_encounter_count=encounter_count,
        reject_count=reject_count,
        verified_field_contract_count=normalized.verified_field_contract_count,
        source_kind="legacy_first_party_encounter_detail",
        parser_version=COMPATIBLE_NORMALIZATION_VERSION,
        mapping_id=batch.mapping_id,
        mapping_version=batch.mapping_version,
    )


__all__ = [
    "REPORT_ENCOUNTER_CATALOG_PARSER_VERSION",
    "REPORT_ENCOUNTER_SOURCE_CORRELATION_VERSION",
    "PersistedEncounterCatalogEvidence",
    "ReportEncounterSourceCorrelation",
    "correlate_report_encounter_catalog_payload",
    "correlate_report_encounter_payload",
    "load_persisted_report_encounter_catalog",
]
