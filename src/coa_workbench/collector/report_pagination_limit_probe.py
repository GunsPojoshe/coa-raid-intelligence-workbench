from __future__ import annotations

import gzip
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from .http_profile import SameOriginHttpSession
from .raw_archive import RawArchive
from .report_discovery import REPORTS_PUBLIC_ROUTE, capture_public_report_discovery
from .source_registry import SourceRegistry

_PROBE_SCHEMA_VERSION = 1
_PROBE_VERSION = "report-pagination-limit-probe-v1"
_DEFAULT_CANDIDATES = (5, 25, 50, 100, 250, 500)
_PROBE_PAGES = (1, 2)
_EXPECTED_PAGINATION_FIELDS = {"hasMore", "hasPrevious", "limit", "offset", "page"}


def _generated_at() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_json(value: object) -> str:
    return _sha256_bytes(_canonical_json(value).encode("utf-8"))


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
        raise ValueError("report limit probe payload must contain a JSON object")
    return payload


def _required_object(value: object, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"report limit probe field {field_name} must be an object")
    return value


def _required_list(value: object, field_name: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"report limit probe field {field_name} must be an array")
    return value


def _required_integer(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"report limit probe field {field_name} must be an integer")
    return value


def _required_boolean(value: object, field_name: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"report limit probe field {field_name} must be a boolean")
    return value


def _prepare_candidates(values: Iterable[int]) -> tuple[int, ...]:
    candidates = tuple(values)
    if len(candidates) < 2 or len(candidates) > 8:
        raise ValueError("limit candidates must contain between 2 and 8 values")
    if any(isinstance(value, bool) or not isinstance(value, int) for value in candidates):
        raise ValueError("limit candidates must contain integers")
    if any(value < 1 or value > 500 for value in candidates):
        raise ValueError("limit candidates must be between 1 and 500")
    if tuple(sorted(set(candidates))) != candidates:
        raise ValueError("limit candidates must be strictly increasing and unique")
    if candidates[0] != 5:
        raise ValueError("limit candidates must start with the verified control value 5")
    return candidates


def _capture_page(
    registry: SourceRegistry,
    archive: RawArchive,
    session: SameOriginHttpSession,
    *,
    page: int,
    limit: int,
    timeout_seconds: float,
    retry_count: int,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, bool], set[int]]:
    result = capture_public_report_discovery(
        registry,
        archive,
        local_category="argentum_report_limit_probe",
        page=page,
        limit=limit,
        timeout_seconds=timeout_seconds,
        retry_count=retry_count,
        allow_unverified_limit_probe=True,
        session=session,
    )
    if not result.complete or result.capture is None:
        safe_row = {
            "page": page,
            "requested_limit": limit,
            "http_status": result.status,
            "complete": False,
            "error": result.error,
            "raw_id": result.capture.raw_id if result.capture else None,
            "observation_id": result.capture.observation_id if result.capture else None,
            "payload_hash": result.capture.payload_hash if result.capture else None,
            "schema_fingerprint": result.capture.schema_fingerprint if result.capture else None,
        }
        checks = {
            "complete": False,
            "success_true": False,
            "page_relation_verified": False,
            "limit_relation_verified": False,
            "offset_relation_verified": False,
            "has_previous_relation_verified": False,
            "has_more_type_verified": False,
            "full_page_observed": False,
            "report_ids_unique_within_page": False,
        }
        return safe_row, safe_row.copy(), checks, set()

    payload = _read_archived_payload(result.capture.payload_path)
    reports = _required_list(payload.get("reports"), f"page[{page}].reports")
    pagination = _required_object(payload.get("pagination"), f"page[{page}].pagination")
    if set(pagination) != _EXPECTED_PAGINATION_FIELDS:
        raise ValueError(f"report limit probe page {page} pagination field set changed")

    observed_page = _required_integer(pagination.get("page"), "pagination.page")
    observed_limit = _required_integer(pagination.get("limit"), "pagination.limit")
    observed_offset = _required_integer(pagination.get("offset"), "pagination.offset")
    has_previous = _required_boolean(pagination.get("hasPrevious"), "pagination.hasPrevious")
    _required_boolean(pagination.get("hasMore"), "pagination.hasMore")

    report_ids = [
        _required_integer(
            _required_object(report, f"page[{page}].reports[{index}]").get("id"),
            f"page[{page}].reports[{index}].id",
        )
        for index, report in enumerate(reports)
    ]
    unique_report_ids = set(report_ids)
    checks = {
        "complete": True,
        "success_true": payload.get("success") is True,
        "page_relation_verified": observed_page == page,
        "limit_relation_verified": observed_limit == limit,
        "offset_relation_verified": observed_offset == (page - 1) * limit,
        "has_previous_relation_verified": has_previous == (page > 1),
        "has_more_type_verified": True,
        "full_page_observed": len(report_ids) == limit,
        "report_ids_unique_within_page": len(unique_report_ids) == len(report_ids),
    }
    private_row = {
        "page": page,
        "requested_limit": limit,
        "raw_id": result.capture.raw_id,
        "observation_id": result.capture.observation_id,
        "payload_hash": result.capture.payload_hash,
        "schema_fingerprint": result.capture.schema_fingerprint,
        "pagination": pagination,
        "source_report_ids": report_ids,
        "report_count": len(report_ids),
        "checks": checks,
    }
    safe_row = {
        "page": page,
        "requested_limit": limit,
        "http_status": result.status,
        "complete": True,
        "raw_id": result.capture.raw_id,
        "observation_id": result.capture.observation_id,
        "payload_hash": result.capture.payload_hash,
        "schema_fingerprint": result.capture.schema_fingerprint,
        "report_occurrence_count": len(report_ids),
        "unique_report_id_count": len(unique_report_ids),
        "report_id_set_sha256": _sha256_json(sorted(unique_report_ids)),
        "pagination_shape_sha256": _sha256_json(sorted(pagination)),
        "checks": checks,
    }
    return private_row, safe_row, checks, unique_report_ids


