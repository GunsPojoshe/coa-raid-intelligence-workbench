from __future__ import annotations

import gzip
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

from .http_profile import SameOriginHttpSession
from .raw_archive import RawArchive
from .report_discovery import REPORTS_PUBLIC_ROUTE, capture_public_report_discovery
from .source_registry import SourceRegistry

_PROBE_SCHEMA_VERSION = 1
_PROBE_VERSION = "report-pagination-boundary-probe-v1"
_REVIEW_KIND = "report_pagination_semantic_review"
_REVIEW_VERSION = "report-pagination-semantic-review-v1"
_PRIVATE_KIND = "bounded_report_pagination_private_batch"
_PRIVATE_VERSION = "report-pagination-evidence-v1"
_DEFAULT_PROBE_PAGES = (4, 64, 1024, 8192, 65536)
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
        raise ValueError(f"pagination boundary probe field {field_name} must be an object")
    return value


def _required_list(value: object, field_name: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"pagination boundary probe field {field_name} must be an array")
    return value


def _required_integer(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"pagination boundary probe field {field_name} must be an integer")
    return value


def _required_boolean(value: object, field_name: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"pagination boundary probe field {field_name} must be a boolean")
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
        raise ValueError("report pagination boundary page must contain a JSON object")
    return payload


def _validate_semantic_review(review: Mapping[str, Any], expected_guild_label: str) -> None:
    expected_root = {
        "schema_version": 1,
        "review_kind": _REVIEW_KIND,
        "review_version": _REVIEW_VERSION,
    }
    for field_name, expected in expected_root.items():
        if review.get(field_name) != expected:
            raise ValueError(f"pagination semantic review mismatch: {field_name}")

    target = _required_object(review.get("target"), "target")
    if target.get("guild_label") != expected_guild_label:
        raise ValueError("pagination semantic review guild label mismatch")
    if target.get("guild_identity_status") != "operator_named_target_unresolved":
        raise ValueError("guild identity was unexpectedly resolved before boundary probing")

    request = _required_object(review.get("request"), "request")
    expected_request = {
        "route_template": REPORTS_PUBLIC_ROUTE,
        "reviewed_pages": [1, 2, 3],
        "limit": 5,
        "sort_by": "created_at",
        "sort_order": "desc",
    }
    for field_name, expected in expected_request.items():
        if request.get(field_name) != expected:
            raise ValueError(f"pagination semantic review request mismatch: {field_name}")

    assignments = _required_object(review.get("semantic_assignments"), "semantic_assignments")
    expected_assignments = {
        "current_page_field": "page",
        "page_size_field": "limit",
        "total_record_count_field": None,
        "total_page_count_field": None,
        "has_next_page_field": None,
        "current_page_candidate_count": 1,
        "page_size_candidate_count": 1,
        "total_record_page_pair_candidate_count": 0,
        "has_next_page_candidate_count": 0,
    }
    for field_name, expected in expected_assignments.items():
        if assignments.get(field_name) != expected:
            raise ValueError(f"pagination semantic assignment mismatch: {field_name}")

    summary = _required_object(review.get("summary"), "summary")
    expected_summary = {
        "reviewed_page_count": 3,
        "pagination_direct_field_count": 5,
        "relationship_verified_field_count": 2,
        "unresolved_field_count": 3,
        "pagination_field_semantics_verified": False,
        "termination_condition_verified": False,
        "ready_for_exhaustive_public_report_manifest_capture": False,
        "ready_for_full_guild_crawl": False,
        "ready_for_bis25_scoring": False,
        "all_integrity_checks_passed": True,
        "contains_source_scalar_values": False,
        "private_evidence_contains_source_scalar_values": True,
    }
    for field_name, expected in expected_summary.items():
        if summary.get(field_name) != expected:
            raise ValueError(f"pagination semantic review summary mismatch: {field_name}")

    boundary = _required_object(review.get("decision_boundary"), "decision_boundary")
    expected_boundary = {
        "status": "pagination_semantics_reviewed",
        "pagination_field_semantics_verified": False,
        "termination_condition_verified": False,
        "ready_for_exhaustive_public_report_manifest_capture": False,
        "ready_for_full_guild_crawl": False,
        "ready_for_guild_identity_review": False,
        "ready_for_guild_filtering": False,
        "ready_for_multi_report_character_graph": False,
        "ready_for_performance_model": False,
        "ready_for_global_benchmark": False,
        "ready_for_bis25_scoring": False,
        "planner_scoring_allowed": False,
    }
    for field_name, expected in expected_boundary.items():
        if boundary.get(field_name) != expected:
            raise ValueError(f"pagination semantic review boundary mismatch: {field_name}")

    contracts = [
        _required_object(row, "field_contracts[]")
        for row in _required_list(review.get("field_contracts"), "field_contracts")
    ]
    contracts_by_name = {str(row.get("field_name")): row for row in contracts}
    if set(contracts_by_name) != _EXPECTED_FIELDS:
        raise ValueError("pagination semantic review field set changed")
    if contracts_by_name["page"].get("semantic_assignment") != "current_page":
        raise ValueError("pagination page field is not relationship-verified")
    if contracts_by_name["limit"].get("semantic_assignment") != "page_size":
        raise ValueError("pagination limit field is not relationship-verified")
    for field_name in ("hasMore", "hasPrevious", "offset"):
        if contracts_by_name[field_name].get("semantic_status") != "unresolved":
            raise ValueError(f"pagination field {field_name} was unexpectedly promoted")


