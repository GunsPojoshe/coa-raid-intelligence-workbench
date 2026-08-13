from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping
from urllib.parse import urlencode, urlsplit, urlunsplit
from urllib.request import Request, urlopen

from coa_workbench.collector.http_read import read_response_resilient
from coa_workbench.collector.raw_archive import RawArchive, RawCapture, request_key_from_url
from coa_workbench.storage.migrations import apply_migrations

OBSERVATORY_VERSION = "source-observatory-v1"
_ALLOWED_REVIEW_STATES = {"reviewed", "verified"}
_PATH_PARAMETER = re.compile(r"\{([A-Za-z_][A-Za-z0-9_]*)\}")


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _normalize_timestamp(value: datetime | str | None) -> str:
    if value is None:
        current = _utc_now()
    elif isinstance(value, datetime):
        current = value
    else:
        return value
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    return current.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _json_type(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, int):
        return "int"
    if isinstance(value, float):
        return "float"
    if isinstance(value, str):
        return "str"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return type(value).__name__


def _pointer(parts: tuple[str, ...]) -> str:
    if not parts:
        return "/"
    escaped = [part.replace("~", "~0").replace("/", "~1") for part in parts]
    return "/" + "/".join(escaped)


@dataclass(frozen=True, slots=True)
class ReviewedGetContract:
    source_code: str
    endpoint_code: str
    base_url: str
    route_template: str
    parameter_keys: tuple[str, ...] = ()
    auth_state: str = "none"
    discovery_source: str = "reviewed_network"
    review_state: str = "reviewed"
    request_body_shape: Mapping[str, Any] | None = None
    logical_name: str | None = None

    def __post_init__(self) -> None:
        if self.review_state not in _ALLOWED_REVIEW_STATES:
            raise ValueError(f"contract review_state is not capture-ready: {self.review_state}")
        if self.auth_state == "unknown":
            raise ValueError("contract auth_state cannot be unknown")
        if urlsplit(self.base_url).scheme != "https":
            raise ValueError("contract base_url must use HTTPS")
        if not self.route_template.startswith("/"):
            raise ValueError("contract route_template must start with /")
        if len(self.parameter_keys) != len(set(self.parameter_keys)):
            raise ValueError("contract parameter_keys must be unique")
        if any(not key for key in self.parameter_keys):
            raise ValueError("contract parameter_keys cannot contain empty values")

    @property
    def method(self) -> str:
        return "GET"

    @property
    def contract_fingerprint(self) -> str:
        canonical = {
            "source_code": self.source_code,
            "endpoint_code": self.endpoint_code,
            "base_url": self.base_url.rstrip("/"),
            "method": self.method,
            "route_template": self.route_template,
            "parameter_keys": sorted(self.parameter_keys),
            "request_body_shape": self.request_body_shape,
            "auth_state": self.auth_state,
            "discovery_source": self.discovery_source,
            "review_state": self.review_state,
        }
        return _sha256_text(_json(canonical))

    @property
    def contract_id(self) -> str:
        return _sha256_text(f"{OBSERVATORY_VERSION}\0contract\0{self.contract_fingerprint}")


@dataclass(frozen=True, slots=True)
class SchemaSnapshot:
    schema_fingerprint: str
    root_type: str
    path_types: dict[str, tuple[str, ...]]
    dimension_values: dict[str, tuple[str, ...]]
    scan_truncated: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class SourceChange:
    change_type: str
    severity: str
    subject_path: str | None
    previous_value: Any
    current_value: Any


@dataclass(frozen=True, slots=True)
class SourceObservation:
    capture: RawCapture
    contract_id: str
    source_capture_id: str
    snapshot_id: str | None
    change_event_ids: tuple[str, ...]
    reanalysis_request_ids: tuple[str, ...]


