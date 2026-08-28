from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from coa_workbench.analytics.public_api_encounter_context import (
    PUBLIC_API_ENCOUNTER_CONTEXT_V1,
    EncounterContextSlice,
)
from coa_workbench.analytics.public_api_population_priors import (
    PopulationPriorSnapshot,
    read_public_api_population_priors,
)
from coa_workbench.normalizer.public_api_statistics import (
    PUBLIC_API_STATISTICS_NORMALIZER_VERSION,
)
from coa_workbench.storage.migrations import apply_migrations

PUBLIC_API_ENCOUNTER_COMPARATOR_VERSION = "public-api-encounter-location-comparator-v1"
_ENDPOINT_CODE = "public_api_statistics"
_ARTIFACT_TYPE = "public_api_population_statistics"
_ANALYSIS_TYPE = "official_public_api_population_statistics"
_ALLOWED_DIFFICULTIES = frozenset({"normal", "heroic", "mythic", "ascended"})


@dataclass(frozen=True, slots=True)
class LocationComparatorSlice:
    metric: str
    role: str | None

    def query(
        self,
        *,
        phase: int,
        difficulty: str,
        location: str,
    ) -> dict[str, object]:
        query: dict[str, object] = {
            "phase": phase,
            "difficulty": difficulty,
            "metric": self.metric,
            "bracket": "all",
            "location": location,
            "damageMode": "standard",
        }
        if self.role is not None:
            query["role"] = self.role
        return query


PUBLIC_API_LOCATION_COMPARATOR_V1 = tuple(
    LocationComparatorSlice(metric=row.metric, role=row.role)
    for row in PUBLIC_API_ENCOUNTER_CONTEXT_V1
)


@dataclass(frozen=True, slots=True)
class LocationComparatorStatus:
    required_slice_count: int
    covered_slice_indexes: tuple[int, ...]
    missing_slice_indexes: tuple[int, ...]
    selected_batch_count: int
    aggregate_class_count: int
    aggregate_spec_record_count: int
    aggregate_percentile_value_count: int

    @property
    def complete(self) -> bool:
        return not self.missing_slice_indexes

    def public_summary(self) -> dict[str, Any]:
        return {
            "comparator_version": PUBLIC_API_ENCOUNTER_COMPARATOR_VERSION,
            "required_slice_count": self.required_slice_count,
            "covered_slice_count": len(self.covered_slice_indexes),
            "missing_slice_count": len(self.missing_slice_indexes),
            "selected_batch_count": self.selected_batch_count,
            "aggregate_class_count": self.aggregate_class_count,
            "aggregate_spec_record_count": self.aggregate_spec_record_count,
            "aggregate_percentile_value_count": self.aggregate_percentile_value_count,
            "metric_family_count": len({row.metric for row in PUBLIC_API_LOCATION_COMPARATOR_V1}),
            "role_qualified_required_slice_count": sum(
                row.role is not None for row in PUBLIC_API_LOCATION_COMPARATOR_V1
            ),
            "role_omitted_required_slice_count": sum(
                row.role is None for row in PUBLIC_API_LOCATION_COMPARATOR_V1
            ),
            "complete": self.complete,
            "location_scoped": True,
            "boss_scope_omitted": True,
            "bounded_capture_plan": True,
            "bulk_dataset_mode": False,
            "provenance_complete_batches_required": True,
            "phase_values_included": False,
            "difficulty_values_included": False,
            "location_values_included": False,
            "metric_values_included": False,
            "role_values_included": False,
            "query_values_included": False,
            "batch_ids_included": False,
            "class_names_included": False,
            "spec_names_included": False,
            "metric_scalar_values_included": False,
            "planner_scoring_allowed": False,
            "public_release_safe": True,
        }


@dataclass(frozen=True, slots=True)
class EncounterLocationDeltaRecord:
    slice_index: int
    class_name: str
    spec_name: str
    encounter_total_parses: int
    location_total_parses: int
    encounter_parse_share: float | None
    location_parse_share: float | None
    parse_share_delta: float | None
    parse_share_ratio: float | None
    avg_delta: float
    avg_ratio: float | None
    median_delta: float
    median_ratio: float | None


