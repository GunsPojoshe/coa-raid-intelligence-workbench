from __future__ import annotations

import gzip
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .http_profile import SameOriginHttpSession
from .raw_archive import RawArchive
from .report_discovery import (
    REPORT_DISCOVERY_MAX_LIMIT,
    REPORTS_PUBLIC_ROUTE,
    capture_public_report_discovery,
)
from .source_registry import SourceRegistry

_EVIDENCE_SCHEMA_VERSION = 1
_EVIDENCE_VERSION = "report-pagination-evidence-v1"
_CONTRACT_KIND = "guild_wide_report_collection_contract"
_CONTRACT_VERSION = "guild-report-collection-contract-v1"
_EXPECTED_MAPPING_ID = "coa-public-report-discovery-v1"
_EXPECTED_REVIEWED_PAYLOAD_HASH = (
    "2203e52709fad4fbc8d5235bc3699abeec6b85cf1e13b9df3e24091ddf8775c2"
)
_EXPECTED_SCHEMA_FINGERPRINT = (
    "4f47885820e6931cd76db538cabd68405b4969778c1bede9dee53a7f1e005ed4"
)


def _generated_at() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_json(value: object) -> str:
    return _sha256_bytes(_canonical_json(value).encode("utf-8"))


def _load_object(path: Path, label: str) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{label} must contain a JSON object")
    return payload


def _required_object(value: object, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"pagination evidence field {field_name} must be an object")
    return value


def _required_list(value: object, field_name: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"pagination evidence field {field_name} must be an array")
    return value


def _required_string(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"pagination evidence field {field_name} must be a non-empty string")
    return value


def _shape(value: object) -> object:
    if isinstance(value, dict):
        return {
            "type": "object",
            "fields": {str(key): _shape(value[key]) for key in sorted(value)},
        }
    if isinstance(value, list):
        item_shapes: list[object] = []
        for item in value[:25]:
            candidate = _shape(item)
            if candidate not in item_shapes:
                item_shapes.append(candidate)
        return {"type": "array", "item_shapes": item_shapes}
    if value is None:
        return {"type": "null"}
    if isinstance(value, bool):
        return {"type": "boolean"}
    if isinstance(value, int):
        return {"type": "integer"}
    if isinstance(value, float):
        return {"type": "number"}
    return {"type": "string"}


def _write_json(path: Path, payload: object) -> bytes:
    rendered = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    body = rendered.encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(body)
    temporary.replace(path)
    return body


