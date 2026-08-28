from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import parse_qs, urlparse

from coa_workbench.normalizer.public_api_statistics import (
    PUBLIC_API_STATISTICS_NORMALIZER_VERSION,
)
from coa_workbench.storage.migrations import apply_migrations

PUBLIC_API_ENCOUNTER_CONTEXT_VERSION = "public-api-encounter-context-v1"
_ENDPOINT_CODE = "public_api_statistics"
_ARTIFACT_TYPE = "public_api_population_statistics"
_ANALYSIS_TYPE = "official_public_api_population_statistics"
_ALLOWED_DIFFICULTIES = frozenset({"normal", "heroic", "mythic", "ascended"})


@dataclass(frozen=True, slots=True)
class EncounterReference:
    report_id: int
    encounter_id: int


@dataclass(frozen=True, slots=True)
class EncounterContextSlice:
    metric: str
    role: str | None

    def query(
        self,
        *,
        phase: int,
        difficulty: str,
        location: str,
        boss_id: int,
    ) -> dict[str, object]:
        query: dict[str, object] = {
            "phase": phase,
            "difficulty": difficulty,
            "metric": self.metric,
            "bracket": "all",
            "location": location,
            "bossId": boss_id,
            "damageMode": "standard",
        }
        if self.role is not None:
            query["role"] = self.role
        return query


PUBLIC_API_ENCOUNTER_CONTEXT_V1 = (
    EncounterContextSlice(metric="avg_dps", role="dps"),
    EncounterContextSlice(metric="avg_dps", role="support"),
    EncounterContextSlice(metric="avg_hps", role=None),
    EncounterContextSlice(metric="avg_dtps", role="tank"),
)


@dataclass(frozen=True, slots=True)
class EncounterContextStatus:
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
            "context_version": PUBLIC_API_ENCOUNTER_CONTEXT_VERSION,
            "required_slice_count": self.required_slice_count,
            "covered_slice_count": len(self.covered_slice_indexes),
            "missing_slice_count": len(self.missing_slice_indexes),
            "selected_batch_count": self.selected_batch_count,
            "aggregate_class_count": self.aggregate_class_count,
            "aggregate_spec_record_count": self.aggregate_spec_record_count,
            "aggregate_percentile_value_count": self.aggregate_percentile_value_count,
            "metric_family_count": len({row.metric for row in PUBLIC_API_ENCOUNTER_CONTEXT_V1}),
            "role_qualified_required_slice_count": sum(
                row.role is not None for row in PUBLIC_API_ENCOUNTER_CONTEXT_V1
            ),
            "role_omitted_required_slice_count": sum(
                row.role is None for row in PUBLIC_API_ENCOUNTER_CONTEXT_V1
            ),
            "complete": self.complete,
            "encounter_scoped": True,
            "bounded_capture_plan": True,
            "bulk_dataset_mode": False,
            "provenance_complete_batches_required": True,
            "phase_values_included": False,
            "difficulty_values_included": False,
            "location_values_included": False,
            "boss_ids_included": False,
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


def parse_encounter_reference_url(value: str) -> EncounterReference:
    parsed = urlparse(value)
    if parsed.scheme != "https" or parsed.hostname != "coa.ascensionlogs.gg":
        raise ValueError("encounter reference must use https://coa.ascensionlogs.gg")
    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) != 3 or parts[0] != "reports" or parts[2] != "encounters":
        raise ValueError("encounter reference path must be /reports/{reportId}/encounters")
    if not parts[1].isdigit() or int(parts[1]) < 1:
        raise ValueError("encounter reference report id must be a positive integer")
    values = parse_qs(parsed.query, keep_blank_values=True).get("encounters", [])
    if len(values) != 1 or not values[0].isdigit() or int(values[0]) < 1:
        raise ValueError("encounter reference must contain one positive encounters query value")
    return EncounterReference(report_id=int(parts[1]), encounter_id=int(values[0]))


