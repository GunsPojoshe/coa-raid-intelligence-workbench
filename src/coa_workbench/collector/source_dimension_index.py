from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

from coa_workbench.collector.source_observatory import register_artifact_dependency
from coa_workbench.storage.migrations import apply_migrations

SOURCE_DIMENSION_INDEX_VERSION = "source-dimension-index-v1"
SOURCE_DIMENSION_ARTIFACT_TYPE = "source_dimension_index"
SOURCE_DIMENSION_ANALYSIS_TYPE = "source_dimension_index"


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _endpoint_codes(values: Iterable[str]) -> tuple[str, ...]:
    codes = tuple(sorted({str(value).strip() for value in values if str(value).strip()}))
    if not codes:
        raise ValueError("source dimension index requires at least one endpoint")
    return codes


def rebuild_source_dimension_index(
    database_path: Path,
    migrations_dir: Path,
    *,
    source_code: str,
    endpoint_codes: Iterable[str],
    artifact_key: str | None = None,
) -> dict[str, Any]:
    """Rebuild the approved current dimension index from latest complete source snapshots.

    Raw dimension values remain in the local DuckDB. The returned summary contains counts and
    fingerprints only, so it can be surfaced through Source Health without exposing values.
    """
    apply_migrations(database_path, migrations_dir)
    endpoints = _endpoint_codes(endpoint_codes)
    artifact = artifact_key or source_code

    dependency_ids = tuple(
        register_artifact_dependency(
            database_path,
            migrations_dir,
            artifact_type=SOURCE_DIMENSION_ARTIFACT_TYPE,
            artifact_key=artifact,
            analysis_type=SOURCE_DIMENSION_ANALYSIS_TYPE,
            analysis_version=SOURCE_DIMENSION_INDEX_VERSION,
            dependency_type="source_endpoint",
            dependency_key=endpoint_code,
            metadata={"source_code": source_code},
        )
        for endpoint_code in endpoints
    )

    import duckdb

    placeholders = ", ".join("?" for _ in endpoints)
    with duckdb.connect(str(database_path)) as connection:
        snapshot_rows = connection.execute(
            f"""
            SELECT snapshot_id, endpoint_code, observed_at, schema_fingerprint,
                   dimension_values_json
            FROM (
                SELECT s.snapshot_id, s.endpoint_code, s.observed_at, s.schema_fingerprint,
                       s.dimension_values_json,
                       ROW_NUMBER() OVER (
                           PARTITION BY s.endpoint_code
                           ORDER BY s.observed_at DESC, s.snapshot_id DESC
                       ) AS row_number
                FROM source_schema_snapshot AS s
                JOIN source_endpoint AS e ON e.endpoint_code = s.endpoint_code
                WHERE e.source_code = ?
                  AND s.scan_truncated = FALSE
                  AND s.endpoint_code IN ({placeholders})
            )
            WHERE row_number = 1
            ORDER BY endpoint_code
            """,
            [source_code, *endpoints],
        ).fetchall()

        if not snapshot_rows:
            return {
                "index_version": SOURCE_DIMENSION_INDEX_VERSION,
                "status": "no_snapshots",
                "source_code": source_code,
                "artifact_key": artifact,
                "dependency_count": len(dependency_ids),
                "configured_endpoint_count": len(endpoints),
                "observed_endpoint_count": 0,
                "snapshot_count": 0,
                "dimension_name_count": 0,
                "dimension_value_count": 0,
                "completed_reanalysis_request_count": 0,
            }

        snapshot_identity: list[dict[str, str]] = []
        dimension_rows: set[tuple[str, str, str]] = set()
        for row in snapshot_rows:
            endpoint_code = str(row[1])
            snapshot_identity.append(
                {
                    "snapshot_id": str(row[0]),
                    "endpoint_code": endpoint_code,
                    "schema_fingerprint": str(row[3]),
                }
            )
            dimensions = json.loads(row[4]) if row[4] else {}
            if not isinstance(dimensions, dict):
                continue
            for dimension_name, values in dimensions.items():
                if not isinstance(values, list):
                    continue
                for value in values:
                    dimension_rows.add((endpoint_code, str(dimension_name), str(value)))

        canonical_dimensions = sorted(dimension_rows)
        input_fingerprint = _sha256(_json(snapshot_identity))
        output_fingerprint = _sha256(_json(canonical_dimensions))
        analysis_run_id = _sha256(
            f"{SOURCE_DIMENSION_INDEX_VERSION}\0{artifact}\0{input_fingerprint}"
        )
        target_scope = {
            "source_code": source_code,
            "artifact_key": artifact,
            "endpoint_codes": list(endpoints),
        }

        connection.execute(
            """
            INSERT INTO analysis_run (
                analysis_run_id, analysis_type, analysis_version, artifact_type,
                artifact_key, target_scope_json, input_fingerprint, output_fingerprint,
                started_at, finished_at, status, metadata_json
            ) SELECT ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP,
                     'completed', ?
            WHERE NOT EXISTS (
                SELECT 1 FROM analysis_run WHERE analysis_run_id = ?
            )
            """,
            [
                analysis_run_id,
                SOURCE_DIMENSION_ANALYSIS_TYPE,
                SOURCE_DIMENSION_INDEX_VERSION,
                SOURCE_DIMENSION_ARTIFACT_TYPE,
                artifact,
                _json(target_scope),
                input_fingerprint,
                output_fingerprint,
                _json({"dependency_ids": list(dependency_ids)}),
                analysis_run_id,
            ],
        )

        for endpoint_code, dimension_name, dimension_value in canonical_dimensions:
            connection.execute(
                """
                INSERT INTO source_dimension_index_value (
                    analysis_run_id, artifact_key, source_code, endpoint_code,
                    dimension_name, dimension_value
                ) SELECT ?, ?, ?, ?, ?, ?
                WHERE NOT EXISTS (
                    SELECT 1 FROM source_dimension_index_value
                    WHERE analysis_run_id = ? AND source_code = ? AND endpoint_code = ?
                      AND dimension_name = ? AND dimension_value = ?
                )
                """,
                [
                    analysis_run_id,
                    artifact,
                    source_code,
                    endpoint_code,
                    dimension_name,
                    dimension_value,
                    analysis_run_id,
                    source_code,
                    endpoint_code,
                    dimension_name,
                    dimension_value,
                ],
            )

        pending_count = int(
            connection.execute(
                """
                SELECT COUNT(*)
                FROM reanalysis_request
                WHERE artifact_type = ? AND artifact_key = ? AND status = 'pending'
                """,
                [SOURCE_DIMENSION_ARTIFACT_TYPE, artifact],
            ).fetchone()[0]
        )
        if pending_count:
            connection.execute(
                """
                UPDATE reanalysis_request
                SET status = 'completed'
                WHERE artifact_type = ? AND artifact_key = ? AND status = 'pending'
                """,
                [SOURCE_DIMENSION_ARTIFACT_TYPE, artifact],
            )

    dimension_names = {row[1] for row in canonical_dimensions}
    return {
        "index_version": SOURCE_DIMENSION_INDEX_VERSION,
        "status": "completed",
        "source_code": source_code,
        "artifact_key": artifact,
        "analysis_run_id": analysis_run_id,
        "input_fingerprint": input_fingerprint,
        "output_fingerprint": output_fingerprint,
        "dependency_count": len(dependency_ids),
        "configured_endpoint_count": len(endpoints),
        "observed_endpoint_count": len(snapshot_rows),
        "snapshot_count": len(snapshot_rows),
        "dimension_name_count": len(dimension_names),
        "dimension_value_count": len(canonical_dimensions),
        "completed_reanalysis_request_count": pending_count,
    }


__all__ = [
    "SOURCE_DIMENSION_ANALYSIS_TYPE",
    "SOURCE_DIMENSION_ARTIFACT_TYPE",
    "SOURCE_DIMENSION_INDEX_VERSION",
    "rebuild_source_dimension_index",
]
