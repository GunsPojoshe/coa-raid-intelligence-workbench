from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from coa_workbench.collector.source_observatory import register_artifact_dependency
from coa_workbench.collector.source_registry import SourceRegistry
from coa_workbench.collector.source_scope import scope_fingerprint_from_url
from coa_workbench.storage.current_report_observations import (
    CURRENT_REPORT_PERSISTENCE_VERSION,
)
from coa_workbench.storage.migrations import apply_migrations

_CURRENT_REPORT_SOURCE_ENDPOINTS = (
    "report_detail_api",
    "report_encounters_api",
    "report_combatants_roster_api",
)


@dataclass(frozen=True, slots=True)
class CurrentReportDependencyRegistration:
    artifact_type: str
    analysis_type: str
    analysis_version: str
    dependency_count: int
    endpoint_codes: tuple[str, ...]
    scope_path_keys: tuple[str, ...]

    def public_summary(self) -> dict[str, Any]:
        return {
            "artifact_type": self.artifact_type,
            "analysis_type": self.analysis_type,
            "analysis_version": self.analysis_version,
            "dependency_type": "source_endpoint_scope",
            "dependency_count": self.dependency_count,
            "endpoint_codes": list(self.endpoint_codes),
            "scope_path_keys": list(self.scope_path_keys),
            "scope_values_included": False,
            "scope_fingerprints_included": False,
            "source_capture_ids_included": False,
        }


def register_current_report_scoped_dependencies(
    database_path: Path,
    migrations_dir: Path,
    *,
    registry: SourceRegistry,
    artifact_key: str,
) -> CurrentReportDependencyRegistration:
    """Bind one persisted current-report artifact only to its reviewed private report path scope."""
    apply_migrations(database_path, migrations_dir)

    import duckdb

    with duckdb.connect(str(database_path), read_only=True) as connection:
        persistence = connection.execute(
            """
            SELECT source_batch_hashes_json
            FROM parser_slice_persistence_run
            WHERE reconstruction_sha256 = ?
              AND reconstruction_version = ?
              AND status = 'completed'
            """,
            [artifact_key, CURRENT_REPORT_PERSISTENCE_VERSION],
        ).fetchall()
        if len(persistence) != 1:
            raise ValueError(
                "current report scoped dependency registration requires exactly one completed "
                "persistence run"
            )
        source_identity = json.loads(str(persistence[0][0]))
        if not isinstance(source_identity, dict):
            raise ValueError("current report persistence source identity must be an object")
        if set(source_identity) != set(_CURRENT_REPORT_SOURCE_ENDPOINTS):
            raise ValueError(
                "current report persistence source endpoint set changed before scoped dependency "
                "registration"
            )

        analysis_rows = connection.execute(
            """
            SELECT artifact_type, analysis_type, analysis_version
            FROM analysis_run
            WHERE artifact_key = ?
              AND analysis_version = ?
              AND status = 'completed'
            ORDER BY finished_at DESC, analysis_run_id DESC
            """,
            [artifact_key, CURRENT_REPORT_PERSISTENCE_VERSION],
        ).fetchall()
        if len(analysis_rows) != 1:
            raise ValueError(
                "current report scoped dependency registration requires exactly one completed "
                "analysis run"
            )
        artifact_type = str(analysis_rows[0][0])
        analysis_type = str(analysis_rows[0][1])
        analysis_version = str(analysis_rows[0][2])

        scope_fingerprints: dict[str, str] = {}
        scope_key_sets: set[tuple[str, ...]] = set()
        for endpoint_code in _CURRENT_REPORT_SOURCE_ENDPOINTS:
            route = registry.route(endpoint_code)
            if not route.route_template or not route.scope_path_keys:
                raise ValueError(
                    f"current report source route {endpoint_code!r} has no reviewed path scope"
                )
            scope_key_sets.add(tuple(route.scope_path_keys))
            row = source_identity[endpoint_code]
            if not isinstance(row, dict) or not row.get("capture_id"):
                raise ValueError(
                    f"current report persistence source identity lacks capture_id for {endpoint_code}"
                )
            capture = connection.execute(
                """
                SELECT rfo.request_url_sanitized
                FROM source_capture AS sc
                JOIN raw_fetch_observation AS rfo
                  ON rfo.observation_id = sc.raw_observation_id
                WHERE sc.capture_id = ?
                  AND sc.endpoint_code = ?
                """,
                [str(row["capture_id"]), endpoint_code],
            ).fetchone()
            if capture is None or not capture[0]:
                raise ValueError(
                    f"current report source capture for {endpoint_code} has no sanitized request URL"
                )
            scope_fingerprints[endpoint_code] = scope_fingerprint_from_url(
                source_code=registry.source_code,
                route_template=route.route_template,
                scope_path_keys=route.scope_path_keys,
                request_url=str(capture[0]),
            )

    if len(scope_key_sets) != 1:
        raise ValueError("current report source routes do not share one reviewed scope-key contract")
    if len(set(scope_fingerprints.values())) != 1:
        raise ValueError("current report source captures do not resolve to the same private report scope")
    scope_fingerprint = next(iter(scope_fingerprints.values()))
    scope_path_keys = next(iter(scope_key_sets))

    for endpoint_code in _CURRENT_REPORT_SOURCE_ENDPOINTS:
        register_artifact_dependency(
            database_path,
            migrations_dir,
            artifact_type=artifact_type,
            artifact_key=artifact_key,
            analysis_type=analysis_type,
            analysis_version=analysis_version,
            dependency_type="source_endpoint_scope",
            dependency_key=endpoint_code,
            dependency_version=scope_fingerprint,
            metadata={
                "scope_path_keys": list(scope_path_keys),
                "scope_values_included": False,
                "scope_fingerprint_public": False,
            },
        )

    return CurrentReportDependencyRegistration(
        artifact_type=artifact_type,
        analysis_type=analysis_type,
        analysis_version=analysis_version,
        dependency_count=len(_CURRENT_REPORT_SOURCE_ENDPOINTS),
        endpoint_codes=_CURRENT_REPORT_SOURCE_ENDPOINTS,
        scope_path_keys=scope_path_keys,
    )


__all__ = [
    "CurrentReportDependencyRegistration",
    "register_current_report_scoped_dependencies",
]