def capture_report_pagination_limit_probe(
    registry: SourceRegistry,
    archive: RawArchive,
    *,
    private_output_path: Path,
    receipt_output_path: Path,
    expected_guild_label: str = "Argentum",
    candidates: Iterable[int] = _DEFAULT_CANDIDATES,
    timeout_seconds: float = 20.0,
    retry_count: int = 1,
    opener: Any | None = None,
) -> dict[str, Any]:
    """Probe larger page sizes without promoting them into production collection."""
    prepared_candidates = _prepare_candidates(candidates)
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be greater than zero")
    if retry_count < 0 or retry_count > 1:
        raise ValueError("retry_count must be between 0 and 1")

    session = SameOriginHttpSession(registry.base_url, opener=opener)
    private_candidates: list[dict[str, Any]] = []
    receipt_candidates: list[dict[str, Any]] = []
    supported_limits: list[int] = []

    for limit in prepared_candidates:
        private_pages: list[dict[str, Any]] = []
        receipt_pages: list[dict[str, Any]] = []
        page_checks: list[dict[str, bool]] = []
        page_id_sets: list[set[int]] = []
        for page in _PROBE_PAGES:
            private_row, safe_row, checks, report_ids = _capture_page(
                registry,
                archive,
                session,
                page=page,
                limit=limit,
                timeout_seconds=timeout_seconds,
                retry_count=retry_count,
            )
            private_pages.append(private_row)
            receipt_pages.append(safe_row)
            page_checks.append(checks)
            page_id_sets.append(report_ids)

        candidate_checks = {
            "all_pages_complete": all(check["complete"] for check in page_checks),
            "all_pages_success_true": all(check["success_true"] for check in page_checks),
            "all_page_relations_verified": all(
                check["page_relation_verified"] for check in page_checks
            ),
            "all_limit_relations_verified": all(
                check["limit_relation_verified"] for check in page_checks
            ),
            "all_offset_relations_verified": all(
                check["offset_relation_verified"] for check in page_checks
            ),
            "all_has_previous_relations_verified": all(
                check["has_previous_relation_verified"] for check in page_checks
            ),
            "all_has_more_types_verified": all(
                check["has_more_type_verified"] for check in page_checks
            ),
            "all_pages_full": all(check["full_page_observed"] for check in page_checks),
            "all_report_ids_unique_within_page": all(
                check["report_ids_unique_within_page"] for check in page_checks
            ),
            "cross_page_report_ids_disjoint": not (page_id_sets[0] & page_id_sets[1]),
        }
        observed_supported = all(candidate_checks.values())
        if observed_supported:
            supported_limits.append(limit)

        private_candidates.append(
            {
                "requested_limit": limit,
                "pages": private_pages,
                "checks": candidate_checks,
                "observed_supported": observed_supported,
                "contains_source_scalar_values": True,
            }
        )
        receipt_candidates.append(
            {
                "requested_limit": limit,
                "pages": receipt_pages,
                "checks": candidate_checks,
                "observed_supported": observed_supported,
                "contains_source_scalar_values": False,
            }
        )

    selected_limit = max(supported_limits) if supported_limits else None
    private_payload = {
        "schema_version": _PROBE_SCHEMA_VERSION,
        "probe_kind": "report_pagination_limit_probe_private_batch",
        "probe_version": _PROBE_VERSION,
        "generated_at": _generated_at(),
        "target_guild_label": expected_guild_label,
        "request": {
            "route_template": REPORTS_PUBLIC_ROUTE,
            "candidate_limits": list(prepared_candidates),
            "pages_per_candidate": list(_PROBE_PAGES),
            "sort_by": "created_at",
            "sort_order": "desc",
            "http_profile_version": session.profile.version,
        },
        "candidates": private_candidates,
        "result": {
            "observed_supported_limits": supported_limits,
            "selected_limit_candidate": selected_limit,
            "contains_source_scalar_values": True,
        },
    }
    private_body = _write_json(private_output_path, private_payload)

    larger_limit_observed = selected_limit is not None and selected_limit > 5
    receipt = {
        "schema_version": _PROBE_SCHEMA_VERSION,
        "probe_kind": "report_pagination_limit_probe",
        "probe_version": _PROBE_VERSION,
        "generated_at": _generated_at(),
        "source_private_probe_name": private_output_path.name,
        "source_private_probe_sha256": _sha256_bytes(private_body),
        "target": {
            "guild_label": expected_guild_label,
            "guild_identity_status": "operator_named_target_unresolved",
        },
        "request": {
            "route_template": REPORTS_PUBLIC_ROUTE,
            "candidate_limits": list(prepared_candidates),
            "pages_per_candidate": list(_PROBE_PAGES),
            "sort_by": "created_at",
            "sort_order": "desc",
            "http_profile_version": session.profile.version,
        },
        "candidates": receipt_candidates,
        "decision_boundary": {
            "status": (
                "larger_limit_candidate_observed"
                if larger_limit_observed
                else "no_larger_limit_candidate_observed"
            ),
            "verified_production_limit": 5,
            "selected_limit_candidate": selected_limit,
            "larger_limit_candidate_observed": larger_limit_observed,
            "manual_limit_promotion_required": larger_limit_observed,
            "ready_for_manual_limit_promotion": larger_limit_observed,
            "production_manifest_limit_changed": False,
            "ready_for_fast_manifest_capture": False,
            "ready_for_full_guild_crawl": False,
            "ready_for_guild_filtering": False,
            "planner_scoring_allowed": False,
        },
        "summary": {
            "candidate_count": len(prepared_candidates),
            "completed_page_request_count": sum(
                int(page.get("complete") is True)
                for candidate in receipt_candidates
                for page in candidate["pages"]
            ),
            "observed_supported_limit_count": len(supported_limits),
            "selected_limit_candidate": selected_limit,
            "larger_limit_candidate_observed": larger_limit_observed,
            "contains_source_scalar_values": False,
            "private_probe_contains_source_scalar_values": True,
            "ready_for_manual_limit_promotion": larger_limit_observed,
            "ready_for_fast_manifest_capture": False,
        },
    }
    _write_json(receipt_output_path, receipt)
    return receipt


__all__ = ["capture_report_pagination_limit_probe"]