def _validate_baseline_private(
    baseline: Mapping[str, Any],
    review: Mapping[str, Any],
    baseline_body: bytes,
    expected_guild_label: str,
) -> tuple[list[int], list[dict[str, Any]]]:
    expected_root = {
        "schema_version": 1,
        "evidence_kind": _PRIVATE_KIND,
        "evidence_version": _PRIVATE_VERSION,
        "target_guild_label": expected_guild_label,
    }
    for field_name, expected in expected_root.items():
        if baseline.get(field_name) != expected:
            raise ValueError(f"baseline private pagination evidence mismatch: {field_name}")

    if _sha256_bytes(baseline_body) != review.get("source_private_evidence_sha256"):
        raise ValueError("baseline private pagination evidence hash changed after semantic review")

    pages = [
        _required_object(row, "baseline.pages[]")
        for row in _required_list(baseline.get("pages"), "baseline.pages")
    ]
    if sorted(_required_integer(row.get("page"), "baseline.pages[].page") for row in pages) != [
        1,
        2,
        3,
    ]:
        raise ValueError("baseline private pagination pages must be 1,2,3")

    report_ids: list[int] = []
    prepared_pages: list[dict[str, Any]] = []
    for row in sorted(pages, key=lambda item: int(item["page"])):
        page = _required_integer(row.get("page"), "baseline.pages[].page")
        limit = _required_integer(row.get("limit"), "baseline.pages[].limit")
        if limit != 5:
            raise ValueError("baseline pagination limit changed")
        pagination = _required_object(row.get("pagination"), "baseline.pages[].pagination")
        if set(pagination) != _EXPECTED_FIELDS:
            raise ValueError("baseline pagination field set changed")
        if _required_integer(pagination.get("page"), "pagination.page") != page:
            raise ValueError("baseline pagination page relation changed")
        if _required_integer(pagination.get("limit"), "pagination.limit") != limit:
            raise ValueError("baseline pagination limit relation changed")
        if _required_integer(pagination.get("offset"), "pagination.offset") != (page - 1) * limit:
            raise ValueError("baseline pagination offset relation changed")
        if _required_boolean(pagination.get("hasPrevious"), "pagination.hasPrevious") != (page > 1):
            raise ValueError("baseline pagination hasPrevious relation changed")
        if _required_boolean(pagination.get("hasMore"), "pagination.hasMore") is not True:
            raise ValueError("baseline pages no longer establish a lower hasMore=true bound")

        ids = [
            _required_integer(value, "baseline.pages[].source_report_ids[]")
            for value in _required_list(row.get("source_report_ids"), "source_report_ids")
        ]
        report_ids.extend(ids)
        prepared_pages.append(row)

    return report_ids, prepared_pages


