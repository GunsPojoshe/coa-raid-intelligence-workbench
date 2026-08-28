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
from coa_workbench.collector.source_scope import scope_fingerprint_from_url
from coa_workbench.storage.migrations import apply_migrations

SCOPE_SCHEMA_CYCLE_VERSION = "scope-schema-cycle-v1"
_MEMBER_SCHEMA_CHANGE_TYPES = (
    "schema_changed",
    "field_added",
    "field_removed",
    "field_type_changed",
    "new_dimension_value",
)


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _utc_naive(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value
    return value.astimezone(timezone.utc).replace(tzinfo=None)


def _snapshot_from_parts(
    root_type: Any,
    path_types_json: Any,
    dimension_values_json: Any,
    scan_truncated: Any,
) -> SchemaSnapshot:
    path_types = normalize_path_types(
        {
            str(path): tuple(str(item) for item in values)
            for path, values in json.loads(str(path_types_json)).items()
        }
    )
    dimensions = {
        str(name): tuple(str(item) for item in values)
        for name, values in json.loads(str(dimension_values_json)).items()
    }
    return SchemaSnapshot(
        schema_fingerprint=_sha256_text(_json(path_types)),
        root_type=str(root_type),
        path_types=path_types,
        dimension_values=dimensions,
        scan_truncated=bool(scan_truncated),
    )


def _snapshot_from_row(row: Sequence[Any]) -> SchemaSnapshot:
    return _snapshot_from_parts(row[1], row[2], row[3], row[4])


def _merge_schema_snapshots(snapshots: Iterable[SchemaSnapshot]) -> SchemaSnapshot:
    prepared = tuple(snapshots)
    if not prepared:
        raise ValueError("scope schema cycle requires at least one schema snapshot")

    root_types = {snapshot.root_type for snapshot in prepared}
    if len(root_types) != 1:
        raise ValueError(
            f"scope schema cycle cannot merge different root types: {sorted(root_types)}"
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


def _scope_partition_key(
    contract: ReviewedGetContract,
    *,
    scope_key: str,
    profile_key: str | None,
) -> str:
    payload = {
        "version": SCOPE_SCHEMA_CYCLE_VERSION,
        "source_code": contract.source_code,
        "endpoint_code": contract.endpoint_code,
        "scope_key": scope_key,
        "profile_key": profile_key,
    }
    return _sha256_text(
        f"{SCOPE_SCHEMA_CYCLE_VERSION}\0partition\0{_json(payload)}"
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
    return _sha256_text(f"{SCOPE_SCHEMA_CYCLE_VERSION}\0event\0{seed}")


def _capture_scope_key(
    connection: Any,
    *,
    capture_id: str,
    contract: ReviewedGetContract,
    scope_path_keys: tuple[str, ...],
) -> str:
    row = connection.execute(
        """
        SELECT rfo.request_url_sanitized
        FROM source_capture AS sc
        JOIN raw_fetch_observation AS rfo
          ON rfo.observation_id = sc.raw_observation_id
        WHERE sc.capture_id = ?
          AND sc.endpoint_code = ?
        """,
        [capture_id, contract.endpoint_code],
    ).fetchone()
    if row is None or not row[0]:
        raise RuntimeError(
            f"source capture {capture_id!r} has no sanitized request URL for scope aggregation"
        )
    return scope_fingerprint_from_url(
        source_code=contract.source_code,
        route_template=contract.route_template,
        scope_path_keys=scope_path_keys,
        request_url=str(row[0]),
    )


def _legacy_cycle_scope_key(
    connection: Any,
    *,
    member_capture_ids_json: Any,
    contract: ReviewedGetContract,
    scope_path_keys: tuple[str, ...],
) -> str:
    member_ids = [str(value) for value in json.loads(str(member_capture_ids_json))]
    if not member_ids:
        raise RuntimeError("legacy profile schema cycle has no member captures")
    scopes = {
        _capture_scope_key(
            connection,
            capture_id=capture_id,
            contract=contract,
            scope_path_keys=scope_path_keys,
        )
        for capture_id in member_ids
    }
    if len(scopes) != 1:
        raise RuntimeError("legacy profile schema cycle spans multiple reviewed path scopes")
    return next(iter(scopes))


def _previous_scope_snapshot(
    connection: Any,
    *,
    contract: ReviewedGetContract,
    scope_path_keys: tuple[str, ...],
    scope_key: str,
    profile_key: str | None,
    before_at: datetime,
) -> SchemaSnapshot | None:
    partition_key = _scope_partition_key(
        contract,
        scope_key=scope_key,
        profile_key=profile_key,
    )
    canonical = connection.execute(
        """
        SELECT root_type, path_types_json, dimension_values_json, scan_truncated
        FROM source_profile_schema_cycle
        WHERE endpoint_code = ?
          AND observation_profile_key = ?
          AND COALESCE(
                json_extract_string(metadata_json, '$.scope_schema_cycle_aggregated'),
                'false'
              ) = 'true'
          AND observed_at < ?
        ORDER BY observed_at DESC, cycle_snapshot_id DESC
        LIMIT 1
        """,
        [contract.endpoint_code, partition_key, before_at],
    ).fetchone()
    if canonical is not None:
        return _snapshot_from_parts(canonical[0], canonical[1], canonical[2], canonical[3])

    if profile_key is not None:
        legacy_rows = connection.execute(
            """
            SELECT root_type, path_types_json, dimension_values_json, scan_truncated,
                   member_capture_ids_json
            FROM source_profile_schema_cycle
            WHERE endpoint_code = ?
              AND observation_profile_key = ?
              AND COALESCE(
                    json_extract_string(metadata_json, '$.scope_schema_cycle_aggregated'),
                    'false'
                  ) <> 'true'
              AND observed_at < ?
            ORDER BY observed_at DESC, cycle_snapshot_id DESC
            """,
            [contract.endpoint_code, profile_key, before_at],
        ).fetchall()
        for row in legacy_rows:
            if (
                _legacy_cycle_scope_key(
                    connection,
                    member_capture_ids_json=row[4],
                    contract=contract,
                    scope_path_keys=scope_path_keys,
                )
                == scope_key
            ):
                return _snapshot_from_parts(row[0], row[1], row[2], row[3])
        return None

    legacy_rows = connection.execute(
        """
        SELECT capture_id, root_type, path_types_json, dimension_values_json,
               scan_truncated
        FROM source_schema_snapshot
        WHERE endpoint_code = ?
          AND json_extract_string(metadata_json, '$.observation_profile_key') IS NULL
          AND observed_at < ?
        ORDER BY observed_at DESC, snapshot_id DESC
        """,
        [contract.endpoint_code, before_at],
    ).fetchall()
    for row in legacy_rows:
        if (
            _capture_scope_key(
                connection,
                capture_id=str(row[0]),
                contract=contract,
                scope_path_keys=scope_path_keys,
            )
            == scope_key
        ):
            return _snapshot_from_parts(row[1], row[2], row[3], row[4])
    return None


def _supersede_event_ids(
    connection: Any,
    event_ids: list[str],
    *,
    event_status: str,
    request_status: str,
) -> tuple[int, int]:
    if not event_ids:
        return 0, 0
    placeholders = ", ".join("?" for _ in event_ids)
    linked = connection.execute(
        f"""
        SELECT request_id, status
        FROM reanalysis_request
        WHERE reason_event_id IN ({placeholders})
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
            "refusing to supersede scoped schema events after downstream reanalysis has started"
        )
    request_ids = [str(row[0]) for row in linked]
    if request_ids:
        request_placeholders = ", ".join("?" for _ in request_ids)
        connection.execute(
            f"""
            UPDATE reanalysis_request
            SET status = ?
            WHERE request_id IN ({request_placeholders})
            """,
            [request_status, *request_ids],
        )
    connection.execute(
        f"""
        UPDATE source_change_event
        SET status = ?
        WHERE event_id IN ({placeholders})
        """,
        [event_status, *event_ids],
    )
    return len(event_ids), len(request_ids)


@dataclass(frozen=True, slots=True)
class ScopeSchemaCycleSummary:
    endpoint_code: str
    scope_cycle_count: int
    member_capture_count: int
    superseded_member_event_count: int
    superseded_legacy_profile_event_count: int
    superseded_reanalysis_request_count: int
    aggregate_change_event_count: int
    aggregate_reanalysis_request_count: int

    def public_summary(self) -> dict[str, Any]:
        return {
            "endpoint_code": self.endpoint_code,
            "scope_cycle_count": self.scope_cycle_count,
            "member_capture_count": self.member_capture_count,
            "superseded_member_event_count": self.superseded_member_event_count,
            "superseded_legacy_profile_event_count": (
                self.superseded_legacy_profile_event_count
            ),
            "superseded_reanalysis_request_count": (
                self.superseded_reanalysis_request_count
            ),
            "aggregate_change_event_count": self.aggregate_change_event_count,
            "aggregate_reanalysis_request_count": (
                self.aggregate_reanalysis_request_count
            ),
            "strategy": SCOPE_SCHEMA_CYCLE_VERSION,
            "scope_values_included": False,
            "scope_hashes_included": False,
            "profile_values_included": False,
            "profile_hashes_included": False,
            "member_capture_ids_included": False,
            "schema_fingerprints_included": False,
            "dimension_values_included": False,
        }


def aggregate_scope_schema_observations(
    database_path: Path,
    migrations_dir: Path,
    *,
    contract: ReviewedGetContract,
    scope_path_keys: Iterable[str],
    observations: Iterable[Any],
    metadata: Mapping[str, Any] | None = None,
) -> ScopeSchemaCycleSummary:
    """Build one schema baseline per reviewed path scope and optional response profile.

    Exact raw captures and source_schema_snapshot rows remain immutable. Legacy per-response
    schema events and legacy profile-cycle events associated with the same member captures are
    superseded only while their downstream requests are still pending. A new aggregate event is
    emitted only against the previous schema from the same reviewed path scope.
    """
    scope_keys = tuple(str(value) for value in scope_path_keys)
    if not scope_keys:
        raise ValueError("scope schema cycle requires scope_path_keys")

    apply_migrations(database_path, migrations_dir)

    capture_ids = sorted(
        {
            str(item.source_observation.source_capture_id)
            for item in observations
            if getattr(item, "source_observation", None) is not None
        }
    )
    if not capture_ids:
        return ScopeSchemaCycleSummary(
            endpoint_code=contract.endpoint_code,
            scope_cycle_count=0,
            member_capture_count=0,
            superseded_member_event_count=0,
            superseded_legacy_profile_event_count=0,
            superseded_reanalysis_request_count=0,
            aggregate_change_event_count=0,
            aggregate_reanalysis_request_count=0,
        )

    import duckdb

    placeholders = ", ".join("?" for _ in capture_ids)
    member_change_placeholders = ", ".join("?" for _ in _MEMBER_SCHEMA_CHANGE_TYPES)
    scope_cycle_count = 0
    member_capture_count = 0
    superseded_member_event_count = 0
    superseded_legacy_profile_event_count = 0
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
                "scope schema cycle could not resolve every member source schema snapshot"
            )

        groups: dict[tuple[str, str | None], list[tuple[Any, ...]]] = {}
        for row in rows:
            capture_id = str(row[0])
            scope_key = _capture_scope_key(
                connection,
                capture_id=capture_id,
                contract=contract,
                scope_path_keys=scope_keys,
            )
            profile_key = str(row[6]) if row[6] else None
            groups.setdefault((scope_key, profile_key), []).append(row)

        connection.execute("BEGIN TRANSACTION")
        try:
            for scope_key, profile_key in sorted(
                groups,
                key=lambda item: (item[0], "" if item[1] is None else item[1]),
            ):
                group_rows = groups[(scope_key, profile_key)]
                member_ids = sorted(str(row[0]) for row in group_rows)
                member_capture_count += len(member_ids)
                aggregate = _merge_schema_snapshots(
                    _snapshot_from_row(row) for row in group_rows
                )
                observed_at = max(_utc_naive(row[5]) for row in group_rows)
                first_observed_at = min(_utc_naive(row[5]) for row in group_rows)
                partition_key = _scope_partition_key(
                    contract,
                    scope_key=scope_key,
                    profile_key=profile_key,
                )
                cycle_fingerprint = _sha256_text(
                    _json(
                        {
                            "version": SCOPE_SCHEMA_CYCLE_VERSION,
                            "contract_id": contract.contract_id,
                            "partition_key": partition_key,
                            "member_capture_ids": member_ids,
                        }
                    )
                )
                cycle_snapshot_id = _sha256_text(
                    f"{SCOPE_SCHEMA_CYCLE_VERSION}\0snapshot\0{cycle_fingerprint}"
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
                      AND COALESCE(
                            json_extract_string(metadata_json, '$.scope_schema_cycle_aggregated'),
                            'false'
                          ) <> 'true'
                    ORDER BY event_id
                    """,
                    [*member_ids, *_MEMBER_SCHEMA_CHANGE_TYPES],
                ).fetchall()
                member_event_ids = [str(row[0]) for row in member_events]
                removed_events, removed_requests = _supersede_event_ids(
                    connection,
                    member_event_ids,
                    event_status="superseded_scope_schema_cycle_aggregation",
                    request_status="superseded_scope_schema_cycle_aggregation",
                )
                superseded_member_event_count += removed_events
                superseded_reanalysis_request_count += removed_requests

                legacy_profile_events = connection.execute(
                    f"""
                    SELECT event_id
                    FROM source_change_event
                    WHERE capture_id IN ({group_placeholders})
                      AND status = 'open'
                      AND change_type IN ({member_change_placeholders})
                      AND COALESCE(
                            json_extract_string(metadata_json, '$.schema_cycle_aggregated'),
                            'false'
                          ) = 'true'
                      AND COALESCE(
                            json_extract_string(metadata_json, '$.scope_schema_cycle_aggregated'),
                            'false'
                          ) <> 'true'
                    ORDER BY event_id
                    """,
                    [*member_ids, *_MEMBER_SCHEMA_CHANGE_TYPES],
                ).fetchall()
                legacy_event_ids = [str(row[0]) for row in legacy_profile_events]
                removed_events, removed_requests = _supersede_event_ids(
                    connection,
                    legacy_event_ids,
                    event_status="superseded_scope_schema_cycle_aggregation",
                    request_status="superseded_scope_schema_cycle_aggregation",
                )
                superseded_legacy_profile_event_count += removed_events
                superseded_reanalysis_request_count += removed_requests

                if cycle_exists is not None:
                    continue

                previous = _previous_scope_snapshot(
                    connection,
                    contract=contract,
                    scope_path_keys=scope_keys,
                    scope_key=scope_key,
                    profile_key=profile_key,
                    before_at=first_observed_at,
                )
                changes = (
                    diff_schema_snapshots(previous, aggregate)
                    if previous is not None
                    else ()
                )

                safe_metadata = {
                    "scope_schema_cycle_version": SCOPE_SCHEMA_CYCLE_VERSION,
                    "scope_schema_cycle_aggregated": True,
                    "scope_path_keys": list(scope_keys),
                    "schema_profile_keys": list(contract.schema_profile_keys),
                    "response_profiled": profile_key is not None,
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
                        partition_key,
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
                    SET schema_fingerprint = ?, last_verified_at = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE endpoint_code = ?
                    """,
                    [
                        aggregate.schema_fingerprint,
                        observed_at,
                        contract.endpoint_code,
                    ],
                )
                scope_cycle_count += 1

                representative_capture_id = max(
                    group_rows,
                    key=lambda row: (_utc_naive(row[5]), str(row[0])),
                )[0]
                for change in changes:
                    event_id = _cycle_event_id(cycle_snapshot_id, change)
                    existing_event = connection.execute(
                        "SELECT 1 FROM source_change_event WHERE event_id = ?",
                        [event_id],
                    ).fetchone()
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
                    if existing_event is None:
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
                        dedupe_key = _sha256_text(
                            f"{OBSERVATORY_VERSION}\0reanalysis\0{event_id}\0{dependency_id}"
                        )
                        request_id = _sha256_text(
                            f"{OBSERVATORY_VERSION}\0request\0{dedupe_key}"
                        )
                        existing_request = connection.execute(
                            "SELECT 1 FROM reanalysis_request WHERE dedupe_key = ?",
                            [dedupe_key],
                        ).fetchone()
                        target_scope = {
                            "source_code": contract.source_code,
                            "endpoint_code": contract.endpoint_code,
                            "artifact_type": str(dependency[1]),
                            "artifact_key": str(dependency[2]),
                            "scope_path_keys": list(scope_keys),
                            "scope_schema_cycle_aggregated": True,
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
                                str(dependency[1]),
                                str(dependency[2]),
                                str(dependency[3]),
                                str(dependency[4]),
                                _json(target_scope),
                                dedupe_key,
                                _json(
                                    {
                                        "change_type": change.change_type,
                                        "scope_schema_cycle_aggregated": True,
                                        "scope_path_keys": list(scope_keys),
                                    }
                                ),
                                dedupe_key,
                            ],
                        )
                        if existing_request is None:
                            aggregate_reanalysis_request_count += 1

            connection.execute("COMMIT")
        except Exception:
            connection.execute("ROLLBACK")
            raise

    return ScopeSchemaCycleSummary(
        endpoint_code=contract.endpoint_code,
        scope_cycle_count=scope_cycle_count,
        member_capture_count=member_capture_count,
        superseded_member_event_count=superseded_member_event_count,
        superseded_legacy_profile_event_count=superseded_legacy_profile_event_count,
        superseded_reanalysis_request_count=superseded_reanalysis_request_count,
        aggregate_change_event_count=aggregate_change_event_count,
        aggregate_reanalysis_request_count=aggregate_reanalysis_request_count,
    )


__all__ = [
    "SCOPE_SCHEMA_CYCLE_VERSION",
    "ScopeSchemaCycleSummary",
    "aggregate_scope_schema_observations",
]