def _validate_contract(contract: dict[str, Any], expected_guild_label: str) -> None:
    if contract.get("schema_version") != 1:
        raise ValueError("unsupported guild collection contract schema version")
    if contract.get("contract_kind") != _CONTRACT_KIND:
        raise ValueError("unexpected guild collection contract kind")
    if contract.get("contract_version") != _CONTRACT_VERSION:
        raise ValueError("unexpected guild collection contract version")

    target = _required_object(contract.get("target"), "target")
    if target.get("guild_label") != expected_guild_label:
        raise ValueError("guild collection contract target label mismatch")
    if target.get("guild_identity_status") != "operator_named_target_unresolved":
        raise ValueError("guild identity was unexpectedly promoted before pagination review")
    if target.get("verified_source_guild_id") is not False:
        raise ValueError("source guild id must remain unverified")
    if target.get("verified_source_guild_name") is not False:
        raise ValueError("source guild name must remain unverified")

    boundary = _required_object(contract.get("decision_boundary"), "decision_boundary")
    expected_boundary = {
        "status": "collection_contract_only",
        "ready_for_bounded_pagination_capture": True,
        "ready_for_full_guild_crawl": False,
        "ready_for_guild_filtering": False,
        "ready_for_multi_report_character_graph": False,
        "ready_for_performance_model": False,
        "ready_for_global_benchmark": False,
        "ready_for_bis25_scoring": False,
        "planner_scoring_allowed": False,
        "automatic_network_collection": False,
        "contains_source_scalar_values": False,
    }
    for field_name, expected in expected_boundary.items():
        if boundary.get(field_name) != expected:
            raise ValueError(f"guild collection boundary mismatch: {field_name}")

    summary = _required_object(contract.get("summary"), "summary")
    expected_summary = {
        "collection_phase_count": 7,
        "open_phase_count": 1,
        "blocked_phase_count": 6,
        "current_exact_payload_actor_count": 11,
        "persisted_parser_observation_count": 1343,
        "persisted_actor_build_observation_count": 1339,
        "minimum_candidate_character_count": 30,
        "preferred_candidate_character_count": 40,
        "final_roster_size": 25,
        "ready_for_bounded_pagination_capture": True,
        "ready_for_full_guild_crawl": False,
        "ready_for_bis25_scoring": False,
        "contains_source_scalar_values": False,
    }
    for field_name, expected in expected_summary.items():
        if summary.get(field_name) != expected:
            raise ValueError(f"guild collection summary mismatch: {field_name}")

    foundation = _required_object(contract.get("verified_foundation"), "verified_foundation")
    expected_foundation = {
        "report_discovery_mapping_id": _EXPECTED_MAPPING_ID,
        "report_discovery_route": REPORTS_PUBLIC_ROUTE,
        "report_discovery_reviewed_payload_hash": _EXPECTED_REVIEWED_PAYLOAD_HASH,
        "report_discovery_schema_fingerprint": _EXPECTED_SCHEMA_FINGERPRINT,
        "reviewed_discovery_page_count": 1,
        "reviewed_discovery_record_count": 5,
        "exact_payload_linked_actors": 11,
        "persisted_parser_observations": 1343,
        "persisted_actor_build_observations": 1339,
    }
    for field_name, expected in expected_foundation.items():
        if foundation.get(field_name) != expected:
            raise ValueError(f"guild collection foundation mismatch: {field_name}")

    phases = _required_list(contract.get("collection_phases"), "collection_phases")
    phase_status = {
        _required_string(_required_object(row, "collection_phases[]").get("code"), "phase.code"):
        _required_string(_required_object(row, "collection_phases[]").get("status"), "phase.status")
        for row in phases
    }
    if phase_status.get("pagination_evidence") != "ready_for_bounded_capture":
        raise ValueError("pagination evidence phase is not open")
    if any(
        status != "blocked"
        for code, status in phase_status.items()
        if code != "pagination_evidence"
    ):
        raise ValueError("a downstream guild collection phase was unexpectedly opened")


def _read_archived_payload(payload_path: str) -> dict[str, Any]:
    body = gzip.decompress(Path(payload_path).read_bytes())
    payload = json.loads(body)
    if not isinstance(payload, dict):
        raise ValueError("report discovery page must contain a JSON object")
    return payload