def resolve_public_api_boss_id(
    payload: Mapping[str, Any],
    *,
    boss_name: str,
    location: str,
) -> int:
    if payload.get("success") is not True:
        raise ValueError("public API bosses response was not successful")
    bosses = payload.get("bosses")
    if not isinstance(bosses, list):
        raise ValueError("public API bosses response must contain a bosses array")
    if not boss_name.strip() or not location.strip():
        raise ValueError("boss name and location must be non-empty")

    matches: list[int] = []
    for index, raw_boss in enumerate(bosses):
        if not isinstance(raw_boss, dict):
            raise ValueError(f"bosses[{index}] must be an object")
        raw_id = raw_boss.get("boss_id")
        raw_name = raw_boss.get("name")
        raw_location = raw_boss.get("location")
        if isinstance(raw_id, bool) or not isinstance(raw_id, int):
            raise ValueError(f"bosses[{index}].boss_id must be an integer")
        if not isinstance(raw_name, str) or not raw_name:
            raise ValueError(f"bosses[{index}].name must be a non-empty string")
        if raw_location is not None and not isinstance(raw_location, str):
            raise ValueError(f"bosses[{index}].location must be a string or null")
        if raw_name == boss_name and raw_location == location:
            matches.append(raw_id)

    if len(matches) != 1:
        raise ValueError(
            "encounter boss binding requires exactly one exact boss-name + location match; "
            f"found {len(matches)}"
        )
    return matches[0]


def _matching_batch(
    connection: Any,
    *,
    phase: int,
    difficulty: str,
    location: str,
    boss_id: int,
    context_slice: EncounterContextSlice,
) -> tuple[str, int, int, int] | None:
    predicates = [
        "batch.endpoint_code = ?",
        "batch.normalizer_version = ?",
        "batch.phase_number = ?",
        "batch.difficulty = ?",
        "batch.metric = ?",
        "batch.bracket = 'all'",
        "batch.location = ?",
        "batch.boss_id = ?",
        "batch.damage_mode = 'standard'",
        "batch.class_filter IS NULL",
        "batch.spec_filter IS NULL",
        "batch.week_number IS NULL",
        "batch.realm IS NULL",
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
    ]
    parameters: list[Any] = [
        _ENDPOINT_CODE,
        PUBLIC_API_STATISTICS_NORMALIZER_VERSION,
        phase,
        difficulty,
        context_slice.metric,
        location,
        boss_id,
        _ARTIFACT_TYPE,
        _ARTIFACT_TYPE,
        _ENDPOINT_CODE,
        _ARTIFACT_TYPE,
        _ANALYSIS_TYPE,
    ]
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


def review_public_api_encounter_context(
    database_path: Path,
    migrations_path: Path,
    *,
    phase: int,
    difficulty: str,
    location: str,
    boss_id: int,
) -> EncounterContextStatus:
    if isinstance(phase, bool) or not isinstance(phase, int) or phase < 1:
        raise ValueError("phase must be a positive integer")
    if difficulty not in _ALLOWED_DIFFICULTIES:
        raise ValueError("difficulty must be one concrete documented difficulty")
    if not location:
        raise ValueError("location must be non-empty")
    if isinstance(boss_id, bool) or not isinstance(boss_id, int):
        raise ValueError("boss_id must be an integer")

    apply_migrations(database_path, migrations_path)
    import duckdb

    covered: list[int] = []
    missing: list[int] = []
    selected_batch_ids: set[str] = set()
    aggregate_class_count = 0
    aggregate_spec_record_count = 0
    aggregate_percentile_value_count = 0

    with duckdb.connect(str(database_path), read_only=True) as connection:
        for index, context_slice in enumerate(PUBLIC_API_ENCOUNTER_CONTEXT_V1):
            matched = _matching_batch(
                connection,
                phase=phase,
                difficulty=difficulty,
                location=location,
                boss_id=boss_id,
                context_slice=context_slice,
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

    return EncounterContextStatus(
        required_slice_count=len(PUBLIC_API_ENCOUNTER_CONTEXT_V1),
        covered_slice_indexes=tuple(covered),
        missing_slice_indexes=tuple(missing),
        selected_batch_count=len(selected_batch_ids),
        aggregate_class_count=aggregate_class_count,
        aggregate_spec_record_count=aggregate_spec_record_count,
        aggregate_percentile_value_count=aggregate_percentile_value_count,
    )


__all__ = [
    "PUBLIC_API_ENCOUNTER_CONTEXT_V1",
    "PUBLIC_API_ENCOUNTER_CONTEXT_VERSION",
    "EncounterContextSlice",
    "EncounterContextStatus",
    "EncounterReference",
    "parse_encounter_reference_url",
    "resolve_public_api_boss_id",
    "review_public_api_encounter_context",
]
