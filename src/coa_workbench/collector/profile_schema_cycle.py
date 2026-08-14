from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from coa_workbench.collector.json_structure import normalize_path_types
from coa_workbench.collector.source_observatory import (
    OBSERVATORY_VERSION,
    ReviewedGetContract,
    SchemaSnapshot,
    SourceChange,
    diff_schema_snapshots,
)
from coa_workbench.storage.migrations import apply_migrations

PROFILE_SCHEMA_CYCLE_VERSION = "profile-schema-cycle-v1"
_MEMBER_LEVEL_SCHEMA_CHANGE_TYPES = (
    "schema_changed",
    "field_added",
    "field_removed",
    "field_type_changed",
    "new_dimension_value",
    "observation_profile_added",
)


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _utc_naive(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value
    return value.astimezone(timezone.utc).replace(tzinfo=None)


def _snapshot_from_db_row(row: Sequence[Any]) -> SchemaSnapshot:
    path_types = normalize_path_types(
        {
            str(path): tuple(str(item) for item in values)
            for path, values in json.loads(str(row[2])).items()
        }
    )
    dimensions = {
        str(name): tuple(str(item) for item in values)
        for name, values in json.loads(str(row[3])).items()
    }
    return SchemaSnapshot(
        schema_fingerprint=_sha256_text(_json(path_types)),
        root_type=str(row[1]),
        path_types=path_types,
        dimension_values=dimensions,
        scan_truncated=bool(row[4]),
    )


def merge_schema_snapshots(snapshots: Iterable[SchemaSnapshot]) -> SchemaSnapshot:
    prepared = tuple(snapshots)
    if not prepared:
        raise ValueError("profile schema cycle requires at least one schema snapshot")

    root_types = {snapshot.root_type for snapshot in prepared}
    if len(root_types) != 1:
        raise ValueError(
            f"profile schema cycle cannot merge different root types: {sorted(root_types)}"
        )

    path_types: dict[str, set[str]] = {}
    dimensions: dict[str, set[str]] = {}
    truncated = False
    for snapshot in prepared:
        truncated = truncated or snapshot.scan_truncated
        for path, values in snapshot.path_types.items():
            path_types.setdefault(path, set()).update(values)
        for name, values in snapshot.dimension_values.items():
            dimensions.setdefault(name, set()).update(values)

    canonical_paths = {
        path: tuple(sorted(values)) for path, values in sorted(path_types.items())
    }
    canonical_dimensions = {
        name: tuple(sorted(values)) for name, values in sorted(dimensions.items()) if values
    }
    return SchemaSnapshot(
        schema_fingerprint=_sha256_text(_json(canonical_paths)),
        root_type=next(iter(root_types)),
        path_types=canonical_paths,
        dimension_values=canonical_dimensions,
        scan_truncated=truncated,
    )


def _cycle_event_id(cycle_snapshot_id: str, change: SourceChange) -> str:
    seed = _json(
        {
            "cycle_snapshot_id": cycle_snapshot_id,
            "change_type": change.change_type,
            "subject_path": change.subject_path,
            "previous_value": change.previous_value,
            "current_value": change.current_value,
        }
    )
    return _sha256_text(f"{PROFILE_SCHEMA_CYCLE_VERSION}\0event\0{seed}")


@dataclass(frozen=True, slots=True)
class ProfileSchemaCycleSummary:
    endpoint_code: str
    profile_cycle_count: int
    member_capture_count: int
    superseded_member_event_count: int
    superseded_reanalysis_request_count: int
    aggregate_change_event_count: int
    aggregate_reanalysis_request_count: int

    def public_summary(self) -> dict[str, Any]:
        return {
            "endpoint_code": self.endpoint_code,
            "profile_cycle_count": self.profile_cycle_count,
            "member_capture_count": self.member_capture_count,
            "superseded_member_event_count": self.superseded_member_event_count,
            "superseded_reanalysis_request_count": self.superseded_reanalysis_request_count,
            "aggregate_change_event_count": self.aggregate_change_event_count,
            "aggregate_reanalysis_request_count": self.aggregate_reanalysis_request_count,
            "strategy": PROFILE_SCHEMA_CYCLE_VERSION,
            "profile_values_included": False,
            "profile_hashes_included": False,
            "member_capture_ids_included": False,
            "schema_fingerprints_included": False,
            "dimension_values_included": False,
        }


def aggregate_profile_schema_observations(
    database_path: Path,
    migrations_dir: Path,
    *,
    contract: ReviewedGetContract,
    observations: Iterable[Any],
    metadata: Mapping[str, Any] | None = None,
) -> ProfileSchemaCycleSummary:
    """Replace per-response schema churn with one union schema per reviewed HAR profile cycle.

    Individual raw captures and exact source_schema_snapshot rows remain immutable. Only open
    member-level schema change events from the same captures are superseded; any linked request must
    still be pending. Aggregate cycle-level changes are then compared with the previous aggregate
    cycle for the same reviewed profile and create the normal endpoint dependencies/reanalysis
    requests.
    """
    if not contract.schema_profile_keys:
        raise ValueError("profile schema cycle requires contract.schema_profile_keys")

    apply_migrations(database_path, migrations_dir)

    capture_ids = sorted(
        {
            str(item.source_observation.source_capture_id)
            for item in observations
            if getattr(item, "source_observation", None) is not None
        }
    )
    if not capture_ids:
        return ProfileSchemaCycleSummary(
            endpoint_code=contract.endpoint_code,
            profile_cycle_count=0,
            member_capture_count=0,
            superseded_member_event_count=0,
            superseded_reanalysis_request_count=0,
            aggregate_change_event_count=0,
            aggregate_reanalysis_request_count=0,
        )

    import duckdb

    placeholders = ", ".join("?" for _ in capture_ids)
    member_change_placeholders = ", ".join(
        "?" for _ in _MEMBER_LEVEL_SCHEMA_CHANGE_TYPES
    )
    profile_cycle_count = 0
    member_capture_count = 0
    superseded_member_event_count = 0
    superseded_reanalysis_request_count = 0
    aggregate_change_event_count = 0
    aggregate_reanalysis_request_count = 0

    with duckdb.connect(str(database_path)) as connection:
        rows = connection.execute(
            f"""
            SELECT
                ss.capture_id,
                ss.root_type,
                ss.path_types_json,
                ss.dimension_values_json,
                ss.scan_truncated,
                ss.observed_at,
                json_extract_string(ss.metadata_json, '$.observation_profile_key')
            FROM source_schema_snapshot AS ss
            WHERE ss.capture_id IN ({placeholders})
              AND ss.endpoint_code = ?
            ORDER BY ss.observed_at, ss.capture_id
            """,
            [*capture_ids, contract.endpoint_code],
        ).fetchall()
        if len(rows) != len(capture_ids):
            raise RuntimeError(
                "profile schema cycle could not resolve every member source schema snapshot"
            )

        groups: dict[str, list[tuple[Any, ...]]] = {}
        for row in rows:
            profile_key = row[6]
            if not profile_key:
                raise RuntimeError(
                    "profile schema cycle member is missing observation_profile_key"
                )
            groups.setdefault(str(profile_key), []).append(row)

        connection.execute("BEGIN TRANSACTION")
        try:
            for profile_key in sorted(groups):
                group_rows = groups[profile_key]
                member_ids = sorted(str(row[0]) for row in group_rows)
                member_capture_count += len(member_ids)
                aggregate = merge_schema_snapshots(
                    _snapshot_from_db_row(row) for row in group_rows
                )
                observed_at = max(_utc_naive(row[5]) for row in group_rows)
                cycle_fingerprint = _sha256_text(
                    _json(
                        {
                            "version": PROFILE_SCHEMA_CYCLE_VERSION,
                            "contract_id": contract.contract_id,
                            "profile_key": profile_key,
                            "member_capture_ids": member_ids,
                        }
                    )
                )
                cycle_snapshot_id = _sha256_text(
                    f"{PROFILE_SCHEMA_CYCLE_VERSION}\0snapshot\0{cycle_fingerprint}"
                )
                cycle_exists = connection.execute(
                    """
                    SELECT 1
                    FROM source_profile_schema_cycle
                    WHERE cycle_snapshot_id = ?
                    """,
                    [cycle_snapshot_id],
                ).fetchone()

                group_placeholders = ", ".join("?" for _ in member_ids)
                member_events = connection.execute(
                    f"""
                    SELECT event_id
                    FROM source_change_event
                    WHERE capture_id IN ({group_placeholders})
                      AND status = 'open'
                      AND change_type IN ({member_change_placeholders})
                      AND COALESCE(
                            json_extract_string(metadata_json, '$.schema_cycle_aggregated'),
                            'false'
                          ) <> 'true'
                    ORDER BY event_id
                    """,
                    [*member_ids, *_MEMBER_LEVEL_SCHEMA_CHANGE_TYPES],
                ).fetchall()
                event_ids = [str(row[0]) for row in member_events]
                if event_ids:
                    event_placeholders = ", ".join("?" for _ in event_ids)
                    linked = connection.execute(
                        f"""
                        SELECT request_id, status
                        FROM reanalysis_request
                        WHERE reason_event_id IN ({event_placeholders})
                        ORDER BY request_id
                        """,
                        event_ids,
                    ).fetchall()
                    non_pending = [
                        str(request_id)
                        for request_id, status in linked
                        if str(status) != "pending"
                    ]
                    if non_pending:
                        raise RuntimeError(
                            "refusing to supersede profile member schema events after "
                            "downstream reanalysis has started"
                        )
                    if linked:
                        request_ids = [str(row[0]) for row in linked]
                        request_placeholders = ", ".join("?" for _ in request_ids)
                        connection.execute(
                            f"""
                            UPDATE reanalysis_request
                            SET status = 'superseded_profile_cycle_aggregation'
                            WHERE request_id IN ({request_placeholders})
                            """,
                            request_ids,
                        )
                        superseded_reanalysis_request_count += len(request_ids)
                    connection.execute(
                        f"""
                        UPDATE source_change_event
                        SET status = 'superseded_profile_cycle_aggregation'
                        WHERE event_id IN ({event_placeholders})
                        """,
                        event_ids,
                    )
                    superseded_member_event_count += len(event_ids)

                if cycle_exists is not None:
                    continue

                previous_row = connection.execute(
                    """
                    SELECT
                        schema_fingerprint,
                        root_type,
                        path_types_json,
                        dimension_values_json,
                        scan_truncated
                    FROM source_profile_schema_cycle
                    WHERE endpoint_code = ?
                      AND observation_profile_key = ?
                    ORDER BY observed_at DESC, cycle_snapshot_id DESC
                    LIMIT 1
                    """,
                    [contract.endpoint_code, profile_key],
                ).fetchone()

                safe_metadata = {
                    "schema_cycle_version": PROFILE_SCHEMA_CYCLE_VERSION,
                    "schema_cycle_aggregated": True,
                    "schema_profile_keys": list(contract.schema_profile_keys),
                    **dict(metadata or {}),
                }
                connection.execute(
                    """
                    INSERT INTO source_profile_schema_cycle (
                        cycle_snapshot_id, source_code, endpoint_code, contract_id,
                        observation_profile_key, cycle_fingerprint, observed_at,
                        member_capture_count, member_capture_ids_json, schema_fingerprint,
                        root_type, path_types_json, dimension_values_json, scan_truncated,
                        metadata_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    [
                        cycle_snapshot_id,
                        contract.source_code,
                        contract.endpoint_code,
                        contract.contract_id,
                        profile_key,
                        cycle_fingerprint,
                        observed_at,
                        len(member_ids),
                        _json(member_ids),
                        aggregate.schema_fingerprint,
                        aggregate.root_type,
                        _json(
                            {
                                path: list(values)
                                for path, values in aggregate.path_types.items()
                            }
                        ),
                        _json(
                            {
                                name: list(values)
                                for name, values in aggregate.dimension_values.items()
                            }
                        ),
                        aggregate.scan_truncated,
                        _json(safe_metadata),
                    ],
                )
                connection.execute(
                    """
                    UPDATE source_endpoint
                    SET schema_fingerprint = ?, last_verified_at = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE endpoint_code = ?
                    """,
                    [
                        aggregate.schema_fingerprint,
                        observed_at,
                        contract.endpoint_code,
                    ],
                )
                profile_cycle_count += 1

                changes: tuple[SourceChange, ...] = ()
                if previous_row is not None:
                    previous = _snapshot_from_db_row(
                        (
                            "",
                            previous_row[1],
                            previous_row[2],
                            previous_row[3],
                            previous_row[4],
                        )
                    )
                    changes = diff_schema_snapshots(previous, aggregate)

                representative_capture_id = max(
                    group_rows,
                    key=lambda row: (_utc_naive(row[5]), str(row[0])),
                )[0]
                for change in changes:
                    event_id = _cycle_event_id(cycle_snapshot_id, change)
                    connection.execute(
                        """
                        INSERT INTO source_change_event (
                            event_id, source_code, endpoint_code, contract_id, capture_id,
                            observed_at, change_type, severity, subject_path,
                            previous_value_json, current_value_json, confidence, status,
                            metadata_json
                        ) SELECT ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1.0, 'open', ?
                        WHERE NOT EXISTS (
                            SELECT 1 FROM source_change_event WHERE event_id = ?
                        )
                        """,
                        [
                            event_id,
                            contract.source_code,
                            contract.endpoint_code,
                            contract.contract_id,
                            str(representative_capture_id),
                            observed_at,
                            change.change_type,
                            change.severity,
                            change.subject_path,
                            (
                                _json(change.previous_value)
                                if change.previous_value is not None
                                else None
                            ),
                            (
                                _json(change.current_value)
                                if change.current_value is not None
                                else None
                            ),
                            _json(safe_metadata),
                            event_id,
                        ],
                    )
                    aggregate_change_event_count += 1

                    dependencies = connection.execute(
                        """
                        SELECT dependency_id, artifact_type, artifact_key,
                               analysis_type, analysis_version
                        FROM artifact_dependency
                        WHERE dependency_type = 'source_endpoint'
                          AND dependency_key = ?
                          AND active = TRUE
                        ORDER BY dependency_id
                        """,
                        [contract.endpoint_code],
                    ).fetchall()
                    for dependency in dependencies:
                        dependency_id = str(dependency[0])
                        artifact_type = str(dependency[1])
                        artifact_key = str(dependency[2])
                        analysis_type = str(dependency[3])
                        analysis_version = str(dependency[4])
                        dedupe_key = _sha256_text(
                            f"{OBSERVATORY_VERSION}\0reanalysis\0{event_id}\0{dependency_id}"
                        )
                        request_id = _sha256_text(
                            f"{OBSERVATORY_VERSION}\0request\0{dedupe_key}"
                        )
                        target_scope = {
                            "source_code": contract.source_code,
                            "endpoint_code": contract.endpoint_code,
                            "artifact_type": artifact_type,
                            "artifact_key": artifact_key,
                            "schema_cycle_aggregated": True,
                        }
                        connection.execute(
                            """
                            INSERT INTO reanalysis_request (
                                request_id, reason_event_id, dependency_id, artifact_type,
                                artifact_key, analysis_type, requested_analysis_version,
                                target_scope_json, status, dedupe_key, metadata_json
                            ) SELECT ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?
                            WHERE NOT EXISTS (
                                SELECT 1 FROM reanalysis_request WHERE dedupe_key = ?
                            )
                            """,
                            [
                                request_id,
                                event_id,
                                dependency_id,
                                artifact_type,
                                artifact_key,
                                analysis_type,
                                analysis_version,
                                _json(target_scope),
                                dedupe_key,
                                _json(
                                    {
                                        "change_type": change.change_type,
                                        "schema_cycle_aggregated": True,
                                    }
                                ),
                                dedupe_key,
                            ],
                        )
                        aggregate_reanalysis_request_count += 1

            connection.execute("COMMIT")
        except Exception:
            connection.execute("ROLLBACK")
            raise

    return ProfileSchemaCycleSummary(
        endpoint_code=contract.endpoint_code,
        profile_cycle_count=profile_cycle_count,
        member_capture_count=member_capture_count,
        superseded_member_event_count=superseded_member_event_count,
        superseded_reanalysis_request_count=superseded_reanalysis_request_count,
        aggregate_change_event_count=aggregate_change_event_count,
        aggregate_reanalysis_request_count=aggregate_reanalysis_request_count,
    )


__all__ = [
    "PROFILE_SCHEMA_CYCLE_VERSION",
    "ProfileSchemaCycleSummary",
    "aggregate_profile_schema_observations",
    "merge_schema_snapshots",
]
