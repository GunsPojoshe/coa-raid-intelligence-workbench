from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from coa_workbench.normalizer.canonical import stable_id
from coa_workbench.normalizer.public_api_statistics import (
    PUBLIC_API_STATISTICS_NORMALIZER_VERSION,
    PublicApiStatisticsBatch,
)

from .migrations import apply_migrations

PUBLIC_API_STATISTICS_PERSISTENCE_VERSION = "public-api-statistics-persistence-v1"
_ANALYSIS_TYPE = "official_public_api_population_statistics"
_ARTIFACT_TYPE = "public_api_population_statistics"
_ENDPOINT_CODE = "public_api_statistics"


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(_json(value).encode("utf-8")).hexdigest()


def _insert_or_match(
    connection: Any,
    *,
    table: str,
    key_fields: tuple[str, ...],
    values: Mapping[str, Any],
) -> str:
    columns = tuple(values)
    where = " AND ".join(f"{field} = ?" for field in key_fields)
    existing = connection.execute(
        f"SELECT {', '.join(columns)} FROM {table} WHERE {where}",
        [values[field] for field in key_fields],
    ).fetchone()
    if existing is None:
        placeholders = ", ".join("?" for _ in columns)
        connection.execute(
            f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})",
            [values[field] for field in columns],
        )
        return "inserted"
    existing_values = dict(zip(columns, existing, strict=True))
    if existing_values != dict(values):
        raise ValueError(f"existing {table} row conflicts with deterministic statistics output")
    return "matched"


def _output_material(batch: PublicApiStatisticsBatch) -> dict[str, Any]:
    dimensions = batch.dimensions
    return {
        "normalizer_version": PUBLIC_API_STATISTICS_NORMALIZER_VERSION,
        "dimensions": {
            "phase": dimensions.phase,
            "difficulty": dimensions.difficulty,
            "metric": dimensions.metric,
            "bracket": dimensions.bracket,
            "location": dimensions.location,
            "boss_id": dimensions.boss_id,
            "damage_mode": dimensions.damage_mode,
            "role": dimensions.role,
            "class_filter": dimensions.class_filter,
            "spec_filter": dimensions.spec_filter,
            "week_number": dimensions.week_number,
            "realm": dimensions.realm,
            "day_number": dimensions.day_number,
        },
        "class_summaries": [
            {"class_name": row.class_name, "total_parses": row.total_parses}
            for row in batch.class_summaries
        ],
        "records": [
            {
                "class_name": row.class_name,
                "spec_name": row.spec_name,
                "avg": row.avg,
                "median": row.median,
                "max": row.maximum,
                "min": row.minimum,
                "total_parses": row.total_parses,
                "percentiles": list(row.percentiles),
            }
            for row in batch.records
        ],
    }


