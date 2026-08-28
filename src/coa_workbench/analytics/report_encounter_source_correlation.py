from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from coa_workbench.analytics.public_api_encounter_context import EncounterReference
from coa_workbench.collector.compatible_normalization import (
    COMPATIBLE_NORMALIZATION_VERSION,
    normalize_verified_compatible_payload,
)

REPORT_ENCOUNTER_SOURCE_CORRELATION_VERSION = "report-encounter-source-correlation-v1"
_EXPECTED_MAPPING_ID = "coa-encounter-detail-v1"
_EXPECTED_ROUTE_TEMPLATE = "/api/reports/{template}/encounters/{template}"


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
    mapping_id: str
    mapping_version: str

    @property
    def complete(self) -> bool:
        return self.boss_source_correlated and self.difficulty_source_correlated

    def public_summary(self) -> dict[str, Any]:
        return {
            "correlation_version": REPORT_ENCOUNTER_SOURCE_CORRELATION_VERSION,
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
            "source_kind": "persisted_first_party_encounter_detail",
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


def correlate_report_encounter_payload(
    payload: Any,
    mapping_payload: Mapping[str, Any],
    *,
    reference: EncounterReference,
    expected_boss_name: str,
    expected_difficulty: str,
) -> ReportEncounterSourceCorrelation:
    """Correlate one reviewed report encounter against verified first-party parser fields.

    The expected boss/difficulty values are operator-selected private inputs. They are compared
    against the independently fetched encounter-detail source record and never copied into the
    public summary. Parser compatibility fails closed when a promoted field is absent or changes
    type. Exact report/encounter identity is required before either correlation can pass.
    """
    if mapping_payload.get("mapping_id") != _EXPECTED_MAPPING_ID:
        raise ValueError(f"expected verified mapping {_EXPECTED_MAPPING_ID}")
    if mapping_payload.get("route_template") != _EXPECTED_ROUTE_TEMPLATE:
        raise ValueError("encounter-detail mapping route template is not the reviewed route")
    if mapping_payload.get("status") != "verified":
        raise ValueError("encounter-detail mapping must be verified")
    if not expected_boss_name.strip():
        raise ValueError("expected boss name must be non-empty")
    if not expected_difficulty.strip():
        raise ValueError("expected difficulty must be non-empty")

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
        boss_name_matches = isinstance(row.get("name"), str) and row["name"] == expected_boss_name
        difficulty_matches = (
            isinstance(row.get("difficulty"), str)
            and row["difficulty"] == expected_difficulty
        )
        boss_flag_verified = row.get("is_boss_encounter") is True

    boss_source_correlated = exact_identity and boss_flag_verified and boss_name_matches
    difficulty_source_correlated = exact_identity and difficulty_matches

    return ReportEncounterSourceCorrelation(
        exact_reference_identity_verified=exact_identity,
        boss_name_field_verified=boss_name_matches,
        difficulty_field_verified=difficulty_matches,
        boss_source_correlated=boss_source_correlated,
        difficulty_source_correlated=difficulty_source_correlated,
        boss_encounter_flag_verified=boss_flag_verified,
        normalized_encounter_count=encounter_count,
        reject_count=reject_count,
        verified_field_contract_count=normalized.verified_field_contract_count,
        mapping_id=batch.mapping_id,
        mapping_version=batch.mapping_version,
    )


__all__ = [
    "REPORT_ENCOUNTER_SOURCE_CORRELATION_VERSION",
    "ReportEncounterSourceCorrelation",
    "correlate_report_encounter_payload",
]
