from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from coa_workbench.analytics.public_api_encounter_comparator import (
    EncounterLocationComparator,
    LocationComparatorStatus,
)
from coa_workbench.analytics.public_api_encounter_context import EncounterContextStatus
from coa_workbench.analytics.report_encounter_source_correlation import (
    ReportEncounterSourceCorrelation,
)

REPORT_ENCOUNTER_POPULATION_BINDING_VERSION = "report-encounter-population-binding-v1"


@dataclass(frozen=True, slots=True)
class ReportEncounterPopulationBinding:
    source_correlation_complete: bool
    encounter_context_complete: bool
    location_comparator_complete: bool
    differential_built: bool
    exact_dimension_match_verified: bool
    temporal_scope_match_verified: bool
    same_private_scope_inputs_reused: bool
    report_catalog_source_kind: str
    encounter_context_slice_count: int
    location_comparator_slice_count: int
    matched_record_count: int
    encounter_only_record_count: int
    location_only_record_count: int

    @property
    def complete(self) -> bool:
        return all(
            (
                self.source_correlation_complete,
                self.encounter_context_complete,
                self.location_comparator_complete,
                self.differential_built,
                self.exact_dimension_match_verified,
                self.temporal_scope_match_verified,
                self.same_private_scope_inputs_reused,
            )
        )

    def public_summary(self) -> dict[str, Any]:
        return {
            "binding_version": REPORT_ENCOUNTER_POPULATION_BINDING_VERSION,
            "source_correlation_complete": self.source_correlation_complete,
            "encounter_context_complete": self.encounter_context_complete,
            "location_comparator_complete": self.location_comparator_complete,
            "differential_built": self.differential_built,
            "exact_dimension_match_verified": self.exact_dimension_match_verified,
            "temporal_scope_match_verified": self.temporal_scope_match_verified,
            "same_private_scope_inputs_reused": self.same_private_scope_inputs_reused,
            "machine_correlated_encounter_population_binding_complete": self.complete,
            "report_catalog_source_kind": self.report_catalog_source_kind,
            "encounter_context_slice_count": self.encounter_context_slice_count,
            "location_comparator_slice_count": self.location_comparator_slice_count,
            "matched_record_count": self.matched_record_count,
            "encounter_only_record_count": self.encounter_only_record_count,
            "location_only_record_count": self.location_only_record_count,
            "report_ids_included": False,
            "encounter_ids_included": False,
            "boss_names_included": False,
            "boss_ids_included": False,
            "location_values_included": False,
            "difficulty_values_included": False,
            "phase_values_included": False,
            "query_values_included": False,
            "class_names_included": False,
            "spec_names_included": False,
            "metric_scalar_values_included": False,
            "parse_share_values_included": False,
            "raw_ids_included": False,
            "raw_paths_included": False,
            "source_structure_fingerprints_included": False,
            "player_identity_verified": False,
            "mechanic_semantics_verified": False,
            "site_tier_list_algorithm_verified": False,
            "planner_scoring_allowed": False,
            "public_release_safe": True,
        }


def build_report_encounter_population_binding(
    *,
    source_correlation: ReportEncounterSourceCorrelation,
    encounter_context: EncounterContextStatus,
    location_comparator: LocationComparatorStatus,
    differential: EncounterLocationComparator | None,
    same_private_scope_inputs_reused: bool,
) -> ReportEncounterPopulationBinding:
    """Bind independently proven encounter identity to existing population context.

    The caller must compute every input in one local execution from the same private
    report/encounter/boss/location/difficulty arguments. This function intentionally cannot infer
    scope equivalence from scalar-safe public receipts because those values are redacted.
    """
    differential_built = differential is not None
    exact_dimension_match_verified = differential_built
    temporal_scope_match_verified = differential_built
    return ReportEncounterPopulationBinding(
        source_correlation_complete=source_correlation.complete,
        encounter_context_complete=encounter_context.complete,
        location_comparator_complete=location_comparator.complete,
        differential_built=differential_built,
        exact_dimension_match_verified=exact_dimension_match_verified,
        temporal_scope_match_verified=temporal_scope_match_verified,
        same_private_scope_inputs_reused=same_private_scope_inputs_reused,
        report_catalog_source_kind=source_correlation.source_kind,
        encounter_context_slice_count=len(encounter_context.covered_slice_indexes),
        location_comparator_slice_count=len(location_comparator.covered_slice_indexes),
        matched_record_count=differential.matched_record_count if differential is not None else 0,
        encounter_only_record_count=(
            differential.encounter_only_record_count if differential is not None else 0
        ),
        location_only_record_count=(
            differential.location_only_record_count if differential is not None else 0
        ),
    )


__all__ = [
    "REPORT_ENCOUNTER_POPULATION_BINDING_VERSION",
    "ReportEncounterPopulationBinding",
    "build_report_encounter_population_binding",
]
