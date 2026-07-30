from __future__ import annotations

import gzip
import hashlib
import json
import time
from collections.abc import Callable, Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .http_profile import SameOriginHttpSession
from .raw_archive import RawArchive
from .report_discovery import REPORTS_PUBLIC_ROUTE, capture_public_report_discovery
from .source_registry import SourceRegistry

_MANIFEST_SCHEMA_VERSION = 1
_MANIFEST_VERSION = "public-report-manifest-v1"
_TERMINAL_KIND = "report_pagination_terminal_search"
_TERMINAL_PRIVATE_KIND = "report_pagination_terminal_private_batch"
_TERMINAL_VERSION = "report-pagination-terminal-search-v1"
_EXPECTED_PAGINATION_FIELDS = {"hasMore", "hasPrevious", "limit", "offset", "page"}
_EXPECTED_REPORT_KEYS = {
    "created_at",
    "end_time",
    "guild_id",
    "guild_name",
    "highest_difficulty",
    "id",
    "locations",
    "start_time",
    "title",
    "uploader_username",
    "visibility",
}
_VERIFIED_STRING_FIELDS = (
    "title",
    "created_at",
    "start_time",
    "end_time",
    "visibility",
    "uploader_username",
)
ProgressCallback = Callable[[str, int, int], None]


def _generated_at() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_json(value: object) -> str:
    return _sha256_bytes(_canonical_json(value).encode("utf-8"))


def _load_object(path: Path, label: str) -> tuple[dict[str, Any], bytes]:
    body = path.read_bytes()
    payload = json.loads(body)
    if not isinstance(payload, dict):
        raise ValueError(f"{label} must contain a JSON object")
    return payload, body


def _required_object(value: object, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"public report manifest field {field_name} must be an object")
    return value


def _required_list(value: object, field_name: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"public report manifest field {field_name} must be an array")
    return value


def _required_integer(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"public report manifest field {field_name} must be an integer")
    return value


def _required_boolean(value: object, field_name: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"public report manifest field {field_name} must be a boolean")
    return value