@dataclass(frozen=True, slots=True)
class EncounterLocationComparator:
    slice_count: int
    matched_record_count: int
    encounter_only_record_count: int
    location_only_record_count: int
    records: tuple[EncounterLocationDeltaRecord, ...]

    def public_summary(self) -> dict[str, Any]:
        return {
            "comparator_version": PUBLIC_API_ENCOUNTER_COMPARATOR_VERSION,
            "slice_count": self.slice_count,
            "matched_record_count": self.matched_record_count,
            "encounter_only_record_count": self.encounter_only_record_count,
            "location_only_record_count": self.location_only_record_count,
            "records_with_parse_share_delta": sum(
                row.parse_share_delta is not None for row in self.records
            ),
            "records_with_parse_share_ratio": sum(
                row.parse_share_ratio is not None for row in self.records
            ),
            "records_with_avg_delta": len(self.records),
            "records_with_avg_ratio": sum(row.avg_ratio is not None for row in self.records),
            "records_with_median_delta": len(self.records),
            "records_with_median_ratio": sum(
                row.median_ratio is not None for row in self.records
            ),
            "exact_dimension_match_required": True,
            "temporal_scope_match_required": True,
            "missing_spec_treated_as_zero": False,
            "contains_class_names": False,
            "contains_spec_names": False,
            "contains_dimension_values": False,
            "contains_metric_scalar_values": False,
            "contains_parse_share_values": False,
            "site_tier_list_algorithm_verified": False,
            "mechanic_semantics_verified": False,
            "planner_scoring_allowed": False,
            "public_release_safe": True,
        }


def _provenance_predicates() -> tuple[str, ...]:
    return (
        """
        EXISTS (
            SELECT 1
            FROM artifact_dependency AS dep
            WHERE dep.artifact_type = ?
              AND dep.artifact_key = batch.batch_id
              AND dep.dependency_type = 'raw_object'
              AND dep.active = TRUE
        )
        """,
        """
        EXISTS (
            SELECT 1
            FROM artifact_dependency AS dep
            WHERE dep.artifact_type = ?
              AND dep.artifact_key = batch.batch_id
              AND dep.dependency_type = 'source_endpoint_profile'
              AND dep.dependency_key = ?
              AND dep.active = TRUE
        )
        """,
        """
        EXISTS (
            SELECT 1
            FROM analysis_run AS run
            WHERE run.artifact_type = ?
              AND run.artifact_key = batch.batch_id
              AND run.analysis_type = ?
              AND run.status = 'completed'
        )
        """,
    )


def _matching_batch(
    connection: Any,
    *,
    phase: int,
    difficulty: str,
    location: str,
    context_slice: EncounterContextSlice | LocationComparatorSlice,
    boss_id: int | None,
) -> tuple[str, int, int, int] | None:
    predicates = [
        "batch.endpoint_code = ?",
        "batch.normalizer_version = ?",
        "batch.phase_number = ?",
        "batch.difficulty = ?",
        "batch.metric = ?",
        "batch.bracket = 'all'",
        "batch.location = ?",
        "batch.damage_mode = 'standard'",
        "batch.class_filter IS NULL",
        "batch.spec_filter IS NULL",
        "batch.week_number IS NULL",
        "batch.realm IS NULL",
        *_provenance_predicates(),
    ]
    parameters: list[Any] = [
        _ENDPOINT_CODE,
        PUBLIC_API_STATISTICS_NORMALIZER_VERSION,
        phase,
        difficulty,
        context_slice.metric,
        location,
        _ARTIFACT_TYPE,
        _ARTIFACT_TYPE,
        _ENDPOINT_CODE,
        _ARTIFACT_TYPE,
        _ANALYSIS_TYPE,
    ]
    if boss_id is None:
        predicates.append("batch.boss_id IS NULL")
    else:
        predicates.append("batch.boss_id = ?")
        parameters.append(boss_id)
    if context_slice.role is None:
        predicates.append("batch.role IS NULL")
    else:
        predicates.append("batch.role = ?")
        parameters.append(context_slice.role)

    row = connection.execute(
        f"""
        SELECT
            batch.batch_id,
            batch.class_count,
            batch.spec_record_count,
            batch.percentile_value_count
        FROM public_api_statistics_batch AS batch
        WHERE {' AND '.join(predicates)}
        ORDER BY batch.created_at DESC, batch.batch_id DESC
        LIMIT 1
        """,
        parameters,
    ).fetchone()
    if row is None:
        return None
    return str(row[0]), int(row[1]), int(row[2]), int(row[3])


