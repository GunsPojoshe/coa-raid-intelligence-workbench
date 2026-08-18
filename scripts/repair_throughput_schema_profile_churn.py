from __future__ import annotations

import argparse
import json
from pathlib import Path

from coa_workbench.storage.migrations import apply_migrations

_TARGET_ENDPOINT = "report_encounter_throughput_timeline_api"
_PROFILE_CHANGE_TYPES = (
    "schema_changed",
    "field_added",
    "field_removed",
    "field_type_changed",
    "new_dimension_value",
)


def repair_profile_unaware_churn(database: Path, migrations: Path) -> dict[str, object]:
    """Supersede only profile-unaware schema churn for the current throughput endpoint.

    Raw captures, schema snapshots and the original endpoint-added event are preserved. The repair
    refuses to proceed if any targeted event already has a downstream reanalysis request.
    """
    apply_migrations(database, migrations)

    import duckdb

    placeholders = ", ".join("?" for _ in _PROFILE_CHANGE_TYPES)
    with duckdb.connect(str(database)) as connection:
        target_rows = connection.execute(
            f"""
            SELECT e.event_id, e.change_type
            FROM source_change_event AS e
            JOIN source_capture AS c ON c.capture_id = e.capture_id
            WHERE e.endpoint_code = ?
              AND e.status = 'open'
              AND e.change_type IN ({placeholders})
              AND json_extract_string(c.metadata_json, '$.observation_profile_key') IS NULL
            ORDER BY e.event_id
            """,
            [_TARGET_ENDPOINT, *_PROFILE_CHANGE_TYPES],
        ).fetchall()
        target_ids = [str(row[0]) for row in target_rows]

        if not target_ids:
            return {
                "repair_version": "throughput-schema-profile-repair-v1",
                "status": "no_action",
                "endpoint_code": _TARGET_ENDPOINT,
                "superseded_change_event_count": 0,
                "linked_reanalysis_request_count": 0,
                "raw_objects_deleted": False,
                "raw_fetch_observations_deleted": False,
                "source_captures_deleted": False,
                "schema_snapshots_deleted": False,
            }

        id_placeholders = ", ".join("?" for _ in target_ids)
        linked_reanalysis_count = int(
            connection.execute(
                f"""
                SELECT COUNT(*)
                FROM reanalysis_request
                WHERE reason_event_id IN ({id_placeholders})
                """,
                target_ids,
            ).fetchone()[0]
        )
        if linked_reanalysis_count:
            raise RuntimeError(
                "refusing to supersede profile-unaware changes that already have "
                "reanalysis requests"
            )

        before_raw = int(connection.execute("SELECT COUNT(*) FROM raw_object").fetchone()[0])
        before_raw_fetch = int(
            connection.execute("SELECT COUNT(*) FROM raw_fetch_observation").fetchone()[0]
        )
        before_captures = int(
            connection.execute("SELECT COUNT(*) FROM source_capture").fetchone()[0]
        )
        before_snapshots = int(
            connection.execute("SELECT COUNT(*) FROM source_schema_snapshot").fetchone()[0]
        )

        connection.execute(
            f"""
            UPDATE source_change_event
            SET status = 'superseded_profile_partition'
            WHERE event_id IN ({id_placeholders})
            """,
            target_ids,
        )

        remaining_open = int(
            connection.execute(
                f"""
                SELECT COUNT(*)
                FROM source_change_event AS e
                JOIN source_capture AS c ON c.capture_id = e.capture_id
                WHERE e.endpoint_code = ?
                  AND e.status = 'open'
                  AND e.change_type IN ({placeholders})
                  AND json_extract_string(c.metadata_json, '$.observation_profile_key') IS NULL
                """,
                [_TARGET_ENDPOINT, *_PROFILE_CHANGE_TYPES],
            ).fetchone()[0]
        )
        after_raw = int(connection.execute("SELECT COUNT(*) FROM raw_object").fetchone()[0])
        after_raw_fetch = int(
            connection.execute("SELECT COUNT(*) FROM raw_fetch_observation").fetchone()[0]
        )
        after_captures = int(
            connection.execute("SELECT COUNT(*) FROM source_capture").fetchone()[0]
        )
        after_snapshots = int(
            connection.execute("SELECT COUNT(*) FROM source_schema_snapshot").fetchone()[0]
        )

    if remaining_open:
        raise RuntimeError("profile-unaware schema churn remained open after bounded repair")
    if (before_raw, before_raw_fetch, before_captures, before_snapshots) != (
        after_raw,
        after_raw_fetch,
        after_captures,
        after_snapshots,
    ):
        raise RuntimeError("bounded profile repair unexpectedly changed preserved evidence counts")

    by_type: dict[str, int] = {}
    for _event_id, change_type in target_rows:
        key = str(change_type)
        by_type[key] = by_type.get(key, 0) + 1

    return {
        "repair_version": "throughput-schema-profile-repair-v1",
        "status": "repaired",
        "endpoint_code": _TARGET_ENDPOINT,
        "superseded_change_event_count": len(target_ids),
        "superseded_change_types": dict(sorted(by_type.items())),
        "linked_reanalysis_request_count": 0,
        "raw_objects_deleted": False,
        "raw_fetch_observations_deleted": False,
        "source_captures_deleted": False,
        "schema_snapshots_deleted": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Supersede only the profile-unaware throughput schema churn created before reviewed "
            "metric/perspective schema profiles existed. Raw evidence and snapshots are preserved."
        )
    )
    parser.add_argument("--database", type=Path, default=Path("data/warehouse/coa.duckdb"))
    parser.add_argument("--migrations", type=Path, default=Path("migrations"))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    result = repair_profile_unaware_churn(args.database, args.migrations)
    rendered = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