def build_get_url(
    contract: ReviewedGetContract,
    *,
    path_params: Mapping[str, str | int] | None = None,
    query_params: Mapping[str, str | int | float | bool] | None = None,
) -> str:
    path_params = dict(path_params or {})
    query_params = dict(query_params or {})
    placeholders = set(_PATH_PARAMETER.findall(contract.route_template))
    if set(path_params) != placeholders:
        missing = sorted(placeholders - set(path_params))
        extra = sorted(set(path_params) - placeholders)
        raise ValueError(f"path parameter mismatch: missing={missing}, extra={extra}")
    unknown_query = sorted(set(query_params) - set(contract.parameter_keys))
    if unknown_query:
        raise ValueError(f"query parameters are not in reviewed contract: {unknown_query}")

    route = contract.route_template
    for key in sorted(placeholders):
        value = str(path_params[key])
        if "/" in value or not value:
            raise ValueError(f"path parameter {key!r} is not a single safe segment")
        route = route.replace("{" + key + "}", value)
    base = contract.base_url.rstrip("/")
    query = urlencode(sorted(query_params.items()))
    return f"{base}{route}" + (f"?{query}" if query else "")


def request_fingerprint(method: str, url: str) -> str:
    parts = urlsplit(url)
    canonical = urlunsplit((parts.scheme, parts.netloc, parts.path, parts.query, ""))
    return _sha256_text(f"{method.upper()}\0{canonical}")


def snapshot_json_payload(
    payload: bytes,
    *,
    dimension_keys: Iterable[str] = (),
    max_array_items: int = 1000,
    max_paths: int = 5000,
) -> SchemaSnapshot:
    if max_array_items < 1 or max_paths < 1:
        raise ValueError("snapshot bounds must be positive")
    try:
        value = json.loads(payload)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("observed payload is not valid JSON") from exc

    configured_dimensions = {key.casefold(): key for key in dimension_keys}
    path_types: dict[str, set[str]] = {}
    dimensions: dict[str, set[str]] = {name: set() for name in configured_dimensions.values()}
    truncated = False

    def add_path(path: tuple[str, ...], type_name: str) -> bool:
        nonlocal truncated
        pointer = _pointer(path)
        if pointer not in path_types and len(path_types) >= max_paths:
            truncated = True
            return False
        path_types.setdefault(pointer, set()).add(type_name)
        return True

    def walk(item: Any, path: tuple[str, ...]) -> None:
        nonlocal truncated
        if not add_path(path, _json_type(item)):
            return
        if isinstance(item, dict):
            for key in sorted(item):
                child = item[key]
                dimension_name = configured_dimensions.get(str(key).casefold())
                if dimension_name and isinstance(child, bool):
                    dimensions[dimension_name].add("true" if child else "false")
                elif dimension_name and isinstance(child, (str, int, float)):
                    dimensions[dimension_name].add(str(child))
                walk(child, (*path, str(key)))
        elif isinstance(item, list):
            if len(item) > max_array_items:
                truncated = True
            for child in item[:max_array_items]:
                walk(child, (*path, "*"))

    walk(value, ())
    canonical_paths = {key: tuple(sorted(values)) for key, values in sorted(path_types.items())}
    canonical_dimensions = {
        key: tuple(sorted(values)) for key, values in sorted(dimensions.items()) if values
    }
    fingerprint = _sha256_text(_json(canonical_paths))
    return SchemaSnapshot(
        schema_fingerprint=fingerprint,
        root_type=_json_type(value),
        path_types=canonical_paths,
        dimension_values=canonical_dimensions,
        scan_truncated=truncated,
    )