def _validate_scope(*, phase: int, difficulty: str, location: str, boss_id: int | None) -> None:
    if isinstance(phase, bool) or not isinstance(phase, int) or phase < 1:
        raise ValueError("phase must be a positive integer")
    if difficulty not in _ALLOWED_DIFFICULTIES:
        raise ValueError("difficulty must be one concrete documented difficulty")
    if not location:
        raise ValueError("location must be non-empty")
    if boss_id is not None and (isinstance(boss_id, bool) or not isinstance(boss_id, int)):
        raise ValueError("boss_id must be an integer when provided")


def review_public_api_location_comparator(
    database_path: Path,
    migrations_path: Path,
    *,
    phase: int,
    difficulty: str,
    location: str,
) -> LocationComparatorStatus:
    _validate_scope(phase=phase, difficulty=difficulty, location=location, boss_id=None)
    apply_migrations(database_path, migrations_path)
    import duckdb

    covered: list[int] = []
    missing: list[int] = []
    selected_batch_ids: set[str] = set()
    aggregate_class_count = 0
    aggregate_spec_record_count = 0
    aggregate_percentile_value_count = 0

    with duckdb.connect(str(database_path), read_only=True) as connection:
        for index, context_slice in enumerate(PUBLIC_API_LOCATION_COMPARATOR_V1):
            matched = _matching_batch(
                connection,
                phase=phase,
                difficulty=difficulty,
                location=location,
                context_slice=context_slice,
                boss_id=None,
            )
            if matched is None:
                missing.append(index)
                continue
            covered.append(index)
            batch_id, class_count, spec_count, percentile_count = matched
            selected_batch_ids.add(batch_id)
            aggregate_class_count += class_count
            aggregate_spec_record_count += spec_count
            aggregate_percentile_value_count += percentile_count

    return LocationComparatorStatus(
        required_slice_count=len(PUBLIC_API_LOCATION_COMPARATOR_V1),
        covered_slice_indexes=tuple(covered),
        missing_slice_indexes=tuple(missing),
        selected_batch_count=len(selected_batch_ids),
        aggregate_class_count=aggregate_class_count,
        aggregate_spec_record_count=aggregate_spec_record_count,
        aggregate_percentile_value_count=aggregate_percentile_value_count,
    )


def _snapshot_batch_ids(
    database_path: Path,
    *,
    phase: int,
    difficulty: str,
    location: str,
    boss_id: int,
) -> tuple[tuple[str, str], ...]:
    import duckdb

    pairs: list[tuple[str, str]] = []
    with duckdb.connect(str(database_path), read_only=True) as connection:
        for encounter_slice, location_slice in zip(
            PUBLIC_API_ENCOUNTER_CONTEXT_V1,
            PUBLIC_API_LOCATION_COMPARATOR_V1,
            strict=True,
        ):
            encounter_match = _matching_batch(
                connection,
                phase=phase,
                difficulty=difficulty,
                location=location,
                context_slice=encounter_slice,
                boss_id=boss_id,
            )
            location_match = _matching_batch(
                connection,
                phase=phase,
                difficulty=difficulty,
                location=location,
                context_slice=location_slice,
                boss_id=None,
            )
            if encounter_match is None or location_match is None:
                raise LookupError("encounter/location comparator requires all exact matching slices")
            pairs.append((encounter_match[0], location_match[0]))
    return tuple(pairs)


