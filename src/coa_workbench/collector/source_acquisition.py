from __future__ import annotations

import base64
import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping
from urllib.parse import parse_qsl, urlsplit
from urllib.request import Request, urlopen

from coa_workbench.collector.http_read import read_response_resilient
from coa_workbench.collector.raw_archive import RawArchive, RawCapture, request_key_from_url
from coa_workbench.collector.source_observatory import (
    OBSERVATORY_VERSION,
    ReviewedGetContract,
    SourceObservation,
    build_get_url,
    observe_raw_capture,
    request_fingerprint,
)
from coa_workbench.storage.migrations import apply_migrations

_PATH_PARAMETER = re.compile(r"\{([A-Za-z_][A-Za-z0-9_]*)\}")
_EDGE_CHALLENGE_MARKERS = (
    b"challenges.cloudflare.com",
    b"/cdn-cgi/challenge-platform/",
)


def _utc(value: datetime | None = None) -> datetime:
    current = value or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    return current.astimezone(timezone.utc)


def _timestamp(value: datetime | None = None) -> str:
    return _utc(value).isoformat().replace("+00:00", "Z")


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _content_type_family(content_type: str | None) -> str:
    folded = (content_type or "").casefold()
    if "json" in folded:
        return "json"
    if "html" in folded:
        return "html"
    if "text/" in folded:
        return "text"
    if not folded:
        return "unknown"
    return "binary_or_other"


def _body_kind(body: bytes | None, content_type: str | None) -> str:
    if body is None:
        return "missing"
    try:
        json.loads(body)
    except (UnicodeDecodeError, json.JSONDecodeError):
        if "html" in (content_type or "").casefold() or body.lstrip().lower().startswith(
            (b"<!doctype html", b"<html")
        ):
            return "html"
        return "other"
    return "json"


def _looks_like_managed_edge_challenge(body: bytes | None) -> bool:
    if not body:
        return False
    lowered = body.lower()
    return all(marker in lowered for marker in _EDGE_CHALLENGE_MARKERS)


@dataclass(frozen=True, slots=True)
class AcquisitionClassification:
    body_kind: str
    outcome: str
    blocker_class: str | None
    error_class: str | None


def classify_acquisition(
    *,
    status: int | None,
    content_type: str | None,
    body: bytes | None,
    error: str | None = None,
) -> AcquisitionClassification:
    body_kind = _body_kind(body, content_type)

    if body is None:
        return AcquisitionClassification(
            body_kind=body_kind,
            outcome="transport_error",
            blocker_class=None,
            error_class="transport_error" if error else "response_body_missing",
        )

    if status is not None and 200 <= status < 300:
        if body_kind == "json" and "json" in (content_type or "").casefold():
            return AcquisitionClassification(
                body_kind=body_kind,
                outcome="schema_candidate",
                blocker_class=None,
                error_class=None,
            )
        if body_kind == "json":
            return AcquisitionClassification(
                body_kind=body_kind,
                outcome="json_content_type_mismatch",
                blocker_class=None,
                error_class=None,
            )
        return AcquisitionClassification(
            body_kind=body_kind,
            outcome="non_json_success",
            blocker_class=None,
            error_class=None,
        )

    if status == 403 and _looks_like_managed_edge_challenge(body):
        return AcquisitionClassification(
            body_kind=body_kind,
            outcome="blocked",
            blocker_class="managed_edge_challenge",
            error_class="http_403",
        )
    if status in {401, 403}:
        return AcquisitionClassification(
            body_kind=body_kind,
            outcome="blocked",
            blocker_class="access_denied",
            error_class=f"http_{status}",
        )
    if status == 429:
        return AcquisitionClassification(
            body_kind=body_kind,
            outcome="blocked",
            blocker_class="rate_limited",
            error_class="http_429",
        )
    if status is None:
        return AcquisitionClassification(
            body_kind=body_kind,
            outcome="transport_partial_response",
            blocker_class=None,
            error_class="transport_error" if error else "missing_http_status",
        )
    return AcquisitionClassification(
        body_kind=body_kind,
        outcome="http_error",
        blocker_class=None,
        error_class=f"http_{status}",
    )