def diff_schema_snapshots(
    previous: SchemaSnapshot,
    current: SchemaSnapshot,
) -> tuple[SourceChange, ...]:
    changes: list[SourceChange] = []
    previous_paths = set(previous.path_types)
    current_paths = set(current.path_types)

    if previous.schema_fingerprint != current.schema_fingerprint:
        severity = "warning" if (previous_paths - current_paths) else "info"
        changes.append(
            SourceChange(
                change_type="schema_changed",
                severity=severity,
                subject_path=None,
                previous_value=previous.schema_fingerprint,
                current_value=current.schema_fingerprint,
            )
        )

    for path in sorted(current_paths - previous_paths):
        changes.append(
            SourceChange(
                change_type="field_added",
                severity="info",
                subject_path=path,
                previous_value=None,
                current_value=list(current.path_types[path]),
            )
        )

    if not previous.scan_truncated and not current.scan_truncated:
        for path in sorted(previous_paths - current_paths):
            changes.append(
                SourceChange(
                    change_type="field_removed",
                    severity="warning",
                    subject_path=path,
                    previous_value=list(previous.path_types[path]),
                    current_value=None,
                )
            )

    for path in sorted(previous_paths & current_paths):
        if previous.path_types[path] != current.path_types[path]:
            changes.append(
                SourceChange(
                    change_type="field_type_changed",
                    severity="warning",
                    subject_path=path,
                    previous_value=list(previous.path_types[path]),
                    current_value=list(current.path_types[path]),
                )
            )

    for key, current_values in sorted(current.dimension_values.items()):
        previous_values = set(previous.dimension_values.get(key, ()))
        added = sorted(set(current_values) - previous_values)
        if added:
            changes.append(
                SourceChange(
                    change_type="new_dimension_value",
                    severity="info",
                    subject_path=f"dimension:{key}",
                    previous_value=None,
                    current_value=added,
                )
            )
    return tuple(changes)


