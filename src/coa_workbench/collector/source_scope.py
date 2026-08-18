from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping
from urllib.parse import unquote, urlsplit

from coa_workbench.collector.source_observatory import OBSERVATORY_VERSION
from coa_workbench.collector.source_registry import SourceRegistry, SourceRoute
from coa_workbench.storage.migrations import apply_migrations

SOURCE_SCOPE_VERSION = "source-path-scope-v1"
_PATH_PARAMETER = re.compile(r"\{([A-Za-z_][A-Za-z0-9_]*)\}")


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def route_path_parameters(route_template: str, request_url: str) -> dict[str, str]:
    pieces: list[str] = []
    cursor = 0
    names: list[str] = []
    for match in _PATH_PARAMETER.finditer(route_template):
        name = match.group(1)
        if name in names:
            raise ValueError(f"route template repeats path parameter {name!r}")
        names.append(name)
        pieces.append(re.escape(route_template[cursor : match.start()]))
        pieces.append(f"(?P<{name}>[^/]+)")
        cursor = match.end()
    pieces.append(re.escape(route_template[cursor:]))
    pattern = re.compile("^" + "".join(pieces) + "$")
    path = urlsplit(request_url).path
    matched = pattern.fullmatch(path)
    if matched is None:
        raise ValueError("request URL path does not match reviewed route template")
    return {name: unquote(value) for name, value in matched.groupdict().items()}


def source_scope_fingerprint(
    *,
    source_code: str,
    scope_values: Mapping[str, str],
) -> str:
    if not scope_values:
        raise ValueError("source scope fingerprint requires at least one path value")
    canonical = {
        "version": SOURCE_SCOPE_VERSION,
        "source_code": source_code,
        "scope_values": {key: str(scope_values[key]) for key in sorted(scope_values)},
    }
    return _sha256_text(_json(canonical))


def scope_fingerprint_from_url(
    *,
    source_code: str,
    route_template: str,
    scope_path_keys: Iterable[str],
    request_url: str,
) -> str:
    scope_keys = tuple(scope_path_keys)
    if not scope_keys:
        raise ValueError("scope_path_keys cannot be empty")
    params = route_path_parameters(route_template, request_url)
    missing = sorted(set(scope_keys) - set(params))
    if missing:
        raise ValueError(f"reviewed scope path keys are absent from route template: {missing}")
    return source_scope_fingerprint(
        source_code=source_code,
        scope_values={key: params[key] for key in scope_keys},
    )


def _capture_scope_fingerprint(
    connection: Any,
    *,
    capture_id: str,
    route: SourceRoute,
    source_code: str,
) -> str:
    if not route.route_template or not route.scope_path_keys:
        raise ValueError(f"source route {route.endpoint_code!r} has no reviewed path scope")
    row = connection.execute(
        """
        SELECT rfo.request_url_sanitized
        FROM source_capture AS sc
        JOIN raw_fetch_observation AS rfo
          ON rfo.observation_id = sc.raw_observation_id
        WHERE sc.capture_id = ?
          AND sc.endpoint_code = ?
        """,
        [capture_id, route.endpoint_code],
    ).fetchone()
    if row is None or not row[0]:
        raise ValueError(
            f"source capture {capture_id!r} has no sanitized request URL for scope resolution"
        )
    return scope_fingerprint_from_url(
        source_code=source_code,
        route_template=route.route_template,
        scope_path_keys=route.scope_path_keys,
        request_url=str(row[0]),
    )


@dataclass(frozen=True, slots=True)
class ScopedReanalysisResolution:
    scoped_dependency_count: int
    eligible_event_count: int
    scope_match_count: int
    created_request_count: int
    existing_request_count: int
    endpoint_count: int

    def public_summary(self) -> dict[str, Any]:
        return {
            "resolver_version": SOURCE_SCOPE_VERSION,
            "scoped_dependency_count": self.scoped_dependency_count,
            "eligible_event_count": self.eligible_event_count,
            "scope_match_count": self.scope_match_count,
            "created_request_count": self.created_request_count,
            "existing_request_count": self.existing_request_count,
            "endpoint_count": self.endpoint_count,
            "scope_values_included": False,
            "scope_fingerprints_included": False,
            "request_urls_included": False,
        }