def _validate_pair(
    encounter: PopulationPriorSnapshot,
    location: PopulationPriorSnapshot,
    *,
    expected_boss_id: int,
) -> None:
    if encounter.boss_id != expected_boss_id:
        raise ValueError("encounter comparator batch does not match the expected boss id")
    if location.boss_id is not None:
        raise ValueError("location comparator batch must omit boss id")
    comparable = (
        "phase",
        "difficulty",
        "metric",
        "bracket",
        "location",
        "damage_mode",
        "role",
        "class_filter",
        "spec_filter",
        "week_number",
        "realm",
        "day_number",
    )
    mismatched = [name for name in comparable if getattr(encounter, name) != getattr(location, name)]
    if mismatched:
        raise ValueError(
            "encounter/location comparator dimensions do not match exactly: "
            + ", ".join(mismatched)
        )


def _ratio(numerator: float, denominator: float) -> float | None:
    if denominator == 0.0:
        return None
    return numerator / denominator


def build_public_api_encounter_location_comparator(
    database_path: Path,
    migrations_path: Path,
    *,
    phase: int,
    difficulty: str,
    location: str,
    boss_id: int,
) -> EncounterLocationComparator:
    _validate_scope(phase=phase, difficulty=difficulty, location=location, boss_id=boss_id)
    apply_migrations(database_path, migrations_path)
    pairs = _snapshot_batch_ids(
        database_path,
        phase=phase,
        difficulty=difficulty,
        location=location,
        boss_id=boss_id,
    )

    records: list[EncounterLocationDeltaRecord] = []
    encounter_only_count = 0
    location_only_count = 0

    for slice_index, (encounter_batch_id, location_batch_id) in enumerate(pairs):
        encounter = read_public_api_population_priors(database_path, batch_id=encounter_batch_id)
        comparator = read_public_api_population_priors(database_path, batch_id=location_batch_id)
        _validate_pair(encounter, comparator, expected_boss_id=boss_id)

        encounter_rows = {(row.class_name, row.spec_name): row for row in encounter.records}
        location_rows = {(row.class_name, row.spec_name): row for row in comparator.records}
        shared_keys = sorted(set(encounter_rows) & set(location_rows))
        encounter_only_count += len(set(encounter_rows) - set(location_rows))
        location_only_count += len(set(location_rows) - set(encounter_rows))

        for class_name, spec_name in shared_keys:
            encounter_row = encounter_rows[(class_name, spec_name)]
            location_row = location_rows[(class_name, spec_name)]
            parse_share_delta: float | None = None
            parse_share_ratio: float | None = None
            if (
                encounter_row.local_parse_share is not None
                and location_row.local_parse_share is not None
            ):
                parse_share_delta = (
                    encounter_row.local_parse_share - location_row.local_parse_share
                )
                parse_share_ratio = _ratio(
                    encounter_row.local_parse_share,
                    location_row.local_parse_share,
                )
            records.append(
                EncounterLocationDeltaRecord(
                    slice_index=slice_index,
                    class_name=class_name,
                    spec_name=spec_name,
                    encounter_total_parses=encounter_row.total_parses,
                    location_total_parses=location_row.total_parses,
                    encounter_parse_share=encounter_row.local_parse_share,
                    location_parse_share=location_row.local_parse_share,
                    parse_share_delta=parse_share_delta,
                    parse_share_ratio=parse_share_ratio,
                    avg_delta=encounter_row.avg - location_row.avg,
                    avg_ratio=_ratio(encounter_row.avg, location_row.avg),
                    median_delta=encounter_row.median - location_row.median,
                    median_ratio=_ratio(encounter_row.median, location_row.median),
                )
            )

    return EncounterLocationComparator(
        slice_count=len(pairs),
        matched_record_count=len(records),
        encounter_only_record_count=encounter_only_count,
        location_only_record_count=location_only_count,
        records=tuple(records),
    )


__all__ = [
    "PUBLIC_API_ENCOUNTER_COMPARATOR_VERSION",
    "PUBLIC_API_LOCATION_COMPARATOR_V1",
    "EncounterLocationComparator",
    "EncounterLocationDeltaRecord",
    "LocationComparatorSlice",
    "LocationComparatorStatus",
    "build_public_api_encounter_location_comparator",
    "review_public_api_location_comparator",
]