def register_artifact_dependency(
    database_path: Path,
    migrations_dir: Path,
    *,
    artifact_type: str,
    artifact_key: str,
    analysis_type: str,
    analysis_version: str,
    dependency_type: str,
    dependency_key: str,
    dependency_version: str | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> str:
    apply_migrations(database_path, migrations_dir)
    dependency_seed = _json(
        {
            "artifact_type": artifact_type,
            "artifact_key": artifact_key,
            "analysis_type": analysis_type,
            "analysis_version": analysis_version,
            "dependency_type": dependency_type,
            "dependency_key": dependency_key,
            "dependency_version": dependency_version,
        }
    )
    dependency_id = _sha256_text(f"{OBSERVATORY_VERSION}\0dependency\0{dependency_seed}")

    import duckdb

    with duckdb.connect(str(database_path)) as connection:
        connection.execute(
            """
            INSERT INTO artifact_dependency (
                dependency_id, artifact_type, artifact_key, analysis_type, analysis_version,
                dependency_type, dependency_key, dependency_version, active, metadata_json
            ) SELECT ?, ?, ?, ?, ?, ?, ?, ?, TRUE, ?
            WHERE NOT EXISTS (
                SELECT 1 FROM artifact_dependency WHERE dependency_id = ?
            )
            """,
            [
                dependency_id,
                artifact_type,
                artifact_key,
                analysis_type,
                analysis_version,
                dependency_type,
                dependency_key,
                dependency_version,
                _json(dict(metadata or {})),
                dependency_id,
            ],
        )
    return dependency_id


def _snapshot_from_row(row: tuple[Any, ...]) -> SchemaSnapshot:
    return SchemaSnapshot(
        schema_fingerprint=str(row[0]),
        root_type=str(row[1]),
        path_types={
            str(key): tuple(str(value) for value in values)
            for key, values in json.loads(row[2]).items()
        },
        dimension_values={
            str(key): tuple(str(value) for value in values)
            for key, values in json.loads(row[3]).items()
        },
        scan_truncated=bool(row[4]),
    )


def _event_id(capture_id: str, change: SourceChange) -> str:
    seed = _json(
        {
            "capture_id": capture_id,
            "change_type": change.change_type,
            "subject_path": change.subject_path,
            "previous_value": change.previous_value,
            "current_value": change.current_value,
        }
    )
    return _sha256_text(f"{OBSERVATORY_VERSION}\0event\0{seed}")


def observe_raw_capture(
    database_path: Path,
    migrations_dir: Path,
    *,
    contract: ReviewedGetContract,
    capture: RawCapture,
    payload: bytes,
    request_url: str,
    dimension_keys: Iterable[str] = (),
    metadata: Mapping[str, Any] | None = None,
) -> SourceObservation:
    apply_migrations(database_path, migrations_dir)
    if capture.endpoint_code != contract.endpoint_code:
        raise ValueError("capture endpoint_code does not match reviewed contract")
    if capture.source_code != contract.source_code:
        raise ValueError("capture source_code does not match reviewed contract")
    if capture.content_type and "json" not in capture.content_type.casefold():
        raise ValueError("Source Observatory v1 requires a JSON response")

    snapshot = snapshot_json_payload(payload, dimension_keys=dimension_keys)
    observed_at = _normalize_timestamp(capture.fetched_at)
    source_capture_id = _sha256_text(
        f"{OBSERVATORY_VERSION}\0capture\0{contract.contract_id}\0{capture.observation_id}"
    )
    snapshot_id = _sha256_text(
        f"{OBSERVATORY_VERSION}\0snapshot\0{source_capture_id}\0{snapshot.schema_fingerprint}"
    )

    import duckdb

    change_event_ids: list[str] = []
    reanalysis_request_ids: list[str] = []
    with duckdb.connect(str(database_path)) as connection:
        endpoint_row = connection.execute(
            "SELECT endpoint_id FROM source_endpoint WHERE endpoint_code = ?",
            [contract.endpoint_code],
        ).fetchone()
        endpoint_existed = endpoint_row is not None
        endpoint_id = (
            str(endpoint_row[0])
            if endpoint_row
            else _sha256_text(
                f"{OBSERVATORY_VERSION}\0endpoint\0{contract.source_code}\0{contract.endpoint_code}"
            )
        )

        previous_contract = connection.execute(
            """
            SELECT contract_fingerprint
            FROM source_contract_version
            WHERE endpoint_code = ?
            ORDER BY last_seen_at DESC, contract_id DESC
            LIMIT 1
            """,
            [contract.endpoint_code],
        ).fetchone()

        previous_snapshot_row = connection.execute(
            """
            SELECT schema_fingerprint, root_type, path_types_json,
                   dimension_values_json, scan_truncated
            FROM source_schema_snapshot
            WHERE endpoint_code = ?
            ORDER BY observed_at DESC, snapshot_id DESC
            LIMIT 1
            """,
            [contract.endpoint_code],
        ).fetchone()

        if not endpoint_existed:
            connection.execute(
                """
                INSERT INTO source_endpoint (
                    endpoint_id, endpoint_code, route_template, method, params_json, auth_mode,
                    schema_fingerprint, last_verified_at, status, source_code, logical_name,
                    first_seen_at, last_seen_at
                ) VALUES (?, ?, ?, 'GET', ?, ?, ?, ?, 'verified', ?, ?, ?, ?)
                """,
                [
                    endpoint_id,
                    contract.endpoint_code,
                    contract.route_template,
                    _json(sorted(contract.parameter_keys)),
                    contract.auth_state,
                    snapshot.schema_fingerprint,
                    observed_at,
                    contract.source_code,
                    contract.logical_name or contract.endpoint_code,
                    observed_at,
                    observed_at,
                ],
            )
        else:
            connection.execute(
                """
                UPDATE source_endpoint
                SET route_template = ?, method = 'GET', params_json = ?, auth_mode = ?,
                    schema_fingerprint = ?, last_verified_at = ?, status = 'verified',
                    source_code = COALESCE(source_code, ?),
                    logical_name = COALESCE(logical_name, ?),
                    first_seen_at = COALESCE(first_seen_at, ?),
                    last_seen_at = ?, updated_at = CURRENT_TIMESTAMP
                WHERE endpoint_code = ?
                """,
                [
                    contract.route_template,
                    _json(sorted(contract.parameter_keys)),
                    contract.auth_state,
                    snapshot.schema_fingerprint,
                    observed_at,
                    contract.source_code,
                    contract.logical_name or contract.endpoint_code,
                    observed_at,
                    observed_at,
                    contract.endpoint_code,
                ],
            )

        connection.execute(
            """
            INSERT INTO source_contract_version (
                contract_id, source_code, endpoint_code, method, route_template,
                contract_fingerprint, parameter_keys_json, request_body_shape_json,
                auth_state, discovery_source, review_state, first_seen_at, last_seen_at,
                metadata_json
            ) SELECT ?, ?, ?, 'GET', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            WHERE NOT EXISTS (
                SELECT 1 FROM source_contract_version WHERE contract_id = ?
            )
            """,
            [
                contract.contract_id,
                contract.source_code,
                contract.endpoint_code,
                contract.route_template,
                contract.contract_fingerprint,
                _json(sorted(contract.parameter_keys)),
                _json(contract.request_body_shape) if contract.request_body_shape is not None else None,
                contract.auth_state,
                contract.discovery_source,
                contract.review_state,
                observed_at,
                observed_at,
                _json(dict(metadata or {})),
                contract.contract_id,
            ],
        )
        connection.execute(
            "UPDATE source_contract_version SET last_seen_at = ? WHERE contract_id = ?",
            [observed_at, contract.contract_id],
        )
        connection.execute(
            "UPDATE raw_object SET endpoint_id = ? WHERE raw_id = ?",
            [endpoint_id, capture.raw_id],
        )

        connection.execute(
            """
            INSERT INTO source_capture (
                capture_id, contract_id, endpoint_code, raw_id, raw_observation_id,
                captured_at, request_fingerprint, schema_fingerprint, http_status,
                content_type, metadata_json
            ) SELECT ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            WHERE NOT EXISTS (SELECT 1 FROM source_capture WHERE capture_id = ?)
            """,
            [
                source_capture_id,
                contract.contract_id,
                contract.endpoint_code,
                capture.raw_id,
                capture.observation_id,
                observed_at,
                request_fingerprint("GET", request_url),
                snapshot.schema_fingerprint,
                capture.http_status,
                capture.content_type,
                _json(dict(metadata or {})),
                source_capture_id,
            ],
        )

        connection.execute(
            """
            INSERT INTO source_schema_snapshot (
                snapshot_id, capture_id, contract_id, endpoint_code, observed_at,
                schema_fingerprint, root_type, path_types_json, dimension_values_json,
                scan_truncated, metadata_json
            ) SELECT ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            WHERE NOT EXISTS (SELECT 1 FROM source_schema_snapshot WHERE snapshot_id = ?)
            """,
            [
                snapshot_id,
                source_capture_id,
                contract.contract_id,
                contract.endpoint_code,
                observed_at,
                snapshot.schema_fingerprint,
                snapshot.root_type,
                _json({key: list(values) for key, values in snapshot.path_types.items()}),
                _json({key: list(values) for key, values in snapshot.dimension_values.items()}),
                snapshot.scan_truncated,
                _json(dict(metadata or {})),
                snapshot_id,
            ],
        )

        changes: list[SourceChange] = []
        if not endpoint_existed:
            changes.append(
                SourceChange(
                    change_type="endpoint_added",
                    severity="info",
                    subject_path=contract.route_template,
                    previous_value=None,
                    current_value={
                        "method": "GET",
                        "contract_fingerprint": contract.contract_fingerprint,
                    },
                )
            )
        elif previous_contract and str(previous_contract[0]) != contract.contract_fingerprint:
            changes.append(
                SourceChange(
                    change_type="request_contract_changed",
                    severity="warning",
                    subject_path=contract.route_template,
                    previous_value=str(previous_contract[0]),
                    current_value=contract.contract_fingerprint,
                )
            )

        if previous_snapshot_row:
            previous_snapshot = _snapshot_from_row(previous_snapshot_row)
            changes.extend(diff_schema_snapshots(previous_snapshot, snapshot))

        for change in changes:
            event_id = _event_id(source_capture_id, change)
            connection.execute(
                """
                INSERT INTO source_change_event (
                    event_id, source_code, endpoint_code, contract_id, capture_id,
                    observed_at, change_type, severity, subject_path,
                    previous_value_json, current_value_json, confidence, status,
                    metadata_json
                ) SELECT ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1.0, 'open', ?
                WHERE NOT EXISTS (SELECT 1 FROM source_change_event WHERE event_id = ?)
                """,
                [
                    event_id,
                    contract.source_code,
                    contract.endpoint_code,
                    contract.contract_id,
                    source_capture_id,
                    observed_at,
                    change.change_type,
                    change.severity,
                    change.subject_path,
                    _json(change.previous_value) if change.previous_value is not None else None,
                    _json(change.current_value) if change.current_value is not None else None,
                    _json({"observatory_version": OBSERVATORY_VERSION}),
                    event_id,
                ],
            )
            change_event_ids.append(event_id)

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
                request_id = _sha256_text(f"{OBSERVATORY_VERSION}\0request\0{dedupe_key}")
                target_scope = {
                    "source_code": contract.source_code,
                    "endpoint_code": contract.endpoint_code,
                    "artifact_type": artifact_type,
                    "artifact_key": artifact_key,
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
                        _json({"change_type": change.change_type}),
                        dedupe_key,
                    ],
                )
                reanalysis_request_ids.append(request_id)

    return SourceObservation(
        capture=capture,
        contract_id=contract.contract_id,
        source_capture_id=source_capture_id,
        snapshot_id=snapshot_id,
        change_event_ids=tuple(change_event_ids),
        reanalysis_request_ids=tuple(dict.fromkeys(reanalysis_request_ids)),
    )