def capture_bounded_report_pagination_evidence(
    registry: SourceRegistry,
    archive: RawArchive,
    *,
    contract_path: Path,
    private_output_path: Path,
    receipt_output_path: Path,
    expected_guild_label: str = "Argentum",
    start_page: int = 1,
    page_count: int = 3,
    limit: int = REPORT_DISCOVERY_MAX_LIMIT,
    timeout_seconds: float = 20.0,
    retry_count: int = 0,
    opener: Any | None = None,
) -> dict[str, Any]:
    """Capture an explicit page window without inferring pagination or guild semantics."""
    if start_page != 1:
        raise ValueError("initial pagination evidence must start at page 1")
    if page_count < 2 or page_count > 5:
        raise ValueError("page_count must be between 2 and 5")
    if limit != REPORT_DISCOVERY_MAX_LIMIT:
        raise ValueError("limit must remain at the observed maximum of 5")
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be greater than zero")
    if retry_count < 0 or retry_count > 1:
        raise ValueError("retry_count must be between 0 and 1")

    contract_body = contract_path.read_bytes()
    contract = json.loads(contract_body)
    if not isinstance(contract, dict):
        raise ValueError("guild collection contract must contain a JSON object")
    _validate_contract(contract, expected_guild_label)

    session = SameOriginHttpSession(registry.base_url, opener=opener)
    private_pages: list[dict[str, Any]] = []
    receipt_pages: list[dict[str, Any]] = []
    seen_report_ids: set[int] = set()
    all_report_ids: list[int] = []
    pagination_shape_hashes: set[str] = set()
    top_level_shapes: set[str] = set()
    payload_hashes: set[str] = set()
    schema_fingerprints: set[str] = set()
    empty_page_count = 0

    for page in range(start_page, start_page + page_count):
        result = capture_public_report_discovery(
            registry,
            archive,
            local_category="argentum_pagination_evidence",
            page=page,
            limit=limit,
            timeout_seconds=timeout_seconds,
            retry_count=retry_count,
            session=session,
        )
        if not result.complete or result.capture is None:
            raise ValueError(f"report discovery page {page} capture was incomplete: {result.error}")

        payload = _read_archived_payload(result.capture.payload_path)
        reports = _required_list(payload.get("reports"), f"page[{page}].reports")
        pagination = _required_object(payload.get("pagination"), f"page[{page}].pagination")
        if payload.get("success") is not True:
            raise ValueError(f"report discovery page {page} did not report success=true")

        report_ids: list[int] = []
        for index, raw_report in enumerate(reports):
            report = _required_object(raw_report, f"page[{page}].reports[{index}]")
            source_report_id = report.get("id")
            if isinstance(source_report_id, bool) or not isinstance(source_report_id, int):
                raise ValueError(f"report discovery page {page} contains a non-integer report id")
            report_ids.append(source_report_id)

        unique_report_ids = set(report_ids)
        duplicate_within_page_count = len(report_ids) - len(unique_report_ids)
        duplicate_with_prior_count = sum(1 for report_id in report_ids if report_id in seen_report_ids)
        seen_report_ids.update(unique_report_ids)
        all_report_ids.extend(report_ids)
        if not reports:
            empty_page_count += 1

        pagination_shape = _shape(pagination)
        pagination_shape_sha256 = _sha256_json(pagination_shape)
        top_level_shape = _shape(payload)
        top_level_shape_sha256 = _sha256_json(top_level_shape)
        report_id_set_sha256 = _sha256_json(sorted(unique_report_ids))
        pagination_shape_hashes.add(pagination_shape_sha256)
        top_level_shapes.add(top_level_shape_sha256)
        payload_hashes.add(result.capture.payload_hash)
        if result.capture.schema_fingerprint is not None:
            schema_fingerprints.add(result.capture.schema_fingerprint)

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
                "pagination_shape": pagination_shape,
                "top_level_keys": sorted(payload),
                "report_count": len(report_ids),
                "duplicate_within_page_count": duplicate_within_page_count,
                "duplicate_with_prior_pages_count": duplicate_with_prior_count,
            }
        )
        receipt_pages.append(
            {
                "page": page,
                "limit": limit,
                "http_status": result.status,
                "raw_id": result.capture.raw_id,
                "observation_id": result.capture.observation_id,
                "payload_hash": result.capture.payload_hash,
                "schema_fingerprint": result.capture.schema_fingerprint,
                "report_occurrence_count": len(report_ids),
                "unique_report_id_count": len(unique_report_ids),
                "duplicate_within_page_count": duplicate_within_page_count,
                "duplicate_with_prior_pages_count": duplicate_with_prior_count,
                "report_id_set_sha256": report_id_set_sha256,
                "pagination_shape_sha256": pagination_shape_sha256,
                "pagination_direct_field_count": len(pagination),
                "top_level_keys": sorted(payload),
            }
        )

    private_payload = {
        "schema_version": _EVIDENCE_SCHEMA_VERSION,
        "evidence_kind": "bounded_report_pagination_private_batch",
        "evidence_version": _EVIDENCE_VERSION,
        "generated_at": _generated_at(),
        "source_contract_name": contract_path.name,
        "source_contract_sha256": _sha256_bytes(contract_body),
        "target_guild_label": expected_guild_label,
        "request": {
            "route_template": REPORTS_PUBLIC_ROUTE,
            "start_page": start_page,
            "page_count": page_count,
            "limit": limit,
            "sort_by": "created_at",
            "sort_order": "desc",
            "http_profile_version": session.profile.version,
        },
        "pages": private_pages,
        "summary": {
            "captured_page_count": len(private_pages),
            "report_occurrence_count": len(all_report_ids),
            "unique_report_id_count": len(set(all_report_ids)),
            "duplicate_report_occurrence_count": len(all_report_ids) - len(set(all_report_ids)),
            "empty_page_count": empty_page_count,
            "contains_source_scalar_values": True,
        },
    }
    private_body = _write_json(private_output_path, private_payload)

    checks = {
        "guild_collection_contract_verified": True,
        "explicit_page_window_verified": True,
        "observed_query_shape_preserved": True,
        "all_pages_archived_before_review": True,
        "all_pages_completed": True,
        "all_report_ids_type_checked": True,
        "pagination_objects_present": True,
        "cross_page_duplicate_measurement_completed": True,
        "private_batch_written": True,
        "scalar_free_receipt_boundary_preserved": True,
    }
    receipt = {
        "schema_version": _EVIDENCE_SCHEMA_VERSION,
        "evidence_kind": "bounded_report_pagination_evidence",
        "evidence_version": _EVIDENCE_VERSION,
        "generated_at": _generated_at(),
        "source_contract_name": contract_path.name,
        "source_contract_sha256": _sha256_bytes(contract_body),
        "source_private_evidence_name": private_output_path.name,
        "source_private_evidence_sha256": _sha256_bytes(private_body),
        "target": {
            "guild_label": expected_guild_label,
            "guild_identity_status": "operator_named_target_unresolved",
        },
        "request": {
            "route_template": REPORTS_PUBLIC_ROUTE,
            "query_keys": ["page", "limit", "sortBy", "sortOrder"],
            "start_page": start_page,
            "page_count": page_count,
            "limit": limit,
            "sort_by": "created_at",
            "sort_order": "desc",
            "http_profile_version": session.profile.version,
        },
        "pages": receipt_pages,
        "integrity_checks": checks,
        "decision_boundary": {
            "status": "bounded_pagination_evidence_captured",
            "automatic_termination_used": False,
            "pagination_field_semantics_verified": False,
            "termination_condition_verified": False,
            "limit_behavior_above_5_verified": False,
            "cross_page_deduplication_policy_verified": False,
            "ready_for_manual_pagination_field_review": True,
            "ready_for_full_guild_crawl": False,
            "ready_for_guild_filtering": False,
            "ready_for_multi_report_character_graph": False,
            "ready_for_performance_model": False,
            "ready_for_global_benchmark": False,
            "ready_for_bis25_scoring": False,
            "planner_scoring_allowed": False,
            "private_evidence_contains_source_scalar_values": True,
        },
        "summary": {
            "requested_page_count": page_count,
            "completed_page_count": len(receipt_pages),
            "report_occurrence_count": len(all_report_ids),
            "unique_report_id_count": len(set(all_report_ids)),
            "duplicate_report_occurrence_count": len(all_report_ids) - len(set(all_report_ids)),
            "empty_page_count": empty_page_count,
            "distinct_payload_hash_count": len(payload_hashes),
            "distinct_schema_fingerprint_count": len(schema_fingerprints),
            "distinct_pagination_shape_count": len(pagination_shape_hashes),
            "distinct_top_level_shape_count": len(top_level_shapes),
            "all_pages_same_pagination_shape": len(pagination_shape_hashes) == 1,
            "all_pages_same_top_level_shape": len(top_level_shapes) == 1,
            "integrity_check_count": len(checks),
            "all_integrity_checks_passed": True,
            "contains_source_scalar_values": False,
            "private_evidence_contains_source_scalar_values": True,
            "ready_for_manual_pagination_field_review": True,
            "ready_for_full_guild_crawl": False,
            "ready_for_bis25_scoring": False,
        },
    }
    _write_json(receipt_output_path, receipt)
    return receipt