def resolve_scoped_reanalysis_requests(
    database_path: Path,
    migrations_dir: Path,
    *,
    registry: SourceRegistry,
    endpoint_codes: Iterable[str] = (),
) -> ScopedReanalysisResolution:
    """Reconcile report/path-scoped dependencies against newly observed open source changes.

    Dependencies are eligible only for source events whose upstream observed_at is not older than the
    dependency registration time. This prevents registering a new artifact from back-triggering old
    baseline events. Scope values and their fingerprints remain local/private.
    """
    apply_migrations(database_path, migrations_dir)
    requested_endpoints = set(endpoint_codes)

    import duckdb

    scoped_dependency_count = 0
    eligible_event_count = 0
    scope_match_count = 0
    created_request_count = 0
    existing_request_count = 0
    resolved_endpoints: set[str] = set()

    with duckdb.connect(str(database_path)) as connection:
        dependencies = connection.execute(
            """
            SELECT dependency_id, artifact_type, artifact_key, analysis_type,
                   analysis_version, dependency_key, dependency_version, registered_at
            FROM artifact_dependency
            WHERE dependency_type = 'source_endpoint_scope'
              AND active = TRUE
            ORDER BY dependency_id
            """
        ).fetchall()
        for dependency in dependencies:
            endpoint_code = str(dependency[5])
            if requested_endpoints and endpoint_code not in requested_endpoints:
                continue
            route = registry.route(endpoint_code)
            if not route.scope_path_keys:
                raise RuntimeError(
                    f"active scoped dependency references unscoped route {endpoint_code!r}"
                )
            dependency_version = dependency[6]
            if not dependency_version:
                raise RuntimeError("scoped source dependency has no private scope fingerprint")

            scoped_dependency_count += 1
            resolved_endpoints.add(endpoint_code)
            events = connection.execute(
                """
                SELECT event_id, capture_id, change_type
                FROM source_change_event
                WHERE endpoint_code = ?
                  AND status = 'open'
                  AND observed_at >= ?
                ORDER BY observed_at, event_id
                """,
                [endpoint_code, dependency[7]],
            ).fetchall()
            eligible_event_count += len(events)

            for event_id_raw, capture_id_raw, change_type_raw in events:
                event_id = str(event_id_raw)
                capture_id = str(capture_id_raw)
                event_scope = _capture_scope_fingerprint(
                    connection,
                    capture_id=capture_id,
                    route=route,
                    source_code=registry.source_code,
                )
                if event_scope != str(dependency_version):
                    continue
                scope_match_count += 1

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
                    "source_code": registry.source_code,
                    "endpoint_code": endpoint_code,
                    "artifact_type": str(dependency[1]),
                    "artifact_key": str(dependency[2]),
                    "scope_path_keys": list(route.scope_path_keys),
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
                                "change_type": str(change_type_raw),
                                "scope_resolver_version": SOURCE_SCOPE_VERSION,
                                "scope_path_keys": list(route.scope_path_keys),
                            }
                        ),
                    ],
                )
                created_request_count += 1

    return ScopedReanalysisResolution(
        scoped_dependency_count=scoped_dependency_count,
        eligible_event_count=eligible_event_count,
        scope_match_count=scope_match_count,
        created_request_count=created_request_count,
        existing_request_count=existing_request_count,
        endpoint_count=len(resolved_endpoints),
    )


__all__ = [
    "SOURCE_SCOPE_VERSION",
    "ScopedReanalysisResolution",
    "resolve_scoped_reanalysis_requests",
    "route_path_parameters",
    "scope_fingerprint_from_url",
    "source_scope_fingerprint",
]