def _write_json(path: Path, payload: object) -> bytes:
    body = (json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(body)
    temporary.replace(path)
    return body


def _read_archived_payload(payload_path: str) -> dict[str, Any]:
    payload = json.loads(gzip.decompress(Path(payload_path).read_bytes()))
    if not isinstance(payload, dict):
        raise ValueError("public report manifest page must contain a JSON object")
    return payload


def _validate_terminal_receipt(
    receipt: Mapping[str, Any], expected_guild_label: str
) -> tuple[int, int, int]:
    expected_root = {
        "schema_version": 1,
        "search_kind": _TERMINAL_KIND,
        "search_version": _TERMINAL_VERSION,
    }
    for field_name, expected in expected_root.items():
        if receipt.get(field_name) != expected:
            raise ValueError(f"pagination terminal receipt mismatch: {field_name}")

    target = _required_object(receipt.get("target"), "target")
    if target.get("guild_label") != expected_guild_label:
        raise ValueError("pagination terminal guild label mismatch")
    if target.get("guild_identity_status") != "operator_named_target_unresolved":
        raise ValueError("guild identity was unexpectedly resolved before manifest capture")

    request = _required_object(receipt.get("request"), "request")
    if request.get("route_template") != REPORTS_PUBLIC_ROUTE:
        raise ValueError("pagination terminal route mismatch")
    if request.get("limit") != 5:
        raise ValueError("pagination terminal limit mismatch")
    if request.get("sort_by") != "created_at" or request.get("sort_order") != "desc":
        raise ValueError("pagination terminal sorting mismatch")

    summary = _required_object(receipt.get("summary"), "summary")
    expected_summary = {
        "all_integrity_checks_passed": True,
        "ready_for_exhaustive_public_report_manifest_capture": True,
        "ready_for_full_guild_crawl": False,
        "ready_for_bis25_scoring": False,
        "contains_source_scalar_values": False,
        "private_search_contains_source_scalar_values": True,
    }
    for field_name, expected in expected_summary.items():
        if summary.get(field_name) != expected:
            raise ValueError(f"pagination terminal summary mismatch: {field_name}")

    boundary = _required_object(receipt.get("decision_boundary"), "decision_boundary")
    expected_boundary = {
        "status": "pagination_terminal_contract_verified",
        "page_semantics_verified": True,
        "page_size_semantics_verified": True,
        "offset_semantics_verified": True,
        "has_previous_semantics_verified": True,
        "has_more_semantics_verified": True,
        "termination_condition_verified": True,
        "terminal_page_verified": True,
        "ready_for_exhaustive_public_report_manifest_capture": True,
        "automatic_full_manifest_collection_allowed": False,
        "ready_for_full_guild_crawl": False,
        "ready_for_guild_filtering": False,
        "ready_for_multi_report_character_graph": False,
        "ready_for_performance_model": False,
        "ready_for_global_benchmark": False,
        "ready_for_bis25_scoring": False,
        "planner_scoring_allowed": False,
    }
    for field_name, expected in expected_boundary.items():
        if boundary.get(field_name) != expected:
            raise ValueError(f"pagination terminal boundary mismatch: {field_name}")

    contract = _required_object(receipt.get("terminal_contract"), "terminal_contract")
    if contract.get("status") != "verified_adjacent_transition":
        raise ValueError("pagination terminal transition is not verified")
    if contract.get("strategy") != "request_pages_1_through_terminal_page_inclusive":
        raise ValueError("pagination terminal strategy mismatch")
    if contract.get("inclusive_terminal_page") is not True:
        raise ValueError("pagination terminal page is not inclusive")
    if contract.get("deduplication_key") != "/reports/*/id":
        raise ValueError("pagination terminal deduplication key mismatch")

    terminal_page = _required_integer(contract.get("terminal_page"), "terminal_page")
    terminal_count = _required_integer(
        contract.get("terminal_page_report_count"), "terminal_page_report_count"
    )
    successor_page = _required_integer(contract.get("successor_page"), "successor_page")
    if terminal_page < 2 or successor_page != terminal_page + 1:
        raise ValueError("pagination terminal page relationship is invalid")
    if terminal_count < 1 or terminal_count > 5:
        raise ValueError("pagination terminal report count is invalid")
    if summary.get("terminal_page") != terminal_page:
        raise ValueError("pagination terminal summary page mismatch")
    if summary.get("terminal_page_report_count") != terminal_count:
        raise ValueError("pagination terminal summary report count mismatch")
    return terminal_page, terminal_count, _required_integer(request.get("limit"), "limit")


def _validate_terminal_private(
    private: Mapping[str, Any],
    private_body: bytes,
    receipt: Mapping[str, Any],
    expected_guild_label: str,
    terminal_page: int,
) -> None:
    expected_root = {
        "schema_version": 1,
        "search_kind": _TERMINAL_PRIVATE_KIND,
        "search_version": _TERMINAL_VERSION,
        "target_guild_label": expected_guild_label,
    }
    for field_name, expected in expected_root.items():
        if private.get(field_name) != expected:
            raise ValueError(f"private pagination terminal mismatch: {field_name}")
    if _sha256_bytes(private_body) != receipt.get("source_private_search_sha256"):
        raise ValueError("private pagination terminal hash changed after verification")

    request = _required_object(private.get("request"), "private.request")
    receipt_request = _required_object(receipt.get("request"), "receipt.request")
    for field_name in (
        "route_template",
        "initial_lower_bound",
        "initial_upper_bound",
        "limit",
        "sort_by",
        "sort_order",
        "http_profile_version",
    ):
        if request.get(field_name) != receipt_request.get(field_name):
            raise ValueError(f"private pagination terminal request mismatch: {field_name}")

    rows = [
        _required_object(item, "private.pages[]")
        for item in _required_list(private.get("pages"), "private.pages")
    ]
    phases = {(row.get("phase"), row.get("page")): row for row in rows}
    for phase, page, expected_has_more, expected_count in (
        ("final_predecessor", terminal_page - 1, True, 5),
        (
            "final_terminal",
            terminal_page,
            False,
            _required_integer(
                _required_object(receipt.get("summary"), "summary").get(
                    "terminal_page_report_count"
                ),
                "terminal_page_report_count",
            ),
        ),
        ("final_successor", terminal_page + 1, False, 0),
    ):
        row = phases.get((phase, page))
        if row is None:
            raise ValueError(f"private pagination terminal is missing {phase}")
        pagination = _required_object(row.get("pagination"), f"private.pages[{phase}].pagination")
        if set(pagination) != _EXPECTED_PAGINATION_FIELDS:
            raise ValueError(f"private pagination terminal field set changed in {phase}")
        if _required_integer(pagination.get("page"), "pagination.page") != page:
            raise ValueError(f"private pagination terminal page relation failed in {phase}")
        if _required_integer(pagination.get("limit"), "pagination.limit") != 5:
            raise ValueError(f"private pagination terminal limit relation failed in {phase}")
        if _required_integer(pagination.get("offset"), "pagination.offset") != (page - 1) * 5:
            raise ValueError(f"private pagination terminal offset relation failed in {phase}")
        if _required_boolean(pagination.get("hasMore"), "pagination.hasMore") is not expected_has_more:
            raise ValueError(f"private pagination terminal hasMore relation failed in {phase}")
        report_ids = [
            _required_integer(value, f"private.pages[{phase}].source_report_ids[]")
            for value in _required_list(row.get("source_report_ids"), "source_report_ids")
        ]
        if len(report_ids) != expected_count:
            raise ValueError(f"private pagination terminal report count changed in {phase}")


def _validate_mapping(mapping: Mapping[str, Any]) -> None:
    expected_root = {
        "mapping_schema_version": 1,
        "mapping_id": "coa-public-report-discovery-v1",
        "status": "verified",
        "route_template": REPORTS_PUBLIC_ROUTE,
    }
    for field_name, expected in expected_root.items():
        if mapping.get(field_name) != expected:
            raise ValueError(f"public report mapping mismatch: {field_name}")
    collection = _required_object(mapping.get("collection"), "mapping.collection")
    if collection.get("path") != "/reports/*":
        raise ValueError("public report mapping collection path mismatch")
    required_keys = set(_required_list(collection.get("required_keys"), "required_keys"))
    if required_keys != _EXPECTED_REPORT_KEYS:
        raise ValueError("public report mapping required key set changed")
    fields = _required_object(collection.get("fields"), "mapping.collection.fields")
    expected_fields = {
        "source_report_id",
        "title",
        "created_at",
        "start_time",
        "end_time",
        "visibility",
        "uploader_username",
    }
    if set(fields) != expected_fields:
        raise ValueError("public report mapping verified field set changed")


def _sentinel_pages(terminal_page: int) -> tuple[int, ...]:
    values = {1, (terminal_page + 1) // 2, terminal_page - 1, terminal_page, terminal_page + 1}
    return tuple(sorted(values))


def _validate_report(report: Mapping[str, Any], page: int, index: int) -> dict[str, Any]:
    missing = _EXPECTED_REPORT_KEYS.difference(report)
    if missing:
        raise ValueError(
            f"public report page {page} record {index} is missing keys: {sorted(missing)}"
        )
    report_id = _required_integer(report.get("id"), f"reports[{index}].id")
    for field_name in _VERIFIED_STRING_FIELDS:
        value = report.get(field_name)
        if not isinstance(value, str):
            raise ValueError(
                f"public report page {page} record {index} field {field_name} must be a string"
            )
    prepared = dict(report)
    prepared["id"] = report_id
    return prepared


def _capture_page(
    registry: SourceRegistry,
    archive: RawArchive,
    session: SameOriginHttpSession,
    *,
    page: int,
    terminal_page: int,
    terminal_count: int,
    limit: int,
    phase: str,
    timeout_seconds: float,
    retry_count: int,
) -> dict[str, Any]:
    result = capture_public_report_discovery(
        registry,
        archive,
        local_category="argentum_public_report_manifest",
        page=page,
        limit=limit,
        timeout_seconds=timeout_seconds,
        retry_count=retry_count,
        session=session,
    )
    if not result.complete or result.capture is None:
        raise ValueError(f"public report manifest page {page} capture was incomplete: {result.error}")

    payload = _read_archived_payload(result.capture.payload_path)
    reports = _required_list(payload.get("reports"), f"page[{page}].reports")
    pagination = _required_object(payload.get("pagination"), f"page[{page}].pagination")
    if payload.get("success") is not True:
        raise ValueError(f"public report manifest page {page} did not report success=true")
    if set(pagination) != _EXPECTED_PAGINATION_FIELDS:
        raise ValueError(f"public report manifest page {page} pagination field set changed")

    observed_page = _required_integer(pagination.get("page"), "pagination.page")
    observed_limit = _required_integer(pagination.get("limit"), "pagination.limit")
    observed_offset = _required_integer(pagination.get("offset"), "pagination.offset")
    has_previous = _required_boolean(pagination.get("hasPrevious"), "pagination.hasPrevious")
    has_more = _required_boolean(pagination.get("hasMore"), "pagination.hasMore")
    expected_has_more = page < terminal_page
    expected_count = limit if page < terminal_page else terminal_count if page == terminal_page else 0
    if observed_page != page:
        raise ValueError(f"public report manifest page {page} did not echo the requested page")
    if observed_limit != limit:
        raise ValueError(f"public report manifest page {page} did not echo the requested limit")
    if observed_offset != (page - 1) * limit:
        raise ValueError(f"public report manifest page {page} offset relation failed")
    if has_previous != (page > 1):
        raise ValueError(f"public report manifest page {page} hasPrevious relation failed")
    if has_more is not expected_has_more:
        raise ValueError(f"public report manifest page {page} hasMore relation failed")
    if len(reports) != expected_count:
        raise ValueError(
            f"public report manifest page {page} expected {expected_count} reports, got {len(reports)}"
        )

    prepared_reports = [
        _validate_report(_required_object(raw, f"page[{page}].reports[{index}]"), page, index)
        for index, raw in enumerate(reports)
    ]
    report_ids = [int(report["id"]) for report in prepared_reports]
    if len(set(report_ids)) != len(report_ids):
        raise ValueError(f"public report manifest page {page} contains duplicate report ids")
    key_shapes = sorted({tuple(sorted(report)) for report in prepared_reports})
    return {
        "phase": phase,
        "page": page,
        "limit": limit,
        "raw_id": result.capture.raw_id,
        "observation_id": result.capture.observation_id,
        "payload_hash": result.capture.payload_hash,
        "schema_fingerprint": result.capture.schema_fingerprint,
        "pagination": pagination,
        "reports": prepared_reports,
        "report_count": len(prepared_reports),
        "report_id_set_sha256": _sha256_json(sorted(report_ids)),
        "report_record_sha256": _sha256_json(prepared_reports),
        "report_key_shapes_sha256": _sha256_json(key_shapes),
    }


def _new_checkpoint(
    *,
    terminal_receipt_path: Path,
    terminal_receipt_body: bytes,
    terminal_private_path: Path,
    terminal_private_body: bytes,
    mapping_path: Path,
    mapping_body: bytes,
    expected_guild_label: str,
    terminal_page: int,
    terminal_count: int,
    limit: int,
    sentinel_pages: tuple[int, ...],
) -> dict[str, Any]:
    return {
        "schema_version": _MANIFEST_SCHEMA_VERSION,
        "manifest_kind": "public_report_manifest_checkpoint",
        "manifest_version": _MANIFEST_VERSION,
        "created_at": _generated_at(),
        "updated_at": _generated_at(),
        "source_terminal_receipt_name": terminal_receipt_path.name,
        "source_terminal_receipt_sha256": _sha256_bytes(terminal_receipt_body),
        "source_terminal_private_name": terminal_private_path.name,
        "source_terminal_private_sha256": _sha256_bytes(terminal_private_body),
        "source_mapping_name": mapping_path.name,
        "source_mapping_sha256": _sha256_bytes(mapping_body),
        "target_guild_label": expected_guild_label,
        "request": {
            "route_template": REPORTS_PUBLIC_ROUTE,
            "first_page": 1,
            "terminal_page": terminal_page,
            "successor_page": terminal_page + 1,
            "limit": limit,
            "sort_by": "created_at",
            "sort_order": "desc",
            "sentinel_pages": list(sentinel_pages),
        },
        "expected": {
            "full_page_count": terminal_page - 1,
            "terminal_page_report_count": terminal_count,
            "expected_report_count": (terminal_page - 1) * limit + terminal_count,
        },
        "start_sentinels": {},
        "pages": {},
        "end_sentinels": {},
        "summary": {
            "completed_page_count": 0,
            "contains_source_scalar_values": True,
            "finalized": False,
        },
    }


def _validate_checkpoint(
    checkpoint: Mapping[str, Any],
    *,
    terminal_receipt_body: bytes,
    terminal_private_body: bytes,
    mapping_body: bytes,
    expected_guild_label: str,
    terminal_page: int,
    terminal_count: int,
    limit: int,
    sentinel_pages: tuple[int, ...],
) -> None:
    expected_root = {
        "schema_version": 1,
        "manifest_kind": "public_report_manifest_checkpoint",
        "manifest_version": _MANIFEST_VERSION,
        "source_terminal_receipt_sha256": _sha256_bytes(terminal_receipt_body),
        "source_terminal_private_sha256": _sha256_bytes(terminal_private_body),
        "source_mapping_sha256": _sha256_bytes(mapping_body),
        "target_guild_label": expected_guild_label,
    }
    for field_name, expected in expected_root.items():
        if checkpoint.get(field_name) != expected:
            raise ValueError(f"public report manifest checkpoint mismatch: {field_name}")
    request = _required_object(checkpoint.get("request"), "checkpoint.request")
    expected_request = {
        "route_template": REPORTS_PUBLIC_ROUTE,
        "first_page": 1,
        "terminal_page": terminal_page,
        "successor_page": terminal_page + 1,
        "limit": limit,
        "sort_by": "created_at",
        "sort_order": "desc",
        "sentinel_pages": list(sentinel_pages),
    }
    for field_name, expected in expected_request.items():
        if request.get(field_name) != expected:
            raise ValueError(f"public report manifest checkpoint request mismatch: {field_name}")
    expected = _required_object(checkpoint.get("expected"), "checkpoint.expected")
    if expected.get("terminal_page_report_count") != terminal_count:
        raise ValueError("public report manifest checkpoint terminal count mismatch")


def _notify(callback: ProgressCallback | None, phase: str, current: int, total: int) -> None:
    if callback is not None:
        callback(phase, current, total)


def _sleep(delay_seconds: float, sleep_fn: Callable[[float], None]) -> None:
    if delay_seconds > 0:
        sleep_fn(delay_seconds)


def capture_public_report_manifest(
    registry: SourceRegistry,
    archive: RawArchive,
    *,
    terminal_receipt_path: Path,
    terminal_private_path: Path,
    mapping_path: Path,
    checkpoint_path: Path,
    private_output_path: Path,
    receipt_output_path: Path,
    expected_guild_label: str = "Argentum",
    timeout_seconds: float = 20.0,
    retry_count: int = 1,
    request_delay_seconds: float = 0.15,
    resume: bool = True,
    opener: Any | None = None,
    progress_callback: ProgressCallback | None = None,
    sleep_fn: Callable[[float], None] = time.sleep,
) -> dict[str, Any]:
    """Capture the verified public-report page range with checkpointed scalar-private state."""
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be greater than zero")
    if retry_count < 0 or retry_count > 1:
        raise ValueError("retry_count must be between 0 and 1")
    if request_delay_seconds < 0 or request_delay_seconds > 5:
        raise ValueError("request_delay_seconds must be between 0 and 5")

    terminal_receipt, terminal_receipt_body = _load_object(
        terminal_receipt_path, "pagination terminal receipt"
    )
    terminal_private, terminal_private_body = _load_object(
        terminal_private_path, "private pagination terminal search"
    )
    mapping, mapping_body = _load_object(mapping_path, "public report mapping")
    terminal_page, terminal_count, limit = _validate_terminal_receipt(
        terminal_receipt, expected_guild_label
    )
    _validate_terminal_private(
        terminal_private,
        terminal_private_body,
        terminal_receipt,
        expected_guild_label,
        terminal_page,
    )
    _validate_mapping(mapping)
    sentinels = _sentinel_pages(terminal_page)

    if checkpoint_path.exists():
        if not resume:
            raise ValueError("public report manifest checkpoint exists but resume is disabled")
        checkpoint, _ = _load_object(checkpoint_path, "public report manifest checkpoint")
        _validate_checkpoint(
            checkpoint,
            terminal_receipt_body=terminal_receipt_body,
            terminal_private_body=terminal_private_body,
            mapping_body=mapping_body,
            expected_guild_label=expected_guild_label,
            terminal_page=terminal_page,
            terminal_count=terminal_count,
            limit=limit,
            sentinel_pages=sentinels,
        )
    else:
        checkpoint = _new_checkpoint(
            terminal_receipt_path=terminal_receipt_path,
            terminal_receipt_body=terminal_receipt_body,
            terminal_private_path=terminal_private_path,
            terminal_private_body=terminal_private_body,
            mapping_path=mapping_path,
            mapping_body=mapping_body,
            expected_guild_label=expected_guild_label,
            terminal_page=terminal_page,
            terminal_count=terminal_count,
            limit=limit,
            sentinel_pages=sentinels,
        )
        _write_json(checkpoint_path, checkpoint)

    session = SameOriginHttpSession(registry.base_url, opener=opener)
    start_sentinels = _required_object(checkpoint.get("start_sentinels"), "start_sentinels")
    pages = _required_object(checkpoint.get("pages"), "pages")

    for index, page in enumerate(sentinels, start=1):
        key = str(page)
        if key not in start_sentinels:
            start_sentinels[key] = _capture_page(
                registry,
                archive,
                session,
                page=page,
                terminal_page=terminal_page,
                terminal_count=terminal_count,
                limit=limit,
                phase="start_sentinel",
                timeout_seconds=timeout_seconds,
                retry_count=retry_count,
            )
            checkpoint["updated_at"] = _generated_at()
            _write_json(checkpoint_path, checkpoint)
            _sleep(request_delay_seconds, sleep_fn)
        _notify(progress_callback, "start_sentinel", index, len(sentinels))

    for page in range(1, terminal_page + 1):
        key = str(page)
        if key not in pages:
            pages[key] = _capture_page(
                registry,
                archive,
                session,
                page=page,
                terminal_page=terminal_page,
                terminal_count=terminal_count,
                limit=limit,
                phase="manifest_page",
                timeout_seconds=timeout_seconds,
                retry_count=retry_count,
            )
            checkpoint["updated_at"] = _generated_at()
            checkpoint["summary"] = {
                "completed_page_count": len(pages),
                "contains_source_scalar_values": True,
                "finalized": False,
            }
            _write_json(checkpoint_path, checkpoint)
            _sleep(request_delay_seconds, sleep_fn)
        _notify(progress_callback, "manifest_page", page, terminal_page)

    end_sentinels: dict[str, Any] = {}
    for index, page in enumerate(sentinels, start=1):
        end_sentinels[str(page)] = _capture_page(
            registry,
            archive,
            session,
            page=page,
            terminal_page=terminal_page,
            terminal_count=terminal_count,
            limit=limit,
            phase="end_sentinel",
            timeout_seconds=timeout_seconds,
            retry_count=retry_count,
        )
        _sleep(request_delay_seconds, sleep_fn)
        _notify(progress_callback, "end_sentinel", index, len(sentinels))
    checkpoint["end_sentinels"] = end_sentinels
    checkpoint["updated_at"] = _generated_at()
    _write_json(checkpoint_path, checkpoint)

    sentinel_payloads_stable = all(
        _required_object(start_sentinels[str(page)], "start_sentinel").get("payload_hash")
        == _required_object(end_sentinels[str(page)], "end_sentinel").get("payload_hash")
        for page in sentinels
    )
    if not sentinel_payloads_stable:
        raise ValueError("public report manifest sentinel payload changed during capture")
    sentinel_sweep_matches = all(
        page == terminal_page + 1
        or _required_object(pages[str(page)], "pages[]").get("payload_hash")
        == _required_object(start_sentinels[str(page)], "start_sentinel").get("payload_hash")
        for page in sentinels
    )
    if not sentinel_sweep_matches:
        raise ValueError("public report manifest sweep does not match sentinel payload")

    ordered_pages = [_required_object(pages[str(page)], f"pages[{page}]") for page in range(1, terminal_page + 1)]
    ordered_reports = [
        _required_object(report, "pages[].reports[]")
        for page_row in ordered_pages
        for report in _required_list(page_row.get("reports"), "pages[].reports")
    ]
    ordered_ids = [_required_integer(report.get("id"), "reports[].id") for report in ordered_reports]
    expected_report_count = (terminal_page - 1) * limit + terminal_count
    if len(ordered_reports) != expected_report_count:
        raise ValueError("public report manifest aggregate report count mismatch")
    if len(set(ordered_ids)) != len(ordered_ids):
        raise ValueError("public report manifest contains cross-page duplicate report ids")

    schema_fingerprints = sorted({str(row.get("schema_fingerprint")) for row in ordered_pages})
    report_key_shapes = sorted({tuple(sorted(report)) for report in ordered_reports})
    guild_id_values = [report.get("guild_id") for report in ordered_reports]
    guild_name_values = [report.get("guild_name") for report in ordered_reports]
    non_null_guild_ids = {value for value in guild_id_values if value is not None}
    non_empty_guild_names = {
        value.strip()
        for value in guild_name_values
        if isinstance(value, str) and value.strip()
    }
    reports_with_both_guild_fields = sum(
        guild_id is not None and isinstance(guild_name, str) and bool(guild_name.strip())
        for guild_id, guild_name in zip(guild_id_values, guild_name_values, strict=True)
    )
    guild_identity_pairs = {
        (report.get("guild_id"), report.get("guild_name").strip())
        for report in ordered_reports
        if report.get("guild_id") is not None
        and isinstance(report.get("guild_name"), str)
        and report.get("guild_name").strip()
    }
    normalized_target = expected_guild_label.strip().casefold()
    target_name_match_count = sum(
        isinstance(value, str) and value.strip().casefold() == normalized_target
        for value in guild_name_values
    )
    target_identity_ids = {
        report.get("guild_id")
        for report in ordered_reports
        if report.get("guild_id") is not None
        and isinstance(report.get("guild_name"), str)
        and report.get("guild_name").strip().casefold() == normalized_target
    }

    private_manifest = {
        "schema_version": _MANIFEST_SCHEMA_VERSION,
        "manifest_kind": "public_report_manifest_private_batch",
        "manifest_version": _MANIFEST_VERSION,
        "generated_at": _generated_at(),
        "source_terminal_receipt_name": terminal_receipt_path.name,
        "source_terminal_receipt_sha256": _sha256_bytes(terminal_receipt_body),
        "source_terminal_private_name": terminal_private_path.name,
        "source_terminal_private_sha256": _sha256_bytes(terminal_private_body),
        "source_mapping_name": mapping_path.name,
        "source_mapping_sha256": _sha256_bytes(mapping_body),
        "target_guild_label": expected_guild_label,
        "request": checkpoint["request"],
        "sentinel_pages": list(sentinels),
        "start_sentinels": start_sentinels,
        "pages": ordered_pages,
        "end_sentinels": end_sentinels,
        "reports": ordered_reports,
        "summary": {
            "page_count": terminal_page,
            "report_count": len(ordered_reports),
            "unique_report_id_count": len(set(ordered_ids)),
            "contains_source_scalar_values": True,
        },
    }
    private_body = _write_json(private_output_path, private_manifest)

    checks = {
        "terminal_receipt_verified": True,
        "terminal_private_sha256_verified": True,
        "verified_mapping_loaded": True,
        "checkpoint_contract_verified": True,
        "all_manifest_pages_archived": True,
        "all_manifest_pages_completed": True,
        "page_relation_verified_on_all_pages": True,
        "limit_relation_verified_on_all_pages": True,
        "offset_relation_verified_on_all_pages": True,
        "has_previous_relation_verified_on_all_pages": True,
        "has_more_relation_verified_on_all_pages": True,
        "full_page_counts_verified": True,
        "terminal_page_count_verified": True,
        "sentinel_payload_stability_verified": True,
        "sentinel_sweep_consistency_verified": True,
        "cross_page_report_ids_unique": True,
        "expected_manifest_count_verified": True,
        "private_manifest_written": True,
        "scalar_free_receipt_boundary_preserved": True,
    }
    ready_for_guild_identity_review = target_name_match_count > 0
    receipt = {
        "schema_version": _MANIFEST_SCHEMA_VERSION,
        "manifest_kind": "public_report_manifest_capture",
        "manifest_version": _MANIFEST_VERSION,
        "generated_at": _generated_at(),
        "source_terminal_receipt_name": terminal_receipt_path.name,
        "source_terminal_receipt_sha256": _sha256_bytes(terminal_receipt_body),
        "source_terminal_private_name": terminal_private_path.name,
        "source_terminal_private_sha256": _sha256_bytes(terminal_private_body),
        "source_mapping_name": mapping_path.name,
        "source_mapping_sha256": _sha256_bytes(mapping_body),
        "source_private_manifest_name": private_output_path.name,
        "source_private_manifest_sha256": _sha256_bytes(private_body),
        "target": {
            "guild_label": expected_guild_label,
            "guild_identity_status": "operator_named_target_unresolved",
        },
        "request": checkpoint["request"],
        "manifest_hashes": {
            "ordered_report_ids_sha256": _sha256_json(ordered_ids),
            "ordered_report_records_sha256": _sha256_json(ordered_reports),
            "report_key_shapes_sha256": _sha256_json(report_key_shapes),
            "page_payload_hashes_sha256": _sha256_json(
                [str(row.get("payload_hash")) for row in ordered_pages]
            ),
        },
        "shape_summary": {
            "distinct_page_schema_fingerprint_count": len(schema_fingerprints),
            "distinct_report_key_shape_count": len(report_key_shapes),
            "all_reports_contain_required_keys": True,
        },
        "guild_field_summary": {
            "report_count_with_non_null_guild_id": sum(value is not None for value in guild_id_values),
            "report_count_with_non_empty_guild_name": sum(
                isinstance(value, str) and bool(value.strip()) for value in guild_name_values
            ),
            "report_count_with_both_guild_fields": reports_with_both_guild_fields,
            "distinct_non_null_guild_id_count": len(non_null_guild_ids),
            "distinct_non_empty_guild_name_count": len(non_empty_guild_names),
            "distinct_guild_identity_pair_count": len(guild_identity_pairs),
            "target_label_exact_match_report_count": target_name_match_count,
            "target_label_distinct_non_null_guild_id_count": len(target_identity_ids),
        },
        "sentinel_summary": {
            "sentinel_pages": list(sentinels),
            "sentinel_page_count": len(sentinels),
            "all_start_end_payload_hashes_equal": True,
            "all_sweep_payload_hashes_match_sentinels": True,
        },
        "integrity_checks": checks,
        "decision_boundary": {
            "status": "exhaustive_public_report_manifest_captured",
            "pagination_terminal_contract_verified": True,
            "manifest_page_range_completed": True,
            "manifest_report_ids_unique": True,
            "sentinel_stability_verified": True,
            "guild_identity_verified": False,
            "ready_for_guild_identity_review": ready_for_guild_identity_review,
            "ready_for_guild_filtering": False,
            "ready_for_full_guild_crawl": False,
            "ready_for_multi_report_character_graph": False,
            "ready_for_performance_model": False,
            "ready_for_global_benchmark": False,
            "ready_for_bis25_scoring": False,
            "planner_scoring_allowed": False,
            "private_manifest_contains_source_scalar_values": True,
        },
        "summary": {
            "first_page": 1,
            "terminal_page": terminal_page,
            "successor_page": terminal_page + 1,
            "completed_page_count": terminal_page,
            "full_page_count": terminal_page - 1,
            "terminal_page_report_count": terminal_count,
            "expected_report_count": expected_report_count,
            "report_occurrence_count": len(ordered_reports),
            "unique_report_id_count": len(set(ordered_ids)),
            "duplicate_report_occurrence_count": 0,
            "integrity_check_count": len(checks),
            "all_integrity_checks_passed": True,
            "contains_source_scalar_values": False,
            "private_manifest_contains_source_scalar_values": True,
            "resume_checkpoint_used": checkpoint_path.exists(),
            "ready_for_guild_identity_review": ready_for_guild_identity_review,
            "ready_for_guild_filtering": False,
            "ready_for_full_guild_crawl": False,
            "ready_for_bis25_scoring": False,
        },
    }
    _write_json(receipt_output_path, receipt)
    checkpoint["summary"] = {
        "completed_page_count": terminal_page,
        "contains_source_scalar_values": True,
        "finalized": True,
        "private_manifest_sha256": _sha256_bytes(private_body),
        "receipt_sha256": _sha256_bytes(receipt_output_path.read_bytes()),
    }
    checkpoint["updated_at"] = _generated_at()
    _write_json(checkpoint_path, checkpoint)
    return receipt
