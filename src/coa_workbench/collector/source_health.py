from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _timestamp(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _dimension_counts(raw: str | None) -> dict[str, int]:
    if not raw:
        return {}
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        return {}
    return {
        str(key): len(value) if isinstance(value, list) else 0
        for key, value in sorted(payload.items())
    }


def build_source_health(
    database_path: Path,
    *,
    recent_change_limit: int = 25,
    recent_analysis_limit: int = 10,
) -> dict[str, Any]:
    """Build a compact Source Observatory health view without exposing raw payload values."""
    if recent_change_limit < 1:
        raise ValueError("recent_change_limit must be at least 1")
    if recent_analysis_limit < 1:
        raise ValueError("recent_analysis_limit must be at least 1")

    import duckdb

    with duckdb.connect(str(database_path), read_only=True) as connection:
        endpoint_rows = connection.execute(
            """
            SELECT endpoint_code, source_code, logical_name, route_template, method,
                   status, last_seen_at, schema_fingerprint
            FROM source_endpoint
            WHERE source_code IS NOT NULL
            ORDER BY endpoint_code
            """
        ).fetchall()

        capture_rows = connection.execute(
            """
            SELECT endpoint_code, COUNT(*) AS capture_count, MAX(captured_at) AS latest_capture_at
            FROM source_capture
            GROUP BY endpoint_code
            """
        ).fetchall()
        captures = {
            str(row[0]): {"capture_count": int(row[1]), "latest_capture_at": _timestamp(row[2])}
            for row in capture_rows
        }

        acquisition_rows = connection.execute(
            """
            SELECT endpoint_code, observed_at, capture_mode, http_status, body_kind,
                   outcome, blocker_class, error_class
            FROM (
                SELECT endpoint_code, observed_at, capture_mode, http_status, body_kind,
                       outcome, blocker_class, error_class,
                       ROW_NUMBER() OVER (
                           PARTITION BY endpoint_code
                           ORDER BY observed_at DESC, acquisition_id DESC
                       ) AS row_number
                FROM source_acquisition_observation
            )
            WHERE row_number = 1
            ORDER BY endpoint_code
            """
        ).fetchall()
        acquisitions = {
            str(row[0]): {
                "observed_at": _timestamp(row[1]),
                "capture_mode": str(row[2]),
                "http_status": int(row[3]) if row[3] is not None else None,
                "body_kind": str(row[4]),
                "outcome": str(row[5]),
                "blocker_class": str(row[6]) if row[6] is not None else None,
                "error_class": str(row[7]) if row[7] is not None else None,
            }
            for row in acquisition_rows
        }

        change_rows = connection.execute(
            """
            SELECT endpoint_code, COUNT(*)
            FROM source_change_event
            WHERE status = 'open'
            GROUP BY endpoint_code
            """
        ).fetchall()
        open_changes = {str(row[0]): int(row[1]) for row in change_rows}

        snapshot_rows = connection.execute(
            """
            SELECT endpoint_code, observed_at, schema_fingerprint, root_type,
                   dimension_values_json, scan_truncated
            FROM (
                SELECT endpoint_code, observed_at, schema_fingerprint, root_type,
                       dimension_values_json, scan_truncated,
                       ROW_NUMBER() OVER (
                           PARTITION BY endpoint_code
                           ORDER BY observed_at DESC, snapshot_id DESC
                       ) AS row_number
                FROM source_schema_snapshot
            )
            WHERE row_number = 1
            ORDER BY endpoint_code
            """
        ).fetchall()
        snapshots = {
            str(row[0]): {
                "observed_at": _timestamp(row[1]),
                "schema_fingerprint": str(row[2]),
                "root_type": str(row[3]),
                "dimension_value_counts": _dimension_counts(row[4]),
                "scan_truncated": bool(row[5]),
            }
            for row in snapshot_rows
        }

        pending_reanalysis = int(
            connection.execute(
                "SELECT COUNT(*) FROM reanalysis_request WHERE status = 'pending'"
            ).fetchone()[0]
        )
        active_dependencies = int(
            connection.execute(
                "SELECT COUNT(*) FROM artifact_dependency WHERE active = TRUE"
            ).fetchone()[0]
        )
        completed_analysis_runs = int(
            connection.execute(
                "SELECT COUNT(*) FROM analysis_run WHERE status = 'completed'"
            ).fetchone()[0]
        )
        open_change_total = int(
            connection.execute(
                "SELECT COUNT(*) FROM source_change_event WHERE status = 'open'"
            ).fetchone()[0]
        )

        recent_rows = connection.execute(
            """
            SELECT endpoint_code, observed_at, change_type, severity, subject_path, status
            FROM source_change_event
            ORDER BY observed_at DESC, event_id DESC
            LIMIT ?
            """,
            [recent_change_limit],
        ).fetchall()
        recent_analysis_rows = connection.execute(
            """
            SELECT analysis_type, analysis_version, artifact_type, artifact_key,
                   started_at, finished_at, status
            FROM analysis_run
            ORDER BY COALESCE(finished_at, started_at) DESC, analysis_run_id DESC
            LIMIT ?
            """,
            [recent_analysis_limit],
        ).fetchall()

    endpoints: list[dict[str, Any]] = []
    for row in endpoint_rows:
        endpoint_code = str(row[0])
        acquisition = acquisitions.get(endpoint_code)
        change_count = open_changes.get(endpoint_code, 0)
        capture = captures.get(endpoint_code, {"capture_count": 0, "latest_capture_at": None})
        snapshot = snapshots.get(endpoint_code)

        if acquisition and acquisition["outcome"] in {"blocked", "transport_error", "http_error"}:
            health_state = "acquisition_problem"
        elif change_count:
            health_state = "changed"
        elif capture["capture_count"]:
            health_state = "observed"
        else:
            health_state = "registered"

        endpoints.append(
            {
                "endpoint_code": endpoint_code,
                "source_code": str(row[1]) if row[1] is not None else None,
                "logical_name": str(row[2]) if row[2] is not None else None,
                "route_template": str(row[3]) if row[3] is not None else None,
                "method": str(row[4]) if row[4] is not None else None,
                "registry_status": str(row[5]) if row[5] is not None else None,
                "last_seen_at": _timestamp(row[6]),
                "schema_fingerprint": str(row[7]) if row[7] is not None else None,
                "capture_count": capture["capture_count"],
                "latest_capture_at": capture["latest_capture_at"],
                "open_change_count": change_count,
                "latest_acquisition": acquisition,
                "latest_schema": snapshot,
                "health_state": health_state,
            }
        )

    return {
        "health_version": "source-health-v1",
        "database": str(database_path),
        "summary": {
            "endpoint_count": len(endpoints),
            "captured_endpoint_count": sum(1 for item in endpoints if item["capture_count"] > 0),
            "open_change_event_count": open_change_total,
            "pending_reanalysis_request_count": pending_reanalysis,
            "active_dependency_count": active_dependencies,
            "completed_analysis_run_count": completed_analysis_runs,
            "acquisition_problem_endpoint_count": sum(
                1 for item in endpoints if item["health_state"] == "acquisition_problem"
            ),
        },
        "endpoints": endpoints,
        "recent_changes": [
            {
                "endpoint_code": str(row[0]),
                "observed_at": _timestamp(row[1]),
                "change_type": str(row[2]),
                "severity": str(row[3]),
                "subject_path": str(row[4]) if row[4] is not None else None,
                "status": str(row[5]),
            }
            for row in recent_rows
        ],
        "recent_analysis_runs": [
            {
                "analysis_type": str(row[0]),
                "analysis_version": str(row[1]),
                "artifact_type": str(row[2]) if row[2] is not None else None,
                "artifact_key": str(row[3]) if row[3] is not None else None,
                "started_at": _timestamp(row[4]),
                "finished_at": _timestamp(row[5]),
                "status": str(row[6]),
            }
            for row in recent_analysis_rows
        ],
        "privacy": {
            "raw_payloads_included": False,
            "request_headers_included": False,
            "cookies_included": False,
            "dimension_values_included": False,
        },
    }


__all__ = ["build_source_health"]
