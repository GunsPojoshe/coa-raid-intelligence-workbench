from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class PopulationPriorRecord:
    class_name: str
    spec_name: str
    avg: float
    median: float
    maximum: float
    minimum: float
    total_parses: int
    percentiles: tuple[tuple[str, float], ...]
    local_parse_share: float | None


@dataclass(frozen=True, slots=True)
class PopulationPriorSnapshot:
    phase: int
    difficulty: str
    metric: str
    bracket: str | None
    location: str | None
    boss_id: int | None
    damage_mode: str | None
    role: str | None
    class_filter: str | None
    spec_filter: str | None
    week_number: int | None
    realm: str | None
    day_number: int | None
    records: tuple[PopulationPriorRecord, ...]


def _percentiles(value: str) -> tuple[tuple[str, float], ...]:
    raw = json.loads(value)
    if not isinstance(raw, dict):
        raise ValueError("persisted percentile payload must be an object")
    return tuple((str(key), float(raw[key])) for key in sorted(raw))


def read_public_api_population_priors(
    database_path: Path,
    *,
    batch_id: str | None = None,
    phase: int | None = None,
    difficulty: str | None = None,
    metric: str | None = None,
    bracket: str | None = None,
    location: str | None = None,
    boss_id: int | None = None,
    damage_mode: str | None = None,
    role: str | None = None,
    class_name: str | None = None,
    spec_name: str | None = None,
    week_number: int | None = None,
    realm: str | None = None,
) -> PopulationPriorSnapshot:
    """Read aggregate evidence without converting any source metric into planner score."""
    try:
        import duckdb
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("DuckDB is required for the population prior read model") from exc

    predicates: list[str] = []
    parameters: list[Any] = []
    filters = (
        ("batch_id", batch_id),
        ("phase_number", phase),
        ("difficulty", difficulty),
        ("metric", metric),
        ("bracket", bracket),
        ("location", location),
        ("boss_id", boss_id),
        ("damage_mode", damage_mode),
        ("role", role),
        ("week_number", week_number),
        ("realm", realm),
    )
    for column, value in filters:
        if value is not None:
            predicates.append(f"{column} = ?")
            parameters.append(value)
    where = f"WHERE {' AND '.join(predicates)}" if predicates else ""

    with duckdb.connect(str(database_path), read_only=True) as connection:
        batch_row = connection.execute(
            f"""
            SELECT
                batch_id, phase_number, difficulty, metric, bracket, location, boss_id,
                damage_mode, role, class_filter, spec_filter, week_number, realm, day_number
            FROM public_api_statistics_batch
            {where}
            ORDER BY created_at DESC, batch_id DESC
            LIMIT 1
            """,
            parameters,
        ).fetchone()
        if batch_row is None:
            raise LookupError("no persisted public API statistics batch matches the requested dimensions")

        selected_batch_id = str(batch_row[0])
        row_predicates = ["batch_id = ?"]
        row_parameters: list[Any] = [selected_batch_id]
        if class_name is not None:
            row_predicates.append("class_name = ?")
            row_parameters.append(class_name)
        if spec_name is not None:
            row_predicates.append("spec_name = ?")
            row_parameters.append(spec_name)
        rows = connection.execute(
            f"""
            SELECT
                class_name, spec_name, avg, median, max, min, total_parses,
                percentiles_json, local_parse_share
            FROM public_api_population_prior_v1
            WHERE {' AND '.join(row_predicates)}
            ORDER BY class_name, spec_name
            """,
            row_parameters,
        ).fetchall()

    records = tuple(
        PopulationPriorRecord(
            class_name=str(row[0]),
            spec_name=str(row[1]),
            avg=float(row[2]),
            median=float(row[3]),
            maximum=float(row[4]),
            minimum=float(row[5]),
            total_parses=int(row[6]),
            percentiles=_percentiles(str(row[7])),
            local_parse_share=float(row[8]) if row[8] is not None else None,
        )
        for row in rows
    )
    return PopulationPriorSnapshot(
        phase=int(batch_row[1]),
        difficulty=str(batch_row[2]),
        metric=str(batch_row[3]),
        bracket=str(batch_row[4]) if batch_row[4] is not None else None,
        location=str(batch_row[5]) if batch_row[5] is not None else None,
        boss_id=int(batch_row[6]) if batch_row[6] is not None else None,
        damage_mode=str(batch_row[7]) if batch_row[7] is not None else None,
        role=str(batch_row[8]) if batch_row[8] is not None else None,
        class_filter=str(batch_row[9]) if batch_row[9] is not None else None,
        spec_filter=str(batch_row[10]) if batch_row[10] is not None else None,
        week_number=int(batch_row[11]) if batch_row[11] is not None else None,
        realm=str(batch_row[12]) if batch_row[12] is not None else None,
        day_number=int(batch_row[13]) if batch_row[13] is not None else None,
        records=records,
    )


def population_prior_public_summary(snapshot: PopulationPriorSnapshot) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "read_model": "public-api-population-prior-v1",
        "record_count": len(snapshot.records),
        "records_with_parse_share": sum(row.local_parse_share is not None for row in snapshot.records),
        "documented_dimensions_available": True,
        "derived_local_parse_share_available": any(
            row.local_parse_share is not None for row in snapshot.records
        ),
        "contains_dimension_values": False,
        "contains_class_names": False,
        "contains_spec_names": False,
        "contains_metric_scalar_values": False,
        "site_tier_list_algorithm_verified": False,
        "planner_scoring_allowed": False,
        "public_release_safe": True,
    }


__all__ = [
    "PopulationPriorRecord",
    "PopulationPriorSnapshot",
    "population_prior_public_summary",
    "read_public_api_population_priors",
]
