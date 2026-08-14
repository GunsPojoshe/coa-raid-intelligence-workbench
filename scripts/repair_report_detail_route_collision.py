from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.parse import urlsplit

from coa_workbench.collector.source_health import build_source_health
from coa_workbench.storage.migrations import apply_migrations

_FALSE_ENDPOINT = "report_detail_api"
_COLLIDING_STATIC_PATH = "/api/reports/queue-status"
_EXPECTED_HOST = "coa.ascensionlogs.gg"
_MAX_COLLISION_ROWS = 32


def _placeholders(count: int) -> str:
    return ", ".join("?" for _ in range(count))


def repair_false_report_detail_collision(
    database_path: Path,
    migrations_dir: Path,
) -> dict[str, object]:
    """Remove only the proven queue-status -> report-detail misclassification.

    Raw content and raw fetch observations remain immutable. The repair deletes only the derived
    report-detail classification, snapshots/change events, contract binding, and endpoint binding.
    It fails closed if any report-detail acquisition points at a path other than the known static
    queue-status route or if downstream reanalysis already depends on the false change event.
    """
    apply_migrations(database_path, migrations_dir)

    import duckdb

    status = "no_matching_false_observation"
    removed_acquisition_count = 0
    removed_capture_count = 0
    removed_change_event_count = 0

    with duckdb.connect(str(database_path)) as connection:
        rows = connection.execute(
            """
            SELECT a.acquisition_id, a.raw_id, a.raw_observation_id, a.source_capture_id,
                   f.request_url_sanitized
            FROM source_acquisition_observation AS a
            LEFT JOIN raw_fetch_observation AS f
              ON f.observation_id = a.raw_observation_id
            WHERE a.endpoint_code = ?
            ORDER BY a.observed_at, a.acquisition_id
            """,
            [_FALSE_ENDPOINT],
        ).fetchall()

        if rows:
            if len(rows) > _MAX_COLLISION_ROWS:
                raise RuntimeError(
                    "report-detail collision row count exceeds bounded repair maximum"
                )

            for row in rows:
                sanitized_url = row[4]
                if not isinstance(sanitized_url, str) or not sanitized_url:
                    raise RuntimeError(
                        "report-detail acquisition is missing sanitized request provenance"
                    )
                parts = urlsplit(sanitized_url)
                if (
                    parts.scheme != "https"
                    or parts.hostname != _EXPECTED_HOST
                    or parts.path != _COLLIDING_STATIC_PATH
                    or parts.query
                ):
                    raise RuntimeError(
                        "report-detail acquisition is not the proven queue-status collision; "
                        "aborting"
                    )

            acquisition_ids = [str(row[0]) for row in rows]
            raw_ids = sorted({str(row[1]) for row in rows if row[1] is not None})
            capture_ids = sorted({str(row[3]) for row in rows if row[3] is not None})
            capture_id_set = set(capture_ids)

            event_rows = connection.execute(
                "SELECT event_id, capture_id FROM source_change_event WHERE endpoint_code = ?",
                [_FALSE_ENDPOINT],
            ).fetchall()
            if any(str(row[1]) not in capture_id_set for row in event_rows):
                raise RuntimeError(
                    "report-detail change event is not bound to the proven false capture"
                )
            event_ids = [str(row[0]) for row in event_rows]

            if event_ids:
                query = (
                    "SELECT COUNT(*) FROM reanalysis_request WHERE reason_event_id IN ("
                    + _placeholders(len(event_ids))
                    + ")"
                )
                dependent_requests = int(connection.execute(query, event_ids).fetchone()[0])
                if dependent_requests:
                    raise RuntimeError(
                        "downstream reanalysis depends on the false report-detail event; aborting"
                    )

            active_dependencies = int(
                connection.execute(
                    """
                    SELECT COUNT(*) FROM artifact_dependency
                    WHERE dependency_type = 'source_endpoint'
                      AND dependency_key = ? AND active = TRUE
                    """,
                    [_FALSE_ENDPOINT],
                ).fetchone()[0]
            )
            if active_dependencies:
                raise RuntimeError(
                    "active artifact dependency exists for false report-detail endpoint"
                )

            endpoint_row = connection.execute(
                "SELECT endpoint_id FROM source_endpoint WHERE endpoint_code = ?",
                [_FALSE_ENDPOINT],
            ).fetchone()
            endpoint_id = str(endpoint_row[0]) if endpoint_row else None

            connection.execute("BEGIN TRANSACTION")
            try:
                if endpoint_id and raw_ids:
                    query = (
                        "UPDATE raw_object SET endpoint_id = NULL WHERE endpoint_id = ? "
                        "AND raw_id IN ("
                        + _placeholders(len(raw_ids))
                        + ")"
                    )
                    connection.execute(query, [endpoint_id, *raw_ids])

                if event_ids:
                    query = (
                        "DELETE FROM source_change_event WHERE event_id IN ("
                        + _placeholders(len(event_ids))
                        + ")"
                    )
                    connection.execute(query, event_ids)
                if capture_ids:
                    snapshot_query = (
                        "DELETE FROM source_schema_snapshot WHERE capture_id IN ("
                        + _placeholders(len(capture_ids))
                        + ")"
                    )
                    capture_query = (
                        "DELETE FROM source_capture WHERE capture_id IN ("
                        + _placeholders(len(capture_ids))
                        + ")"
                    )
                    connection.execute(snapshot_query, capture_ids)
                    connection.execute(capture_query, capture_ids)

                acquisition_query = (
                    "DELETE FROM source_acquisition_observation WHERE acquisition_id IN ("
                    + _placeholders(len(acquisition_ids))
                    + ")"
                )
                connection.execute(acquisition_query, acquisition_ids)

                remaining = int(
                    connection.execute(
                        """
                        SELECT COUNT(*) FROM source_acquisition_observation
                        WHERE endpoint_code = ?
                        """,
                        [_FALSE_ENDPOINT],
                    ).fetchone()[0]
                ) + int(
                    connection.execute(
                        "SELECT COUNT(*) FROM source_capture WHERE endpoint_code = ?",
                        [_FALSE_ENDPOINT],
                    ).fetchone()[0]
                )
                if remaining:
                    raise RuntimeError(
                        "unexpected report-detail observations remain after bounded repair"
                    )

                connection.execute(
                    "DELETE FROM source_contract_version WHERE endpoint_code = ?",
                    [_FALSE_ENDPOINT],
                )
                if endpoint_id:
                    connection.execute(
                        "DELETE FROM source_endpoint WHERE endpoint_code = ?",
                        [_FALSE_ENDPOINT],
                    )
                connection.execute("COMMIT")
            except Exception:
                connection.execute("ROLLBACK")
                raise

            status = "repaired"
            removed_acquisition_count = len(acquisition_ids)
            removed_capture_count = len(capture_ids)
            removed_change_event_count = len(event_ids)

    health = build_source_health(database_path)
    return {
        "repair_version": "report-detail-route-collision-repair-v1",
        "status": status,
        "removed_acquisition_count": removed_acquisition_count,
        "removed_capture_count": removed_capture_count,
        "removed_change_event_count": removed_change_event_count,
        "raw_objects_deleted": False,
        "raw_fetch_observations_deleted": False,
        "source_health_summary": health["summary"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Remove only the proven queue-status -> report-detail Source Observatory collision."
        )
    )
    parser.add_argument("--database", type=Path, default=Path("data/warehouse/coa.duckdb"))
    parser.add_argument("--migrations", type=Path, default=Path("migrations"))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    result = repair_false_report_detail_collision(args.database, args.migrations)
    rendered = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