def _prepare_probe_pages(values: Iterable[int]) -> tuple[int, ...]:
    pages = tuple(values)
    if len(pages) < 2 or len(pages) > 5:
        raise ValueError("probe_pages must contain between 2 and 5 pages")
    if any(isinstance(page, bool) or not isinstance(page, int) for page in pages):
        raise ValueError("probe_pages must contain integers")
    if any(page <= 3 or page > 65536 for page in pages):
        raise ValueError("probe_pages must be greater than 3 and at most 65536")
    if tuple(sorted(set(pages))) != pages:
        raise ValueError("probe_pages must be strictly increasing and unique")
    return pages


def capture_report_pagination_boundary_probe(
    registry: SourceRegistry,
    archive: RawArchive,
    *,
    semantic_review_path: Path,
    baseline_private_path: Path,
    private_output_path: Path,
    receipt_output_path: Path,
    expected_guild_label: str = "Argentum",
    probe_pages: Iterable[int] = _DEFAULT_PROBE_PAGES,
    limit: int = 5,
    timeout_seconds: float = 20.0,
    retry_count: int = 0,
    opener: Any | None = None,
) -> dict[str, Any]:
    """Probe a fixed sparse page set without automatically walking to a terminal page."""
    pages = _prepare_probe_pages(probe_pages)
    if limit != 5:
        raise ValueError("boundary probe limit must remain at the verified value of 5")
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be greater than zero")
    if retry_count < 0 or retry_count > 1:
        raise ValueError("retry_count must be between 0 and 1")

    review, review_body = _load_object(semantic_review_path, "pagination semantic review")
    baseline, baseline_body = _load_object(baseline_private_path, "baseline private evidence")
    _validate_semantic_review(review, expected_guild_label)
    baseline_ids, baseline_pages = _validate_baseline_private(
        baseline,
        review,
        baseline_body,
        expected_guild_label,
    )

    session = SameOriginHttpSession(registry.base_url, opener=opener)
    seen_report_ids = set(baseline_ids)
    all_report_ids = list(baseline_ids)
    private_pages: list[dict[str, Any]] = []
    receipt_pages: list[dict[str, Any]] = []
    has_more_true_pages = [int(row["page"]) for row in baseline_pages]
    has_more_false_pages: list[int] = []
    empty_page_count = 0

    for page in pages:
        result = capture_public_report_discovery(
            registry,
            archive,
            local_category="argentum_pagination_boundary_probe",
            page=page,
            limit=limit,
            timeout_seconds=timeout_seconds,
            retry_count=retry_count,
            session=session,
        )
        if not result.complete or result.capture is None:
            raise ValueError(f"pagination boundary page {page} capture was incomplete: {result.error}")

        payload = _read_archived_payload(result.capture.payload_path)
        reports = _required_list(payload.get("reports"), f"page[{page}].reports")
        pagination = _required_object(payload.get("pagination"), f"page[{page}].pagination")
        if payload.get("success") is not True:
            raise ValueError(f"pagination boundary page {page} did not report success=true")
        if set(pagination) != _EXPECTED_FIELDS:
            raise ValueError(f"pagination boundary page {page} field set changed")

        observed_page = _required_integer(pagination.get("page"), "pagination.page")
        observed_limit = _required_integer(pagination.get("limit"), "pagination.limit")
        observed_offset = _required_integer(pagination.get("offset"), "pagination.offset")
        has_previous = _required_boolean(pagination.get("hasPrevious"), "pagination.hasPrevious")
        has_more = _required_boolean(pagination.get("hasMore"), "pagination.hasMore")
        if observed_page != page:
            raise ValueError(f"pagination boundary page {page} did not echo the requested page")
        if observed_limit != limit:
            raise ValueError(f"pagination boundary page {page} did not echo the requested limit")
        if observed_offset != (page - 1) * limit:
            raise ValueError(f"pagination boundary page {page} offset relation failed")
        if has_previous != (page > 1):
            raise ValueError(f"pagination boundary page {page} hasPrevious relation failed")

        report_ids: list[int] = []
        for index, raw_report in enumerate(reports):
            report = _required_object(raw_report, f"page[{page}].reports[{index}]")
            report_ids.append(
                _required_integer(report.get("id"), f"page[{page}].reports[{index}].id")
            )
        unique_report_ids = set(report_ids)
        duplicate_with_prior_count = sum(1 for report_id in report_ids if report_id in seen_report_ids)
        seen_report_ids.update(unique_report_ids)
        all_report_ids.extend(report_ids)
        if not report_ids:
            empty_page_count += 1

        if has_more:
            has_more_true_pages.append(page)
            has_more_state = "more_pages_candidate"
        else:
            has_more_false_pages.append(page)
            has_more_state = "terminal_candidate"

        private_pages.append(
            {
                "page": page,
                "limit": limit,
                "raw_id": result.capture.raw_id,
                "observation_id": result.capture.observation_id,
                "payload_hash": result.capture.payload_hash,
                "schema_fingerprint": result.capture.schema_fingerprint,
                "source_report_ids": report_ids,
                "pagination": pagination,
                "report_count": len(report_ids),
                "duplicate_with_prior_pages_count": duplicate_with_prior_count,
            }
        )
        receipt_pages.append(
            {
                "requested_page": page,
                "limit": limit,
                "http_status": result.status,
                "raw_id": result.capture.raw_id,
                "observation_id": result.capture.observation_id,
                "payload_hash": result.capture.payload_hash,
                "schema_fingerprint": result.capture.schema_fingerprint,
                "report_occurrence_count": len(report_ids),
                "unique_report_id_count": len(unique_report_ids),
                "duplicate_with_prior_pages_count": duplicate_with_prior_count,
                "report_id_set_sha256": _sha256_json(sorted(unique_report_ids)),
                "has_more_state": has_more_state,
                "short_page": len(report_ids) < limit,
                "empty_page": not report_ids,
                "page_relation_verified": True,
                "limit_relation_verified": True,
                "offset_relation_verified": True,
                "has_previous_relation_verified": True,
            }
        )

    lower_candidates = [
        true_page
        for true_page in has_more_true_pages
        if not has_more_false_pages or true_page < min(has_more_false_pages)
    ]
    lower_bound = max(lower_candidates) if lower_candidates else None
    upper_bound = min(has_more_false_pages) if has_more_false_pages else None
    monotonic_candidate = not has_more_false_pages or not any(
        true_page > upper_bound for true_page in has_more_true_pages
    )
    terminal_bracket_observed = (
        monotonic_candidate
        and lower_bound is not None
        and upper_bound is not None
        and lower_bound < upper_bound
    )

    private_payload = {
        "schema_version": _PROBE_SCHEMA_VERSION,
        "probe_kind": "report_pagination_boundary_private_batch",
        "probe_version": _PROBE_VERSION,
        "generated_at": _generated_at(),
        "source_semantic_review_name": semantic_review_path.name,
        "source_semantic_review_sha256": _sha256_bytes(review_body),
        "source_baseline_private_name": baseline_private_path.name,
        "source_baseline_private_sha256": _sha256_bytes(baseline_body),
        "target_guild_label": expected_guild_label,
        "request": {
            "route_template": REPORTS_PUBLIC_ROUTE,
            "probe_pages": list(pages),
            "limit": limit,
            "sort_by": "created_at",
            "sort_order": "desc",
            "http_profile_version": session.profile.version,
        },
        "pages": private_pages,
        "summary": {
            "captured_page_count": len(private_pages),
            "report_occurrence_count": sum(len(row["source_report_ids"]) for row in private_pages),
            "unique_report_id_count": len({value for row in private_pages for value in row["source_report_ids"]}),
            "contains_source_scalar_values": True,
        },
    }
    private_body = _write_json(private_output_path, private_payload)

    checks = {
        "semantic_review_verified": True,
        "baseline_private_hash_verified": True,
        "fixed_probe_window_verified": True,
        "all_probe_pages_archived": True,
        "all_probe_pages_completed": True,
        "page_relation_verified_on_all_probe_pages": True,
        "limit_relation_verified_on_all_probe_pages": True,
        "offset_relation_verified_on_all_probe_pages": True,
        "has_previous_relation_verified_on_all_probe_pages": True,
        "report_ids_type_checked": True,
        "cross_page_duplicate_measurement_completed": True,
        "private_probe_written": True,
        "scalar_free_receipt_boundary_preserved": True,
    }
    receipt = {
        "schema_version": _PROBE_SCHEMA_VERSION,
        "probe_kind": "report_pagination_boundary_probe",
        "probe_version": _PROBE_VERSION,
        "generated_at": _generated_at(),
        "source_semantic_review_name": semantic_review_path.name,
        "source_semantic_review_sha256": _sha256_bytes(review_body),
        "source_baseline_private_name": baseline_private_path.name,
        "source_baseline_private_sha256": _sha256_bytes(baseline_body),
        "source_private_probe_name": private_output_path.name,
        "source_private_probe_sha256": _sha256_bytes(private_body),
        "target": {
            "guild_label": expected_guild_label,
            "guild_identity_status": "operator_named_target_unresolved",
        },
        "request": {
            "route_template": REPORTS_PUBLIC_ROUTE,
            "probe_pages": list(pages),
            "limit": limit,
            "sort_by": "created_at",
            "sort_order": "desc",
            "http_profile_version": session.profile.version,
        },
        "pages": receipt_pages,
        "boundary_observation": {
            "baseline_lower_bound_page": 3,
            "highest_more_pages_candidate": max(has_more_true_pages),
            "lowest_terminal_candidate": upper_bound,
            "terminal_bracket_observed": terminal_bracket_observed,
            "monotonic_has_more_candidate": monotonic_candidate,
        },
        "integrity_checks": checks,
        "decision_boundary": {
            "status": "bounded_pagination_boundary_probe_completed",
            "page_semantics_verified": True,
            "page_size_semantics_verified": True,
            "offset_semantics_verified": True,
            "has_previous_semantics_verified": True,
            "has_more_semantics_verified": False,
            "termination_condition_verified": False,
            "terminal_bracket_observed": terminal_bracket_observed,
            "ready_for_bounded_terminal_search": terminal_bracket_observed,
            "ready_for_larger_bounded_probe": not has_more_false_pages,
            "automatic_full_manifest_collection_allowed": False,
            "ready_for_exhaustive_public_report_manifest_capture": False,
            "ready_for_full_guild_crawl": False,
            "ready_for_guild_identity_review": False,
            "ready_for_guild_filtering": False,
            "ready_for_multi_report_character_graph": False,
            "ready_for_performance_model": False,
            "ready_for_global_benchmark": False,
            "ready_for_bis25_scoring": False,
            "planner_scoring_allowed": False,
            "private_probe_contains_source_scalar_values": True,
        },
        "summary": {
            "baseline_page_count": 3,
            "probe_page_count": len(pages),
            "completed_probe_page_count": len(receipt_pages),
            "report_occurrence_count": len(all_report_ids) - len(baseline_ids),
            "unique_probe_report_id_count": len(
                {value for row in private_pages for value in row["source_report_ids"]}
            ),
            "duplicate_with_baseline_or_prior_count": sum(
                int(row["duplicate_with_prior_pages_count"]) for row in receipt_pages
            ),
            "empty_probe_page_count": empty_page_count,
            "has_more_true_probe_page_count": sum(
                row["has_more_state"] == "more_pages_candidate" for row in receipt_pages
            ),
            "has_more_false_probe_page_count": sum(
                row["has_more_state"] == "terminal_candidate" for row in receipt_pages
            ),
            "terminal_bracket_observed": terminal_bracket_observed,
            "integrity_check_count": len(checks),
            "all_integrity_checks_passed": True,
            "contains_source_scalar_values": False,
            "private_probe_contains_source_scalar_values": True,
            "ready_for_bounded_terminal_search": terminal_bracket_observed,
            "ready_for_larger_bounded_probe": not has_more_false_pages,
            "ready_for_exhaustive_public_report_manifest_capture": False,
            "ready_for_full_guild_crawl": False,
            "ready_for_bis25_scoring": False,
        },
    }
    _write_json(receipt_output_path, receipt)
    return receipt
