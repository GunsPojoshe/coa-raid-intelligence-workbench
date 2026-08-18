from __future__ import annotations

import gzip
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from .http_profile import SameOriginHttpSession
from .raw_archive import RawArchive
from .report_discovery import REPORTS_PUBLIC_ROUTE, capture_public_report_discovery
from .source_registry import SourceRegistry

_SEARCH_SCHEMA_VERSION = 1
_SEARCH_VERSION = "report-pagination-terminal-search-v1"
_BOUNDARY_KIND = "report_pagination_boundary_probe"
_BOUNDARY_PRIVATE_KIND = "report_pagination_boundary_private_batch"
_BOUNDARY_VERSION = "report-pagination-boundary-probe-v1"
_EXPECTED_FIELDS = {"hasMore", "hasPrevious", "limit", "offset", "page"}


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
        raise ValueError(f"pagination terminal search field {field_name} must be an object")
    return value


def _required_list(value: object, field_name: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"pagination terminal search field {field_name} must be an array")
    return value


def _required_integer(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"pagination terminal search field {field_name} must be an integer")
    return value


def _required_boolean(value: object, field_name: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"pagination terminal search field {field_name} must be a boolean")
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
        raise ValueError("report pagination terminal page must contain a JSON object")
    return payload


def _validate_boundary_receipt(
    receipt: Mapping[str, Any], expected_guild_label: str
) -> tuple[int, int, int]:
    expected_root = {
        "schema_version": 1,
        "probe_kind": _BOUNDARY_KIND,
        "probe_version": _BOUNDARY_VERSION,
    }
    for field_name, expected in expected_root.items():
        if receipt.get(field_name) != expected:
            raise ValueError(f"pagination boundary receipt mismatch: {field_name}")

    target = _required_object(receipt.get("target"), "target")
    if target.get("guild_label") != expected_guild_label:
        raise ValueError("pagination boundary guild label mismatch")
    if target.get("guild_identity_status") != "operator_named_target_unresolved":
        raise ValueError("guild identity was unexpectedly resolved before terminal search")

    request = _required_object(receipt.get("request"), "request")
    if request.get("route_template") != REPORTS_PUBLIC_ROUTE:
        raise ValueError("pagination boundary route mismatch")
    if request.get("limit") != 5:
        raise ValueError("pagination boundary limit mismatch")
    if request.get("sort_by") != "created_at" or request.get("sort_order") != "desc":
        raise ValueError("pagination boundary sorting mismatch")

    summary = _required_object(receipt.get("summary"), "summary")
    expected_summary = {
        "all_integrity_checks_passed": True,
        "terminal_bracket_observed": True,
        "ready_for_bounded_terminal_search": True,
        "ready_for_exhaustive_public_report_manifest_capture": False,
        "ready_for_full_guild_crawl": False,
        "ready_for_bis25_scoring": False,
        "contains_source_scalar_values": False,
        "private_probe_contains_source_scalar_values": True,
    }
    for field_name, expected in expected_summary.items():
        if summary.get(field_name) != expected:
            raise ValueError(f"pagination boundary summary mismatch: {field_name}")

    boundary = _required_object(receipt.get("decision_boundary"), "decision_boundary")
    expected_boundary = {
        "status": "bounded_pagination_boundary_probe_completed",
        "page_semantics_verified": True,
        "page_size_semantics_verified": True,
        "offset_semantics_verified": True,
        "has_previous_semantics_verified": True,
        "has_more_semantics_verified": False,
        "termination_condition_verified": False,
        "terminal_bracket_observed": True,
        "ready_for_bounded_terminal_search": True,
        "automatic_full_manifest_collection_allowed": False,
        "ready_for_exhaustive_public_report_manifest_capture": False,
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
            raise ValueError(f"pagination boundary decision mismatch: {field_name}")

    observation = _required_object(receipt.get("boundary_observation"), "boundary_observation")
    lower = _required_integer(
        observation.get("highest_more_pages_candidate"),
        "boundary_observation.highest_more_pages_candidate",
    )
    upper = _required_integer(
        observation.get("lowest_terminal_candidate"),
        "boundary_observation.lowest_terminal_candidate",
    )
    if observation.get("terminal_bracket_observed") is not True:
        raise ValueError("pagination boundary receipt does not contain a terminal bracket")
    if observation.get("monotonic_has_more_candidate") is not True:
        raise ValueError("pagination boundary receipt is not monotonic")
    if lower < 1 or upper <= lower:
        raise ValueError("pagination boundary bounds are invalid")
    return lower, upper, _required_integer(request.get("limit"), "request.limit")


def _validate_boundary_private(
    private: Mapping[str, Any],
    private_body: bytes,
    receipt: Mapping[str, Any],
    expected_guild_label: str,
    lower: int,
    upper: int,
) -> None:
    expected_root = {
        "schema_version": 1,
        "probe_kind": _BOUNDARY_PRIVATE_KIND,
        "probe_version": _BOUNDARY_VERSION,
        "target_guild_label": expected_guild_label,
    }
    for field_name, expected in expected_root.items():
        if private.get(field_name) != expected:
            raise ValueError(f"private pagination boundary mismatch: {field_name}")
    if _sha256_bytes(private_body) != receipt.get("source_private_probe_sha256"):
        raise ValueError("private pagination boundary hash changed after probe")

    private_request = _required_object(private.get("request"), "private.request")
    receipt_request = _required_object(receipt.get("request"), "receipt.request")
    for field_name in (
        "route_template",
        "probe_pages",
        "limit",
        "sort_by",
        "sort_order",
        "http_profile_version",
    ):
        if private_request.get(field_name) != receipt_request.get(field_name):
            raise ValueError(f"private pagination boundary request mismatch: {field_name}")

    pages = {
        _required_integer(row.get("page"), "private.pages[].page"): row
        for row in (
            _required_object(item, "private.pages[]")
            for item in _required_list(private.get("pages"), "private.pages")
        )
    }
    for page, expected_has_more in ((lower, True), (upper, False)):
        row = pages.get(page)
        if row is None:
            raise ValueError(f"private pagination boundary is missing page {page}")
        pagination = _required_object(row.get("pagination"), f"private.pages[{page}].pagination")
        if set(pagination) != _EXPECTED_FIELDS:
            raise ValueError(f"private pagination boundary page {page} field set changed")
        limit = _required_integer(pagination.get("limit"), "pagination.limit")
        if _required_integer(pagination.get("page"), "pagination.page") != page:
            raise ValueError(f"private pagination boundary page relation failed on {page}")
        if _required_integer(pagination.get("offset"), "pagination.offset") != (page - 1) * limit:
            raise ValueError(f"private pagination boundary offset relation failed on {page}")
        if _required_boolean(pagination.get("hasPrevious"), "pagination.hasPrevious") != (page > 1):
            raise ValueError(f"private pagination boundary hasPrevious relation failed on {page}")
        if _required_boolean(pagination.get("hasMore"), "pagination.hasMore") is not expected_has_more:
            raise ValueError(f"private pagination boundary hasMore state changed on {page}")


def _capture_page(
    registry: SourceRegistry,
    archive: RawArchive,
    session: SameOriginHttpSession,
    *,
    page: int,
    limit: int,
    phase: str,
    timeout_seconds: float,
    retry_count: int,
) -> tuple[dict[str, Any], dict[str, Any], bool, set[int]]:
    result = capture_public_report_discovery(
        registry,
        archive,
        local_category="argentum_pagination_terminal_search",
        page=page,
        limit=limit,
        timeout_seconds=timeout_seconds,
        retry_count=retry_count,
        session=session,
    )
    if not result.complete or result.capture is None:
        raise ValueError(f"pagination terminal page {page} capture was incomplete: {result.error}")

    payload = _read_archived_payload(result.capture.payload_path)
    reports = _required_list(payload.get("reports"), f"page[{page}].reports")
    pagination = _required_object(payload.get("pagination"), f"page[{page}].pagination")
    if payload.get("success") is not True:
        raise ValueError(f"pagination terminal page {page} did not report success=true")
    if set(pagination) != _EXPECTED_FIELDS:
        raise ValueError(f"pagination terminal page {page} field set changed")

    observed_page = _required_integer(pagination.get("page"), "pagination.page")
    observed_limit = _required_integer(pagination.get("limit"), "pagination.limit")
    observed_offset = _required_integer(pagination.get("offset"), "pagination.offset")
    has_previous = _required_boolean(pagination.get("hasPrevious"), "pagination.hasPrevious")
    has_more = _required_boolean(pagination.get("hasMore"), "pagination.hasMore")
    if observed_page != page:
        raise ValueError(f"pagination terminal page {page} did not echo the requested page")
    if observed_limit != limit:
        raise ValueError(f"pagination terminal page {page} did not echo the requested limit")
    if observed_offset != (page - 1) * limit:
        raise ValueError(f"pagination terminal page {page} offset relation failed")
    if has_previous != (page > 1):
        raise ValueError(f"pagination terminal page {page} hasPrevious relation failed")

    report_ids: list[int] = []
    for index, raw_report in enumerate(reports):
        report = _required_object(raw_report, f"page[{page}].reports[{index}]")
        report_ids.append(_required_integer(report.get("id"), f"page[{page}].reports[{index}].id"))
    unique_report_ids = set(report_ids)
    if len(unique_report_ids) != len(report_ids):
        raise ValueError(f"pagination terminal page {page} contains duplicate report ids")

    private_row = {
        "phase": phase,
        "page": page,
        "limit": limit,
        "raw_id": result.capture.raw_id,
        "observation_id": result.capture.observation_id,
        "payload_hash": result.capture.payload_hash,
        "schema_fingerprint": result.capture.schema_fingerprint,
        "source_report_ids": report_ids,
        "pagination": pagination,
        "report_count": len(report_ids),
    }
    receipt_row = {
        "phase": phase,
        "requested_page": page,
        "limit": limit,
        "http_status": result.status,
        "raw_id": result.capture.raw_id,
        "observation_id": result.capture.observation_id,
        "payload_hash": result.capture.payload_hash,
        "schema_fingerprint": result.capture.schema_fingerprint,
        "report_occurrence_count": len(report_ids),
        "unique_report_id_count": len(unique_report_ids),
        "report_id_set_sha256": _sha256_json(sorted(unique_report_ids)),
        "has_more_state": "more_pages" if has_more else "terminal",
        "short_page": len(report_ids) < limit,
        "empty_page": not report_ids,
        "page_relation_verified": True,
        "limit_relation_verified": True,
        "offset_relation_verified": True,
        "has_previous_relation_verified": True,
    }
    return private_row, receipt_row, has_more, unique_report_ids


def capture_report_pagination_terminal_search(
    registry: SourceRegistry,
    archive: RawArchive,
    *,
    boundary_receipt_path: Path,
    boundary_private_path: Path,
    private_output_path: Path,
    receipt_output_path: Path,
    expected_guild_label: str = "Argentum",
    max_requests: int = 16,
    timeout_seconds: float = 20.0,
    retry_count: int = 0,
    opener: Any | None = None,
) -> dict[str, Any]:
    """Find and verify the adjacent hasMore transition inside a reviewed bracket."""
    if max_requests < 4 or max_requests > 20:
        raise ValueError("max_requests must be between 4 and 20")
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be greater than zero")
    if retry_count < 0 or retry_count > 1:
        raise ValueError("retry_count must be between 0 and 1")

    boundary, boundary_body = _load_object(boundary_receipt_path, "pagination boundary receipt")
    private_boundary, private_boundary_body = _load_object(
        boundary_private_path, "private pagination boundary"
    )
    lower, upper, limit = _validate_boundary_receipt(boundary, expected_guild_label)
    _validate_boundary_private(
        private_boundary,
        private_boundary_body,
        boundary,
        expected_guild_label,
        lower,
        upper,
    )

    required_midpoint_requests = (upper - lower - 1).bit_length()
    required_request_budget = required_midpoint_requests + 3
    if max_requests < required_request_budget:
        raise ValueError(
            "max_requests is too small for the reviewed bracket and final three-page verification"
        )

    session = SameOriginHttpSession(registry.base_url, opener=opener)
    private_rows: list[dict[str, Any]] = []
    receipt_rows: list[dict[str, Any]] = []
    request_count = 0

    def capture(page: int, phase: str) -> tuple[bool, set[int]]:
        nonlocal request_count
        if request_count >= max_requests:
            raise ValueError("pagination terminal search exceeded its fixed request budget")
        private_row, receipt_row, has_more, report_ids = _capture_page(
            registry,
            archive,
            session,
            page=page,
            limit=limit,
            phase=phase,
            timeout_seconds=timeout_seconds,
            retry_count=retry_count,
        )
        request_count += 1
        private_rows.append(private_row)
        receipt_rows.append(receipt_row)
        return has_more, report_ids

    search_lower = lower
    search_upper = upper
    midpoint_count = 0
    while search_upper - search_lower > 1:
        midpoint = (search_lower + search_upper) // 2
        has_more, _ = capture(midpoint, "binary_search")
        midpoint_count += 1
        if has_more:
            search_lower = midpoint
        else:
            search_upper = midpoint

    predecessor = search_lower
    terminal = search_upper
    successor = terminal + 1
    predecessor_has_more, predecessor_ids = capture(predecessor, "final_predecessor")
    terminal_has_more, terminal_ids = capture(terminal, "final_terminal")
    successor_has_more, successor_ids = capture(successor, "final_successor")

    final_rows = receipt_rows[-3:]
    predecessor_count = int(final_rows[0]["report_occurrence_count"])
    terminal_count = int(final_rows[1]["report_occurrence_count"])
    successor_count = int(final_rows[2]["report_occurrence_count"])
    if predecessor_has_more is not True:
        raise ValueError("final predecessor page does not have hasMore=true")
    if terminal_has_more is not False:
        raise ValueError("final terminal page does not have hasMore=false")
    if successor_has_more is not False:
        raise ValueError("final successor page does not have hasMore=false")
    if predecessor_count != limit:
        raise ValueError("final predecessor page is not a full page")
    if terminal_count < 1 or terminal_count > limit:
        raise ValueError("final terminal page must contain between one and limit reports")
    if successor_count != 0 or successor_ids:
        raise ValueError("final successor page must be empty")
    if predecessor_ids & terminal_ids:
        raise ValueError("final predecessor and terminal pages contain overlapping report ids")

    private_payload = {
        "schema_version": _SEARCH_SCHEMA_VERSION,
        "search_kind": "report_pagination_terminal_search_private_batch",
        "search_version": _SEARCH_VERSION,
        "generated_at": _generated_at(),
        "source_boundary_receipt_name": boundary_receipt_path.name,
        "source_boundary_receipt_sha256": _sha256_bytes(boundary_body),
        "source_boundary_private_name": boundary_private_path.name,
        "source_boundary_private_sha256": _sha256_bytes(private_boundary_body),
        "target_guild_label": expected_guild_label,
        "request": {
            "route_template": REPORTS_PUBLIC_ROUTE,
            "initial_lower_bound": lower,
            "initial_upper_bound": upper,
            "limit": limit,
            "max_requests": max_requests,
            "sort_by": "created_at",
            "sort_order": "desc",
            "http_profile_version": session.profile.version,
        },
        "pages": private_rows,
        "result": {
            "predecessor_page": predecessor,
            "terminal_page": terminal,
            "successor_page": successor,
            "terminal_page_report_count": terminal_count,
            "contains_source_scalar_values": True,
        },
    }
    private_body = _write_json(private_output_path, private_payload)

    checks = {
        "boundary_receipt_verified": True,
        "boundary_private_sha256_verified": True,
        "terminal_bracket_verified": True,
        "fixed_request_budget_verified": True,
        "all_search_pages_archived": True,
        "all_search_pages_completed": True,
        "page_relation_verified_on_all_pages": True,
        "limit_relation_verified_on_all_pages": True,
        "offset_relation_verified_on_all_pages": True,
        "has_previous_relation_verified_on_all_pages": True,
        "adjacent_has_more_transition_verified": True,
        "terminal_page_nonempty_verified": True,
        "successor_page_empty_verified": True,
        "final_adjacent_report_ids_disjoint": True,
        "private_search_written": True,
        "scalar_free_receipt_boundary_preserved": True,
    }
    receipt = {
        "schema_version": _SEARCH_SCHEMA_VERSION,
        "search_kind": "report_pagination_terminal_search",
        "search_version": _SEARCH_VERSION,
        "generated_at": _generated_at(),
        "source_boundary_receipt_name": boundary_receipt_path.name,
        "source_boundary_receipt_sha256": _sha256_bytes(boundary_body),
        "source_boundary_private_name": boundary_private_path.name,
        "source_boundary_private_sha256": _sha256_bytes(private_boundary_body),
        "source_private_search_name": private_output_path.name,
        "source_private_search_sha256": _sha256_bytes(private_body),
        "target": {
            "guild_label": expected_guild_label,
            "guild_identity_status": "operator_named_target_unresolved",
        },
        "request": {
            "route_template": REPORTS_PUBLIC_ROUTE,
            "initial_lower_bound": lower,
            "initial_upper_bound": upper,
            "limit": limit,
            "max_requests": max_requests,
            "sort_by": "created_at",
            "sort_order": "desc",
            "http_profile_version": session.profile.version,
        },
        "pages": receipt_rows,
        "terminal_contract": {
            "status": "verified_adjacent_transition",
            "strategy": "request_pages_1_through_terminal_page_inclusive",
            "predecessor_page": predecessor,
            "terminal_page": terminal,
            "successor_page": successor,
            "terminal_page_report_count": terminal_count,
            "inclusive_terminal_page": True,
            "deduplication_key": "/reports/*/id",
            "automatic_network_collection_allowed": False,
        },
        "integrity_checks": checks,
        "decision_boundary": {
            "status": "pagination_terminal_contract_verified",
            "page_semantics_verified": True,
            "page_size_semantics_verified": True,
            "offset_semantics_verified": True,
            "has_previous_semantics_verified": True,
            "has_more_semantics_verified": True,
            "termination_condition_verified": True,
            "terminal_page_verified": True,
            "cross_page_deduplication_key": "/reports/*/id",
            "cross_page_deduplication_policy_verified": False,
            "automatic_full_manifest_collection_allowed": False,
            "ready_for_exhaustive_public_report_manifest_capture": True,
            "ready_for_full_guild_crawl": False,
            "ready_for_guild_identity_review": False,
            "ready_for_guild_filtering": False,
            "ready_for_multi_report_character_graph": False,
            "ready_for_performance_model": False,
            "ready_for_global_benchmark": False,
            "ready_for_bis25_scoring": False,
            "planner_scoring_allowed": False,
            "private_search_contains_source_scalar_values": True,
        },
        "summary": {
            "initial_lower_bound": lower,
            "initial_upper_bound": upper,
            "midpoint_request_count": midpoint_count,
            "final_verification_request_count": 3,
            "completed_request_count": request_count,
            "maximum_request_count": max_requests,
            "predecessor_page": predecessor,
            "terminal_page": terminal,
            "successor_page": successor,
            "predecessor_report_count": predecessor_count,
            "terminal_page_report_count": terminal_count,
            "successor_report_count": successor_count,
            "integrity_check_count": len(checks),
            "all_integrity_checks_passed": True,
            "contains_source_scalar_values": False,
            "private_search_contains_source_scalar_values": True,
            "ready_for_exhaustive_public_report_manifest_capture": True,
            "ready_for_full_guild_crawl": False,
            "ready_for_bis25_scoring": False,
        },
    }
    _write_json(receipt_output_path, receipt)
    return receipt