@dataclass(frozen=True, slots=True)
class SourceAcquisitionObservation:
    acquisition_id: str
    contract_id: str
    source_code: str
    endpoint_code: str
    observed_at: str
    capture_mode: str
    request_fingerprint: str
    http_status: int | None
    content_type: str | None
    content_type_family: str
    body_kind: str
    outcome: str
    blocker_class: str | None
    error_class: str | None
    capture: RawCapture | None
    source_observation: SourceObservation | None

    def public_summary(self) -> dict[str, Any]:
        return {
            "source_code": self.source_code,
            "endpoint_code": self.endpoint_code,
            "observed_at": self.observed_at,
            "capture_mode": self.capture_mode,
            "http_status": self.http_status,
            "content_type_family": self.content_type_family,
            "body_kind": self.body_kind,
            "outcome": self.outcome,
            "blocker_class": self.blocker_class,
            "error_class": self.error_class,
            "raw_body_archived": self.capture is not None,
            "schema_observation_recorded": self.source_observation is not None,
            "change_event_count": (
                len(self.source_observation.change_event_ids) if self.source_observation else 0
            ),
            "reanalysis_request_count": (
                len(self.source_observation.reanalysis_request_ids)
                if self.source_observation
                else 0
            ),
        }


def _ensure_contract_registered(
    connection: Any,
    *,
    contract: ReviewedGetContract,
    observed_at: str,
    capture: RawCapture | None,
    metadata: Mapping[str, Any] | None,
) -> str:
    endpoint_row = connection.execute(
        "SELECT endpoint_id, status FROM source_endpoint WHERE endpoint_code = ?",
        [contract.endpoint_code],
    ).fetchone()
    endpoint_id = (
        str(endpoint_row[0])
        if endpoint_row
        else _sha256_text(
            f"{OBSERVATORY_VERSION}\0endpoint\0{contract.source_code}\0{contract.endpoint_code}"
        )
    )

    if endpoint_row is None:
        connection.execute(
            """
            INSERT INTO source_endpoint (
                endpoint_id, endpoint_code, route_template, method, params_json, auth_mode,
                schema_fingerprint, last_verified_at, status, source_code, logical_name,
                first_seen_at, last_seen_at
            ) VALUES (?, ?, ?, 'GET', ?, ?, NULL, NULL, 'reviewed', ?, ?, ?, ?)
            """,
            [
                endpoint_id,
                contract.endpoint_code,
                contract.route_template,
                _json(sorted(contract.parameter_keys)),
                contract.auth_state,
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
                source_code = COALESCE(source_code, ?),
                logical_name = COALESCE(logical_name, ?),
                first_seen_at = COALESCE(first_seen_at, ?),
                last_seen_at = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE endpoint_code = ?
            """,
            [
                contract.route_template,
                _json(sorted(contract.parameter_keys)),
                contract.auth_state,
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
            (
                _json(contract.request_body_shape)
                if contract.request_body_shape is not None
                else None
            ),
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
    if capture is not None:
        connection.execute(
            "UPDATE raw_object SET endpoint_id = ? WHERE raw_id = ?",
            [endpoint_id, capture.raw_id],
        )
    return endpoint_id


def record_source_acquisition(
    database_path: Path,
    migrations_dir: Path,
    *,
    contract: ReviewedGetContract,
    request_url: str,
    capture_mode: str,
    classification: AcquisitionClassification,
    capture: RawCapture | None = None,
    source_observation: SourceObservation | None = None,
    observed_at: datetime | str | None = None,
    http_status: int | None = None,
    content_type: str | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> SourceAcquisitionObservation:
    apply_migrations(database_path, migrations_dir)
    if capture is not None:
        if capture.endpoint_code != contract.endpoint_code:
            raise ValueError("capture endpoint_code does not match reviewed contract")
        if capture.source_code != contract.source_code:
            raise ValueError("capture source_code does not match reviewed contract")
        observed_text = capture.fetched_at
        http_status = capture.http_status
        content_type = capture.content_type
        identity = capture.observation_id
    else:
        if isinstance(observed_at, str):
            observed_text = observed_at
        else:
            observed_text = _timestamp(observed_at)
        identity = observed_text

    request_fp = request_fingerprint("GET", request_url)
    acquisition_id = _sha256_text(
        f"{OBSERVATORY_VERSION}\0acquisition\0{contract.contract_id}\0"
        f"{capture_mode}\0{request_fp}\0{identity}"
    )

    import duckdb

    safe_metadata = {
        "observatory_version": OBSERVATORY_VERSION,
        **dict(metadata or {}),
    }
    with duckdb.connect(str(database_path)) as connection:
        _ensure_contract_registered(
            connection,
            contract=contract,
            observed_at=observed_text,
            capture=capture,
            metadata=safe_metadata,
        )
        connection.execute(
            """
            INSERT INTO source_acquisition_observation (
                acquisition_id, contract_id, source_code, endpoint_code, observed_at,
                capture_mode, request_fingerprint, raw_id, raw_observation_id,
                source_capture_id, http_status, content_type, body_kind, outcome,
                blocker_class, error_class, metadata_json
            ) SELECT ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            WHERE NOT EXISTS (
                SELECT 1 FROM source_acquisition_observation WHERE acquisition_id = ?
            )
            """,
            [
                acquisition_id,
                contract.contract_id,
                contract.source_code,
                contract.endpoint_code,
                observed_text,
                capture_mode,
                request_fp,
                capture.raw_id if capture else None,
                capture.observation_id if capture else None,
                source_observation.source_capture_id if source_observation else None,
                http_status,
                content_type,
                classification.body_kind,
                classification.outcome,
                classification.blocker_class,
                classification.error_class,
                _json(safe_metadata),
                acquisition_id,
            ],
        )

    return SourceAcquisitionObservation(
        acquisition_id=acquisition_id,
        contract_id=contract.contract_id,
        source_code=contract.source_code,
        endpoint_code=contract.endpoint_code,
        observed_at=observed_text,
        capture_mode=capture_mode,
        request_fingerprint=request_fp,
        http_status=http_status,
        content_type=content_type,
        content_type_family=_content_type_family(content_type),
        body_kind=classification.body_kind,
        outcome=classification.outcome,
        blocker_class=classification.blocker_class,
        error_class=classification.error_class,
        capture=capture,
        source_observation=source_observation,
    )


def _archive_and_record(
    *,
    archive: RawArchive,
    database_path: Path,
    migrations_dir: Path,
    contract: ReviewedGetContract,
    request_url: str,
    body: bytes | None,
    http_status: int | None,
    content_type: str | None,
    capture_mode: str,
    dimension_keys: Iterable[str],
    observed_at: datetime | None = None,
    error: str | None = None,
) -> SourceAcquisitionObservation:
    classification = classify_acquisition(
        status=http_status,
        content_type=content_type,
        body=body,
        error=error,
    )
    capture = None
    if body is not None:
        capture = archive.capture_bytes(
            body,
            source_code=contract.source_code,
            endpoint_code=contract.endpoint_code,
            request_key=request_key_from_url("GET", request_url),
            fetched_at=observed_at,
            http_status=http_status,
            content_type=content_type,
            request_url=request_url,
            metadata={
                "observatory_version": OBSERVATORY_VERSION,
                "contract_fingerprint": contract.contract_fingerprint,
                "capture_mode": capture_mode,
                "acquisition_outcome": classification.outcome,
                "blocker_class": classification.blocker_class,
            },
        )

    source_observation = None
    if (
        capture is not None
        and classification.outcome == "schema_candidate"
        and body is not None
    ):
        source_observation = observe_raw_capture(
            database_path,
            migrations_dir,
            contract=contract,
            capture=capture,
            payload=body,
            request_url=request_url,
            dimension_keys=dimension_keys,
            metadata={"capture_mode": capture_mode},
        )

    return record_source_acquisition(
        database_path,
        migrations_dir,
        contract=contract,
        request_url=request_url,
        capture_mode=capture_mode,
        classification=classification,
        capture=capture,
        source_observation=source_observation,
        observed_at=observed_at,
        http_status=http_status,
        content_type=content_type,
        metadata={"capture_mode": capture_mode},
    )


def capture_reviewed_get_observation(
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
) -> SourceAcquisitionObservation:
    request_url = build_get_url(
        contract,
        path_params=path_params,
        query_params=query_params,
    )
    request = Request(request_url, method="GET", headers={"Accept": "application/json"})
    status, content_type, body, error = read_response_resilient(
        request,
        timeout_seconds=timeout_seconds,
        opener=opener,
        max_bytes=max_bytes,
        retry_count=1,
    )
    return _archive_and_record(
        archive=archive,
        database_path=database_path,
        migrations_dir=migrations_dir,
        contract=contract,
        request_url=request_url,
        body=body,
        http_status=status,
        content_type=content_type,
        capture_mode="direct_http",
        dimension_keys=dimension_keys,
        error=error,
    )


def _route_regex(route_template: str) -> re.Pattern[str]:
    pieces: list[str] = []
    cursor = 0
    for match in _PATH_PARAMETER.finditer(route_template):
        pieces.append(re.escape(route_template[cursor : match.start()]))
        pieces.append(r"[^/]+")
        cursor = match.end()
    pieces.append(re.escape(route_template[cursor:]))
    return re.compile("^" + "".join(pieces) + "$")


def _har_observed_at(value: Any) -> datetime | None:
    if not value:
        return None
    text = str(value).replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    return _utc(parsed)


def _har_response_body(content: Mapping[str, Any]) -> bytes | None:
    text = content.get("text")
    if text is None:
        return None
    if content.get("encoding") == "base64":
        try:
            return base64.b64decode(str(text), validate=True)
        except ValueError:
            return None
    return str(text).encode("utf-8")


def observe_reviewed_har(
    path: Path,
    *,
    archive: RawArchive,
    database_path: Path,
    migrations_dir: Path,
    contract: ReviewedGetContract,
    dimension_keys: Iterable[str] = (),
) -> tuple[SourceAcquisitionObservation, ...]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    entries = payload.get("log", {}).get("entries", [])
    if not isinstance(entries, list):
        raise ValueError("HAR log.entries must be an array")

    base = urlsplit(contract.base_url)
    route_pattern = _route_regex(contract.route_template)
    results: list[SourceAcquisitionObservation] = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        request = entry.get("request", {})
        response = entry.get("response", {})
        if not isinstance(request, dict) or not isinstance(response, dict):
            continue
        method = str(request.get("method", "")).upper()
        request_url = str(request.get("url", ""))
        parts = urlsplit(request_url)
        if method != "GET":
            continue
        if parts.scheme != "https" or parts.hostname != base.hostname:
            continue
        if not route_pattern.fullmatch(parts.path):
            continue
        query_keys = {key for key, _ in parse_qsl(parts.query, keep_blank_values=True)}
        if not query_keys <= set(contract.parameter_keys):
            continue

        try:
            status = int(response.get("status")) if response.get("status") is not None else None
        except (TypeError, ValueError):
            status = None
        content = response.get("content", {})
        if not isinstance(content, dict):
            content = {}
        body = _har_response_body(content)
        content_type = str(content.get("mimeType") or "") or None
        observed_at = _har_observed_at(entry.get("startedDateTime"))

        results.append(
            _archive_and_record(
                archive=archive,
                database_path=database_path,
                migrations_dir=migrations_dir,
                contract=contract,
                request_url=request_url,
                body=body,
                http_status=status,
                content_type=content_type,
                capture_mode="browser_har",
                dimension_keys=dimension_keys,
                observed_at=observed_at,
                error="har_response_body_missing" if body is None else None,
            )
        )
    return tuple(results)


__all__ = [
    "AcquisitionClassification",
    "SourceAcquisitionObservation",
    "capture_reviewed_get_observation",
    "classify_acquisition",
    "observe_reviewed_har",
    "record_source_acquisition",
]
