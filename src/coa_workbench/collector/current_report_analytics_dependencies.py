from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from coa_workbench.collector.source_observatory import register_artifact_dependency
from coa_workbench.collector.source_registry import SourceRegistry
from coa_workbench.collector.source_scope import scope_fingerprint_from_url
from coa_workbench.storage.current_report_analytics import (
    CURRENT_REPORT_ANALYTICS_PERSISTENCE_VERSION,
)
from coa_workbench.storage.migrations import apply_migrations

_CURRENT_ANALYTICS_ENDPOINTS = (
    "report_detail_api",
    "report_encounters_api",
    "report_combatants_roster_api",
    "report_encounter_throughput_timeline_api",
    "report_character_damage_taken_abilities_api",
    "report_character_spell_healing_api",
)


@dataclass(frozen=True, slots=True)
class CurrentReportAnalyticsDependencyRegistration:
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


def register_current_report_analytics_scoped_dependencies(
    database_path: Path,
    migrations_dir: Path,
    *,
    registry: SourceRegistry,
    artifact_key: str,
) -> CurrentReportAnalyticsDependencyRegistration:
    """Bind one analytics read model to all reviewed source families used to derive it."""
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
            [artifact_key, CURRENT_REPORT_ANALYTICS_PERSISTENCE_VERSION],
        ).fetchall()
        if len(persistence) != 1:
            raise ValueError(
                "current report analytics dependency registration requires exactly one completed "
                "persistence run"
            )
        source_identity = json.loads(str(persistence[0][0]))
        if not isinstance(source_identity, dict):
            raise ValueError("current report analytics source identity must be an object")
        if set(source_identity) != set(_CURRENT_ANALYTICS_ENDPOINTS):
            raise ValueError(
                "current report analytics source endpoint set changed before scoped dependency "
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
            [artifact_key, CURRENT_REPORT_ANALYTICS_PERSISTENCE_VERSION],
        ).fetchall()
        if len(analysis_rows) != 1:
            raise ValueError(
                "current report analytics dependency registration requires exactly one completed "
                "analysis run"
            )
        artifact_type = str(analysis_rows[0][0])
        analysis_type = str(analysis_rows[0][1])
        analysis_version = str(analysis_rows[0][2])

        scope_fingerprints: dict[str, set[str]] = {}
        scope_key_sets: set[tuple[str, ...]] = set()
        for endpoint_code in _CURRENT_ANALYTICS_ENDPOINTS:
            route = registry.route(endpoint_code)
            if not route.route_template or not route.scope_path_keys:
                raise ValueError(
                    f"analytics source route {endpoint_code!r} has no reviewed path scope"
                )
            scope_key_sets.add(tuple(route.scope_path_keys))
            raw_rows = source_identity[endpoint_code]
            if not isinstance(raw_rows, list) or not raw_rows:
                raise ValueError(
                    f"analytics persistence source identity lacks capture list for {endpoint_code}"
                )
            endpoint_scopes: set[str] = set()
            for raw_row in raw_rows:
                if not isinstance(raw_row, dict) or not raw_row.get("capture_id"):
                    raise ValueError(
                        f"analytics persistence source identity lacks capture_id for {endpoint_code}"
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
                    [str(raw_row["capture_id"]), endpoint_code],
                ).fetchone()
                if capture is None or not capture[0]:
                    raise ValueError(
                        f"analytics source capture for {endpoint_code} has no sanitized request URL"
                    )
                endpoint_scopes.add(
                    scope_fingerprint_from_url(
                        source_code=registry.source_code,
                        route_template=route.route_template,
                        scope_path_keys=route.scope_path_keys,
                        request_url=str(capture[0]),
                    )
                )
            if len(endpoint_scopes) != 1:
                raise ValueError(
                    f"analytics source captures for {endpoint_code} span multiple private report scopes"
                )
            scope_fingerprints[endpoint_code] = endpoint_scopes

    if len(scope_key_sets) != 1:
        raise ValueError("analytics source routes do not share one reviewed scope-key contract")
    flattened_scopes = {next(iter(values)) for values in scope_fingerprints.values()}
    if len(flattened_scopes) != 1:
        raise ValueError("analytics source captures do not resolve to one private report scope")
    scope_fingerprint = next(iter(flattened_scopes))
    scope_path_keys = next(iter(scope_key_sets))

    for endpoint_code in _CURRENT_ANALYTICS_ENDPOINTS:
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

    return CurrentReportAnalyticsDependencyRegistration(
        artifact_type=artifact_type,
        analysis_type=analysis_type,
        analysis_version=analysis_version,
        dependency_count=len(_CURRENT_ANALYTICS_ENDPOINTS),
        endpoint_codes=_CURRENT_ANALYTICS_ENDPOINTS,
        scope_path_keys=scope_path_keys,
    )


__all__ = [
    "CurrentReportAnalyticsDependencyRegistration",
    "register_current_report_analytics_scoped_dependencies",
]