def persist_public_api_statistics(
    *,
    database_path: Path,
    migrations_path: Path,
    source_raw_id: str,
    source_code: str,
    batch: PublicApiStatisticsBatch,
) -> dict[str, Any]:
    """Persist one exact normalized public statistics batch with deterministic replay semantics."""
    if not source_raw_id:
        raise ValueError("source_raw_id cannot be empty")
    if not source_code:
        raise ValueError("source_code cannot be empty")

    apply_migrations(database_path, migrations_path)
    try:
        import duckdb
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("DuckDB is required for public API statistics persistence") from exc

    dimensions = batch.dimensions
    output_fingerprint = _sha256_json(_output_material(batch))
    batch_id = stable_id(
        "public_api_statistics_batch",
        source_raw_id,
        PUBLIC_API_STATISTICS_NORMALIZER_VERSION,
    )
    analysis_run_id = stable_id(
        "analysis_run",
        _ANALYSIS_TYPE,
        PUBLIC_API_STATISTICS_PERSISTENCE_VERSION,
        source_raw_id,
    )
    raw_dependency_id = stable_id(
        "artifact_dependency",
        _ARTIFACT_TYPE,
        batch_id,
        "raw_object",
        source_raw_id,
        PUBLIC_API_STATISTICS_NORMALIZER_VERSION,
    )
    endpoint_dependency_id = stable_id(
        "artifact_dependency",
        _ARTIFACT_TYPE,
        batch_id,
        "source_endpoint",
        _ENDPOINT_CODE,
        PUBLIC_API_STATISTICS_NORMALIZER_VERSION,
    )

    batch_values = {
        "batch_id": batch_id,
        "raw_id": source_raw_id,
        "source_code": source_code,
        "endpoint_code": _ENDPOINT_CODE,
        "normalizer_version": PUBLIC_API_STATISTICS_NORMALIZER_VERSION,
        "phase_number": dimensions.phase,
        "difficulty": dimensions.difficulty,
        "metric": dimensions.metric,
        "bracket": dimensions.bracket,
        "location": dimensions.location,
        "boss_id": dimensions.boss_id,
        "damage_mode": dimensions.damage_mode,
        "role": dimensions.role,
        "class_filter": dimensions.class_filter,
        "spec_filter": dimensions.spec_filter,
        "week_number": dimensions.week_number,
        "realm": dimensions.realm,
        "day_number": dimensions.day_number,
        "class_count": len(batch.class_summaries),
        "spec_record_count": len(batch.records),
        "percentile_value_count": batch.percentile_value_count,
        "output_fingerprint": output_fingerprint,
        "metadata_json": _json(
            {
                "persistence_version": PUBLIC_API_STATISTICS_PERSISTENCE_VERSION,
                "source_kind": "official_documented_public_api",
                "request_scope_required": True,
                "mechanic_semantics_verified": False,
                "site_tier_list_algorithm_verified": False,
                "planner_scoring_allowed": False,
            }
        ),
    }

    with duckdb.connect(str(database_path)) as connection:
        source_exists = connection.execute(
            "SELECT 1 FROM raw_object WHERE raw_id = ? LIMIT 1",
            [source_raw_id],
        ).fetchone()
        if source_exists is None:
            raise ValueError("source_raw_id is not registered in raw_object")

        connection.execute("BEGIN TRANSACTION")
        try:
            batch_result = _insert_or_match(
                connection,
                table="public_api_statistics_batch",
                key_fields=("batch_id",),
                values=batch_values,
            )

            class_inserted = 0
            class_matched = 0
            for row in batch.class_summaries:
                result = _insert_or_match(
                    connection,
                    table="public_api_statistics_class",
                    key_fields=("batch_id", "class_name"),
                    values={
                        "batch_id": batch_id,
                        "class_name": row.class_name,
                        "total_parses": row.total_parses,
                    },
                )
                if result == "inserted":
                    class_inserted += 1
                else:
                    class_matched += 1

            spec_inserted = 0
            spec_matched = 0
            for row in batch.records:
                result = _insert_or_match(
                    connection,
                    table="public_api_statistics_spec",
                    key_fields=("batch_id", "class_name", "spec_name"),
                    values={
                        "batch_id": batch_id,
                        "class_name": row.class_name,
                        "spec_name": row.spec_name,
                        "avg": row.avg,
                        "median": row.median,
                        "max": row.maximum,
                        "min": row.minimum,
                        "total_parses": row.total_parses,
                        "percentiles_json": _json(dict(row.percentiles)),
                    },
                )
                if result == "inserted":
                    spec_inserted += 1
                else:
                    spec_matched += 1

            _insert_or_match(
                connection,
                table="analysis_run",
                key_fields=("analysis_run_id",),
                values={
                    "analysis_run_id": analysis_run_id,
                    "analysis_type": _ANALYSIS_TYPE,
                    "analysis_version": PUBLIC_API_STATISTICS_PERSISTENCE_VERSION,
                    "artifact_type": _ARTIFACT_TYPE,
                    "artifact_key": batch_id,
                    "target_scope_json": _json(
                        {
                            "scope": "one_official_public_api_statistics_capture",
                            "class_count": len(batch.class_summaries),
                            "spec_record_count": len(batch.records),
                        }
                    ),
                    "input_fingerprint": source_raw_id,
                    "output_fingerprint": output_fingerprint,
                    "status": "completed",
                    "metadata_json": _json(
                        {
                            "normalizer_version": PUBLIC_API_STATISTICS_NORMALIZER_VERSION,
                            "documented_dimensions_persisted": True,
                            "mechanic_semantics_verified": False,
                            "planner_scoring_allowed": False,
                        }
                    ),
                },
            )
            _insert_or_match(
                connection,
                table="artifact_dependency",
                key_fields=("dependency_id",),
                values={
                    "dependency_id": raw_dependency_id,
                    "artifact_type": _ARTIFACT_TYPE,
                    "artifact_key": batch_id,
                    "analysis_type": _ANALYSIS_TYPE,
                    "analysis_version": PUBLIC_API_STATISTICS_PERSISTENCE_VERSION,
                    "dependency_type": "raw_object",
                    "dependency_key": source_raw_id,
                    "dependency_version": PUBLIC_API_STATISTICS_NORMALIZER_VERSION,
                    "active": True,
                    "metadata_json": _json(
                        {
                            "source_code": source_code,
                            "endpoint_code": _ENDPOINT_CODE,
                        }
                    ),
                },
            )
            _insert_or_match(
                connection,
                table="artifact_dependency",
                key_fields=("dependency_id",),
                values={
                    "dependency_id": endpoint_dependency_id,
                    "artifact_type": _ARTIFACT_TYPE,
                    "artifact_key": batch_id,
                    "analysis_type": _ANALYSIS_TYPE,
                    "analysis_version": PUBLIC_API_STATISTICS_PERSISTENCE_VERSION,
                    "dependency_type": "source_endpoint",
                    "dependency_key": _ENDPOINT_CODE,
                    "dependency_version": PUBLIC_API_STATISTICS_NORMALIZER_VERSION,
                    "active": True,
                    "metadata_json": _json(
                        {
                            "source_code": source_code,
                            "endpoint_code": _ENDPOINT_CODE,
                            "reanalysis_on_source_change": True,
                        }
                    ),
                },
            )
            connection.execute(
                """
                UPDATE analysis_run
                SET finished_at = COALESCE(finished_at, CURRENT_TIMESTAMP)
                WHERE analysis_run_id = ?
                """,
                [analysis_run_id],
            )
            connection.execute("COMMIT")
        except Exception:
            connection.execute("ROLLBACK")
            raise

    return {
        "persistence_version": PUBLIC_API_STATISTICS_PERSISTENCE_VERSION,
        "normalizer_version": PUBLIC_API_STATISTICS_NORMALIZER_VERSION,
        "status": "completed",
        "class_count": len(batch.class_summaries),
        "spec_record_count": len(batch.records),
        "percentile_value_count": batch.percentile_value_count,
        "batch_inserted": batch_result == "inserted",
        "batch_matched": batch_result == "matched",
        "class_rows_inserted": class_inserted,
        "class_rows_matched": class_matched,
        "spec_rows_inserted": spec_inserted,
        "spec_rows_matched": spec_matched,
        "analysis_run_registered": True,
        "source_dependency_registered": True,
        "raw_dependency_registered": True,
        "source_endpoint_dependency_registered": True,
        "contains_source_scalar_values": False,
        "contains_source_raw_id": False,
        "contains_output_fingerprint": False,
        "mechanic_semantics_verified": False,
        "site_tier_list_algorithm_verified": False,
        "planner_scoring_allowed": False,
    }


__all__ = [
    "PUBLIC_API_STATISTICS_PERSISTENCE_VERSION",
    "persist_public_api_statistics",
]
