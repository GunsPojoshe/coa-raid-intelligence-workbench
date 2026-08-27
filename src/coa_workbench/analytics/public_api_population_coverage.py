from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from coa_workbench.normalizer.public_api_statistics import (
    PUBLIC_API_STATISTICS_NORMALIZER_VERSION,
)
from coa_workbench.storage.migrations import apply_migrations

PUBLIC_API_POPULATION_COVERAGE_VERSION = "public-api-population-coverage-v1"
_ENDPOINT_CODE = "public_api_statistics"


@dataclass(frozen=True, slots=True)
class PopulationCoverageSlice:
    difficulty: str
    metric: str
    bracket: str
    damage_mode: str
    role: str | None

    def query(self, *, phase: int) -> dict[str, object]:
        query: dict[str, object] = {
            "phase": phase,
            "difficulty": self.difficulty,
            "metric": self.metric,
            "bracket": self.bracket,
            "damageMode": self.damage_mode,
        }
        if self.role is not None:
            query["role"] = self.role
        return query


# Deliberately bounded. V1 varies only the documented metric/role profile while holding the
# remaining population scope broad and stable. Boss/location/week/realm/class/spec expansion is a
# later evidence gate, not a cartesian-product capture target.
PUBLIC_API_POPULATION_COVERAGE_V1 = (
    PopulationCoverageSlice(
        difficulty="all",
        metric="avg_dps",
        bracket="all",
        damage_mode="standard",
        role="dps",
    ),
    PopulationCoverageSlice(
        difficulty="all",
        metric="avg_dps",
        bracket="all",
        damage_mode="standard",
        role="support",
    ),
    PopulationCoverageSlice(
        difficulty="all",
        metric="avg_hps",
        bracket="all",
        damage_mode="standard",
        role=None,
    ),
    PopulationCoverageSlice(
        difficulty="all",
        metric="avg_dtps",
        bracket="all",
        damage_mode="standard",
        role="tank",
    ),
)


@dataclass(frozen=True, slots=True)
class PopulationCoverageStatus:
    phase: int
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
            "coverage_version": PUBLIC_API_POPULATION_COVERAGE_VERSION,
            "required_slice_count": self.required_slice_count,
            "covered_slice_count": len(self.covered_slice_indexes),
            "missing_slice_count": len(self.missing_slice_indexes),
            "selected_batch_count": self.selected_batch_count,
            "aggregate_class_count": self.aggregate_class_count,
            "aggregate_spec_record_count": self.aggregate_spec_record_count,
            "aggregate_percentile_value_count": self.aggregate_percentile_value_count,
            "metric_family_count": len({row.metric for row in PUBLIC_API_POPULATION_COVERAGE_V1}),
            "role_qualified_required_slice_count": sum(
                row.role is not None for row in PUBLIC_API_POPULATION_COVERAGE_V1
            ),
            "role_omitted_required_slice_count": sum(
                row.role is None for row in PUBLIC_API_POPULATION_COVERAGE_V1
            ),
            "complete": self.complete,
            "bounded_capture_plan": True,
            "bulk_dataset_mode": False,
            "phase_values_included": False,
            "difficulty_values_included": False,
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


def _matching_batch(
    connection: Any,
    *,
    phase: int,
    coverage_slice: PopulationCoverageSlice,
) -> tuple[str, int, int, int] | None:
    predicates = [
        "endpoint_code = ?",
        "normalizer_version = ?",
        "phase_number = ?",
        "difficulty = ?",
        "metric = ?",
        "bracket = ?",
        "damage_mode = ?",
        "location IS NULL",
        "boss_id IS NULL",
        "class_filter IS NULL",
        "spec_filter IS NULL",
        "week_number IS NULL",
        "realm IS NULL",
    ]
    parameters: list[Any] = [
        _ENDPOINT_CODE,
        PUBLIC_API_STATISTICS_NORMALIZER_VERSION,
        phase,
        coverage_slice.difficulty,
        coverage_slice.metric,
        coverage_slice.bracket,
        coverage_slice.damage_mode,
    ]
    if coverage_slice.role is None:
        predicates.append("role IS NULL")
    else:
        predicates.append("role = ?")
        parameters.append(coverage_slice.role)

    row = connection.execute(
        f"""
        SELECT batch_id, class_count, spec_record_count, percentile_value_count
        FROM public_api_statistics_batch
        WHERE {' AND '.join(predicates)}
        ORDER BY created_at DESC, batch_id DESC
        LIMIT 1
        """,
        parameters,
    ).fetchone()
    if row is None:
        return None
    return str(row[0]), int(row[1]), int(row[2]), int(row[3])


def review_public_api_population_coverage(
    database_path: Path,
    migrations_path: Path,
    *,
    phase: int,
) -> PopulationCoverageStatus:
    """Review bounded current-phase aggregate coverage without emitting private dimension values."""
    if isinstance(phase, bool) or not isinstance(phase, int) or phase < 1:
        raise ValueError("phase must be a positive integer")
    apply_migrations(database_path, migrations_path)

    import duckdb

    covered: list[int] = []
    missing: list[int] = []
    selected_batch_ids: set[str] = set()
    aggregate_class_count = 0
    aggregate_spec_record_count = 0
    aggregate_percentile_value_count = 0

    with duckdb.connect(str(database_path), read_only=True) as connection:
        for index, coverage_slice in enumerate(PUBLIC_API_POPULATION_COVERAGE_V1):
            matched = _matching_batch(
                connection,
                phase=phase,
                coverage_slice=coverage_slice,
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

    return PopulationCoverageStatus(
        phase=phase,
        required_slice_count=len(PUBLIC_API_POPULATION_COVERAGE_V1),
        covered_slice_indexes=tuple(covered),
        missing_slice_indexes=tuple(missing),
        selected_batch_count=len(selected_batch_ids),
        aggregate_class_count=aggregate_class_count,
        aggregate_spec_record_count=aggregate_spec_record_count,
        aggregate_percentile_value_count=aggregate_percentile_value_count,
    )


__all__ = [
    "PUBLIC_API_POPULATION_COVERAGE_V1",
    "PUBLIC_API_POPULATION_COVERAGE_VERSION",
    "PopulationCoverageSlice",
    "PopulationCoverageStatus",
    "review_public_api_population_coverage",
]
