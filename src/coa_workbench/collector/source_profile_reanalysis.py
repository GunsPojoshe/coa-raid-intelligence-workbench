from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from coa_workbench.collector.source_observatory import OBSERVATORY_VERSION
from coa_workbench.storage.migrations import apply_migrations

SOURCE_PROFILE_REANALYSIS_VERSION = "source-query-profile-reanalysis-v1"
_GLOBAL_CHANGE_TYPES = frozenset({"request_contract_changed"})


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _capture_profile_key(connection: Any, *, capture_id: str, endpoint_code: str) -> str:
    row = connection.execute(
        """
        SELECT metadata_json
        FROM source_capture
        WHERE capture_id = ?
          AND endpoint_code = ?
        """,
        [capture_id, endpoint_code],
    ).fetchone()
    if row is None or row[0] is None:
        raise RuntimeError(
            f"profile-scoped source capture {capture_id!r} has no observation metadata"
        )
    metadata = json.loads(str(row[0]))
    if not isinstance(metadata, dict):
        raise RuntimeError("profile-scoped source capture metadata must be an object")
    profile_key = metadata.get("observation_profile_key")
    if not isinstance(profile_key, str) or not profile_key:
        raise RuntimeError(
            f"profile-scoped source capture for {endpoint_code!r} has no private profile key"
        )
    return profile_key


@dataclass(frozen=True, slots=True)
class ProfileReanalysisResolution:
    profile_dependency_count: int
    eligible_event_count: int
    profile_match_count: int
    global_match_count: int
    created_request_count: int
    existing_request_count: int
    endpoint_count: int

    def public_summary(self) -> dict[str, Any]:
        return {
            "resolver_version": SOURCE_PROFILE_REANALYSIS_VERSION,
            "profile_dependency_count": self.profile_dependency_count,
            "eligible_event_count": self.eligible_event_count,
            "profile_match_count": self.profile_match_count,
            "global_match_count": self.global_match_count,
            "created_request_count": self.created_request_count,
            "existing_request_count": self.existing_request_count,
            "endpoint_count": self.endpoint_count,
            "profile_values_included": False,
            "profile_fingerprints_included": False,
            "request_urls_included": False,
        }


def resolve_profile_reanalysis_requests(
    database_path: Path,
    migrations_dir: Path,
    *,
    endpoint_codes: Iterable[str] = (),
) -> ProfileReanalysisResolution:
    """Reconcile query-profile dependencies against newly observed open source changes.

    Schema/profile-local changes only invalidate artifacts built from the same private reviewed query
    profile. Request-contract changes are endpoint-global and intentionally fan out to every active
    profile dependency. Events older than dependency registration cannot back-trigger new artifacts.
    """
    apply_migrations(database_path, migrations_dir)
    requested_endpoints = set(endpoint_codes)

    import duckdb

    profile_dependency_count = 0
    eligible_event_count = 0
    profile_match_count = 0
    global_match_count = 0
    created_request_count = 0
    existing_request_count = 0
    resolved_endpoints: set[str] = set()

    with duckdb.connect(str(database_path)) as connection:
        dependencies = connection.execute(
            """
            SELECT dependency_id, artifact_type, artifact_key, analysis_type,
                   analysis_version, dependency_key, dependency_version, registered_at
            FROM artifact_dependency
            WHERE dependency_type = 'source_endpoint_profile'
              AND active = TRUE
            ORDER BY dependency_id
            """
        ).fetchall()
        for dependency in dependencies:
            endpoint_code = str(dependency[5])
            if requested_endpoints and endpoint_code not in requested_endpoints:
                continue
            dependency_version = dependency[6]
            if not dependency_version:
                raise RuntimeError("profile-scoped source dependency has no private profile key")

            profile_dependency_count += 1
            resolved_endpoints.add(endpoint_code)
            events = connection.execute(
                """
                SELECT event_id, capture_id, change_type, source_code
                FROM source_change_event
                WHERE endpoint_code = ?
                  AND status = 'open'
                  AND observed_at >= ?
                ORDER BY observed_at, event_id
                """,
                [endpoint_code, dependency[7]],
            ).fetchall()
            eligible_event_count += len(events)

            for event_id_raw, capture_id_raw, change_type_raw, source_code_raw in events:
                event_id = str(event_id_raw)
                capture_id = str(capture_id_raw)
                change_type = str(change_type_raw)
                global_change = change_type in _GLOBAL_CHANGE_TYPES
                if global_change:
                    global_match_count += 1
                else:
                    event_profile = _capture_profile_key(
                        connection,
                        capture_id=capture_id,
                        endpoint_code=endpoint_code,
                    )
                    if event_profile != str(dependency_version):
                        continue
                    profile_match_count += 1

                dependency_id = str(dependency[0])
                dedupe_key = _sha256_text(
                    f"{OBSERVATORY_VERSION}\0reanalysis\0{event_id}\0{dependency_id}"
                )
                request_id = _sha256_text(
                    f"{OBSERVATORY_VERSION}\0request\0{dedupe_key}"
                )
                existing = connection.execute(
                    "SELECT 1 FROM reanalysis_request WHERE dedupe_key = ?",
                    [dedupe_key],
                ).fetchone()
                if existing is not None:
                    existing_request_count += 1
                    continue

                target_scope = {
                    "source_code": str(source_code_raw),
                    "endpoint_code": endpoint_code,
                    "artifact_type": str(dependency[1]),
                    "artifact_key": str(dependency[2]),
                    "profile_scoped": not global_change,
                }
                connection.execute(
                    """
                    INSERT INTO reanalysis_request (
                        request_id, reason_event_id, dependency_id, artifact_type,
                        artifact_key, analysis_type, requested_analysis_version,
                        target_scope_json, status, dedupe_key, metadata_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?)
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
                                "change_type": change_type,
                                "profile_resolver_version": SOURCE_PROFILE_REANALYSIS_VERSION,
                                "profile_fingerprint_public": False,
                                "global_change": global_change,
                            }
                        ),
                    ],
                )
                created_request_count += 1

    return ProfileReanalysisResolution(
        profile_dependency_count=profile_dependency_count,
        eligible_event_count=eligible_event_count,
        profile_match_count=profile_match_count,
        global_match_count=global_match_count,
        created_request_count=created_request_count,
        existing_request_count=existing_request_count,
        endpoint_count=len(resolved_endpoints),
    )


__all__ = [
    "SOURCE_PROFILE_REANALYSIS_VERSION",
    "ProfileReanalysisResolution",
    "resolve_profile_reanalysis_requests",
]