def capture_reviewed_get(
    *,
    archive: RawArchive,
    database_path: Path,
    migrations_dir: Path,
    contract: ReviewedGetContract,
    path_params: Mapping[str, str | int] | None = None,
    query_params: Mapping[str, str | int | float | bool] | None = None,
    dimension_keys: Iterable[str] = (),
    timeout_seconds: float = 20.0,
    max_bytes: int = 32 * 1024 * 1024,
    opener: Any = urlopen,
) -> SourceObservation:
    url = build_get_url(contract, path_params=path_params, query_params=query_params)
    request = Request(url, method="GET", headers={"Accept": "application/json"})
    status, content_type, body, error = read_response_resilient(
        request,
        timeout_seconds=timeout_seconds,
        opener=opener,
        max_bytes=max_bytes,
        retry_count=1,
    )
    if body is None:
        raise RuntimeError(error or "reviewed GET returned no response body")

    capture = archive.capture_bytes(
        body,
        source_code=contract.source_code,
        endpoint_code=contract.endpoint_code,
        request_key=request_key_from_url("GET", url),
        http_status=status,
        content_type=content_type,
        request_url=url,
        metadata={
            "observatory_version": OBSERVATORY_VERSION,
            "contract_fingerprint": contract.contract_fingerprint,
            "network_error": error,
        },
    )
    if status is None or not 200 <= status < 300:
        raise RuntimeError(error or f"reviewed GET returned HTTP {status}")
    return observe_raw_capture(
        database_path,
        migrations_dir,
        contract=contract,
        capture=capture,
        payload=body,
        request_url=url,
        dimension_keys=dimension_keys,
        metadata={"network_error": error},
    )


__all__ = [
    "OBSERVATORY_VERSION",
    "ReviewedGetContract",
    "SchemaSnapshot",
    "SourceChange",
    "SourceObservation",
    "build_get_url",
    "capture_reviewed_get",
    "diff_schema_snapshots",
    "observe_raw_capture",
    "register_artifact_dependency",
    "request_fingerprint",
    "snapshot_json_payload",
]
