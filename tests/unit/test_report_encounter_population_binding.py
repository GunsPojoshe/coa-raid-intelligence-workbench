from __future__ import annotations

from coa_workbench.analytics.public_api_encounter_comparator import (
    EncounterLocationComparator,
    LocationComparatorStatus,
)
from coa_workbench.analytics.public_api_encounter_context import EncounterContextStatus
from coa_workbench.analytics.report_encounter_population_binding import (
    REPORT_ENCOUNTER_POPULATION_BINDING_VERSION,
    build_report_encounter_population_binding,
)
from coa_workbench.analytics.report_encounter_source_correlation import (
    ReportEncounterSourceCorrelation,
)


def _correlation(*, complete: bool = True) -> ReportEncounterSourceCorrelation:
    return ReportEncounterSourceCorrelation(
        exact_reference_identity_verified=complete,
        boss_name_field_verified=complete,
        difficulty_field_verified=complete,
        boss_source_correlated=complete,
        difficulty_source_correlated=complete,
        boss_encounter_flag_verified=complete,
        normalized_encounter_count=1,
        reject_count=0,
        verified_field_contract_count=5,
        source_kind="archived_first_party_encounter_catalog",
        parser_version="report-encounter-catalog-parser-v1",
    )


def _context(*, complete: bool = True) -> EncounterContextStatus:
    return EncounterContextStatus(
        required_slice_count=4,
        covered_slice_indexes=(0, 1, 2, 3) if complete else (0, 1, 2),
        missing_slice_indexes=() if complete else (3,),
        selected_batch_count=4 if complete else 3,
        aggregate_class_count=59,
        aggregate_spec_record_count=148,
        aggregate_percentile_value_count=1924,
    )


def _location(*, complete: bool = True) -> LocationComparatorStatus:
    return LocationComparatorStatus(
        required_slice_count=4,
        covered_slice_indexes=(0, 1, 2, 3) if complete else (0, 1, 2),
        missing_slice_indexes=() if complete else (3,),
        selected_batch_count=4 if complete else 3,
        aggregate_class_count=59,
        aggregate_spec_record_count=150,
        aggregate_percentile_value_count=1950,
    )


def _differential() -> EncounterLocationComparator:
    return EncounterLocationComparator(
        slice_count=4,
        matched_record_count=148,
        encounter_only_record_count=0,
        location_only_record_count=2,
        records=(),
    )


def test_complete_binding_is_scalar_safe_and_does_not_enable_planner() -> None:
    result = build_report_encounter_population_binding(
        source_correlation=_correlation(),
        encounter_context=_context(),
        location_comparator=_location(),
        differential=_differential(),
        same_private_scope_inputs_reused=True,
    )

    assert result.complete is True
    summary = result.public_summary()
    assert summary["binding_version"] == REPORT_ENCOUNTER_POPULATION_BINDING_VERSION
    assert summary["machine_correlated_encounter_population_binding_complete"] is True
    assert summary["same_private_scope_inputs_reused"] is True
    assert summary["matched_record_count"] == 148
    assert summary["location_only_record_count"] == 2
    assert summary["report_ids_included"] is False
    assert summary["encounter_ids_included"] is False
    assert summary["boss_names_included"] is False
    assert summary["difficulty_values_included"] is False
    assert summary["metric_scalar_values_included"] is False
    assert summary["player_identity_verified"] is False
    assert summary["mechanic_semantics_verified"] is False
    assert summary["planner_scoring_allowed"] is False
    assert summary["public_release_safe"] is True


def test_binding_fails_closed_when_private_scope_is_not_reused() -> None:
    result = build_report_encounter_population_binding(
        source_correlation=_correlation(),
        encounter_context=_context(),
        location_comparator=_location(),
        differential=_differential(),
        same_private_scope_inputs_reused=False,
    )
    assert result.complete is False


def test_binding_fails_closed_when_source_correlation_is_incomplete() -> None:
    result = build_report_encounter_population_binding(
        source_correlation=_correlation(complete=False),
        encounter_context=_context(),
        location_comparator=_location(),
        differential=_differential(),
        same_private_scope_inputs_reused=True,
    )
    assert result.complete is False


def test_binding_fails_closed_without_complete_population_context() -> None:
    result = build_report_encounter_population_binding(
        source_correlation=_correlation(),
        encounter_context=_context(complete=False),
        location_comparator=_location(),
        differential=None,
        same_private_scope_inputs_reused=True,
    )
    assert result.complete is False
    assert result.public_summary()["differential_built"] is False
