from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

_REVIEW_SCHEMA_VERSION = 1
_REVIEW_VERSION = "report-pagination-semantic-review-v1"
_EVIDENCE_KIND = "bounded_report_pagination_evidence"
_EVIDENCE_VERSION = "report-pagination-evidence-v1"
_PRIVATE_KIND = "bounded_report_pagination_private_batch"
_EXPECTED_ROUTE = "/api/reports/public"
_EXPECTED_QUERY_KEYS = ["page", "limit", "sortBy", "sortOrder"]


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
        raise ValueError(f"pagination semantic review field {field_name} must be an object")
    return value


def _required_list(value: object, field_name: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"pagination semantic review field {field_name} must be an array")
    return value


def _required_string(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(
            f"pagination semantic review field {field_name} must be a non-empty string"
        )
    return value


def _required_integer(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"pagination semantic review field {field_name} must be an integer")
    return value


def _value_type(value: object) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return "unknown"


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
    return {"type": _value_type(value)}


def _validate_receipt(receipt: Mapping[str, Any], expected_guild_label: str) -> None:
    expected_root = {
        "schema_version": 1,
        "evidence_kind": _EVIDENCE_KIND,
        "evidence_version": _EVIDENCE_VERSION,
    }
    for field_name, expected in expected_root.items():
        if receipt.get(field_name) != expected:
            raise ValueError(f"pagination evidence receipt mismatch: {field_name}")

    target = _required_object(receipt.get("target"), "target")
    if target.get("guild_label") != expected_guild_label:
        raise ValueError("pagination evidence target guild label mismatch")
    if target.get("guild_identity_status") != "operator_named_target_unresolved":
        raise ValueError("guild identity was unexpectedly resolved before pagination review")

    request = _required_object(receipt.get("request"), "request")
    expected_request = {
        "route_template": _EXPECTED_ROUTE,
        "query_keys": _EXPECTED_QUERY_KEYS,
        "start_page": 1,
        "page_count": 3,
        "limit": 5,
        "sort_by": "created_at",
        "sort_order": "desc",
        "http_profile_version": "coa-fetch-context-v1",
    }
    for field_name, expected in expected_request.items():
        if request.get(field_name) != expected:
            raise ValueError(f"pagination evidence request mismatch: {field_name}")

    summary = _required_object(receipt.get("summary"), "summary")
    expected_summary = {
        "requested_page_count": 3,
        "completed_page_count": 3,
        "report_occurrence_count": 15,
        "unique_report_id_count": 15,
        "duplicate_report_occurrence_count": 0,
        "empty_page_count": 0,
        "distinct_pagination_shape_count": 1,
        "all_pages_same_pagination_shape": True,
        "all_integrity_checks_passed": True,
        "contains_source_scalar_values": False,
        "private_evidence_contains_source_scalar_values": True,
        "ready_for_manual_pagination_field_review": True,
        "ready_for_full_guild_crawl": False,
        "ready_for_bis25_scoring": False,
    }
    for field_name, expected in expected_summary.items():
        if summary.get(field_name) != expected:
            raise ValueError(f"pagination evidence summary mismatch: {field_name}")

    boundary = _required_object(receipt.get("decision_boundary"), "decision_boundary")
    expected_boundary = {
        "status": "bounded_pagination_evidence_captured",
        "automatic_termination_used": False,
        "pagination_field_semantics_verified": False,
        "termination_condition_verified": False,
        "ready_for_manual_pagination_field_review": True,
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
            raise ValueError(f"pagination evidence boundary mismatch: {field_name}")


def _validate_private(
    private: Mapping[str, Any],
    receipt: Mapping[str, Any],
    expected_guild_label: str,
) -> list[dict[str, Any]]:
    expected_root = {
        "schema_version": 1,
        "evidence_kind": _PRIVATE_KIND,
        "evidence_version": _EVIDENCE_VERSION,
        "target_guild_label": expected_guild_label,
    }
    for field_name, expected in expected_root.items():
        if private.get(field_name) != expected:
            raise ValueError(f"private pagination evidence mismatch: {field_name}")

    if private.get("source_contract_name") != receipt.get("source_contract_name"):
        raise ValueError("private pagination source contract name mismatch")
    if private.get("source_contract_sha256") != receipt.get("source_contract_sha256"):
        raise ValueError("private pagination source contract hash mismatch")

    private_request = _required_object(private.get("request"), "private.request")
    receipt_request = _required_object(receipt.get("request"), "receipt.request")
    for field_name in (
        "route_template",
        "start_page",
        "page_count",
        "limit",
        "sort_by",
        "sort_order",
        "http_profile_version",
    ):
        if private_request.get(field_name) != receipt_request.get(field_name):
            raise ValueError(f"private pagination request mismatch: {field_name}")

    private_pages = [
        _required_object(row, "private.pages[]")
        for row in _required_list(private.get("pages"), "private.pages")
    ]
    receipt_pages = [
        _required_object(row, "receipt.pages[]")
        for row in _required_list(receipt.get("pages"), "receipt.pages")
    ]
    if len(private_pages) != 3 or len(receipt_pages) != 3:
        raise ValueError("pagination review requires exactly three completed pages")

    receipt_by_page = {
        _required_integer(row.get("page"), "receipt.pages[].page"): row
        for row in receipt_pages
    }
    if sorted(receipt_by_page) != [1, 2, 3]:
        raise ValueError("pagination receipt page sequence is not 1,2,3")

    all_ids: list[int] = []
    pagination_field_sets: set[tuple[str, ...]] = set()
    for private_page in private_pages:
        page = _required_integer(private_page.get("page"), "private.pages[].page")
        receipt_page = receipt_by_page.get(page)
        if receipt_page is None:
            raise ValueError("private pagination page is missing from receipt")
        if private_page.get("limit") != receipt_page.get("limit"):
            raise ValueError(f"private pagination limit mismatch on page {page}")
        for field_name in (
            "raw_id",
            "observation_id",
            "payload_hash",
            "schema_fingerprint",
        ):
            if private_page.get(field_name) != receipt_page.get(field_name):
                raise ValueError(f"private pagination {field_name} mismatch on page {page}")

        report_ids = _required_list(
            private_page.get("source_report_ids"),
            f"private.pages[{page}].source_report_ids",
        )
        prepared_ids = [
            _required_integer(value, f"private.pages[{page}].source_report_ids[]")
            for value in report_ids
        ]
        if len(prepared_ids) != receipt_page.get("report_occurrence_count"):
            raise ValueError(f"private pagination report count mismatch on page {page}")
        if len(set(prepared_ids)) != receipt_page.get("unique_report_id_count"):
            raise ValueError(f"private pagination unique report count mismatch on page {page}")
        if _sha256_json(sorted(set(prepared_ids))) != receipt_page.get("report_id_set_sha256"):
            raise ValueError(f"private pagination report id hash mismatch on page {page}")
        all_ids.extend(prepared_ids)

        pagination = _required_object(
            private_page.get("pagination"),
            f"private.pages[{page}].pagination",
        )
        if _sha256_json(_shape(pagination)) != receipt_page.get("pagination_shape_sha256"):
            raise ValueError(f"private pagination shape hash mismatch on page {page}")
        if len(pagination) != receipt_page.get("pagination_direct_field_count"):
            raise ValueError(f"private pagination field count mismatch on page {page}")
        pagination_field_sets.add(tuple(sorted(str(key) for key in pagination)))

    if len(all_ids) != 15 or len(set(all_ids)) != 15:
        raise ValueError("private pagination aggregate report identity counts changed")
    if len(pagination_field_sets) != 1:
        raise ValueError("pagination direct field set changed across reviewed pages")
    return sorted(private_pages, key=lambda row: int(row["page"]))


def _field_profile(
    field_name: str,
    values: list[object],
    pages: list[int],
    limits: list[int],
) -> dict[str, Any]:
    types = sorted({_value_type(value) for value in values})
    integer_values = (
        [int(value) for value in values]
        if all(isinstance(value, int) and not isinstance(value, bool) for value in values)
        else None
    )
    relations = {
        "equals_requested_page_on_all_pages": values == pages,
        "equals_requested_limit_on_all_pages": values == limits,
        "constant_across_pages": len({_canonical_json(value) for value in values}) == 1,
        "positive_integer_on_all_pages": bool(integer_values)
        and all(value > 0 for value in integer_values),
        "strictly_increases_by_one": bool(integer_values)
        and all(
            integer_values[index] == integer_values[index - 1] + 1
            for index in range(1, len(integer_values))
        ),
        "non_decreasing": bool(integer_values)
        and all(
            integer_values[index] >= integer_values[index - 1]
            for index in range(1, len(integer_values))
        ),
        "equals_zero_based_page_offset": bool(integer_values)
        and all(
            value == (page - 1) * limit
            for value, page, limit in zip(integer_values, pages, limits, strict=True)
        ),
        "equals_one_based_page_start": bool(integer_values)
        and all(
            value == ((page - 1) * limit) + 1
            for value, page, limit in zip(integer_values, pages, limits, strict=True)
        ),
        "equals_full_page_end": bool(integer_values)
        and all(
            value == page * limit
            for value, page, limit in zip(integer_values, pages, limits, strict=True)
        ),
    }
    return {
        "field_name": field_name,
        "observed_types": types,
        "nullable": any(value is None for value in values),
        "observed_on_all_pages": len(values) == len(pages),
        "unique_value_count": len({_canonical_json(value) for value in values}),
        "relations": relations,
        "semantic_assignment": "unassigned",
        "semantic_status": "unresolved",
    }


def _single_candidate(candidates: list[str]) -> str | None:
    return candidates[0] if len(candidates) == 1 else None


def review_report_pagination_semantics(
    evidence_receipt_path: Path,
    private_evidence_path: Path,
    *,
    expected_guild_label: str = "Argentum",
) -> dict[str, Any]:
    """Review private pagination values through exact cross-page relationships only."""
    receipt, receipt_body = _load_object(evidence_receipt_path, "pagination evidence receipt")
    private, private_body = _load_object(private_evidence_path, "private pagination evidence")
    _validate_receipt(receipt, expected_guild_label)

    expected_private_sha256 = _required_string(
        receipt.get("source_private_evidence_sha256"),
        "source_private_evidence_sha256",
    )
    if _sha256_bytes(private_body) != expected_private_sha256:
        raise ValueError("private pagination evidence hash changed after capture")
    private_pages = _validate_private(private, receipt, expected_guild_label)

    pages = [_required_integer(row.get("page"), "private.pages[].page") for row in private_pages]
    limits = [_required_integer(row.get("limit"), "private.pages[].limit") for row in private_pages]
    pagination_objects = [
        _required_object(row.get("pagination"), "private.pages[].pagination")
        for row in private_pages
    ]
    field_names = sorted(pagination_objects[0])
    profiles = {
        field_name: _field_profile(
            field_name,
            [pagination[field_name] for pagination in pagination_objects],
            pages,
            limits,
        )
        for field_name in field_names
    }

    current_page_candidates = [
        name
        for name, profile in profiles.items()
        if profile["relations"]["equals_requested_page_on_all_pages"]
    ]
    page_size_candidates = [
        name
        for name, profile in profiles.items()
        if profile["relations"]["equals_requested_limit_on_all_pages"]
        and name not in current_page_candidates
    ]
    current_page_field = _single_candidate(current_page_candidates)
    page_size_field = _single_candidate(page_size_candidates)

    total_pairs: list[tuple[str, str]] = []
    if page_size_field is not None:
        page_size_values = [
            _required_integer(pagination[page_size_field], page_size_field)
            for pagination in pagination_objects
        ]
        page_size = page_size_values[0]
        constant_integer_fields: dict[str, int] = {}
        for field_name in field_names:
            if field_name in {current_page_field, page_size_field}:
                continue
            values = [pagination[field_name] for pagination in pagination_objects]
            if (
                all(isinstance(value, int) and not isinstance(value, bool) for value in values)
                and len(set(values)) == 1
                and values[0] > 0
            ):
                constant_integer_fields[field_name] = int(values[0])
        for total_records_field, total_records in constant_integer_fields.items():
            for total_pages_field, total_pages in constant_integer_fields.items():
                if total_records_field == total_pages_field:
                    continue
                if total_records < 15 or total_pages < max(pages):
                    continue
                if math.ceil(total_records / page_size) == total_pages:
                    total_pairs.append((total_records_field, total_pages_field))

    unique_total_pairs = sorted(set(total_pairs))
    if len(unique_total_pairs) == 1:
        total_record_count_field, total_page_count_field = unique_total_pairs[0]
    else:
        total_record_count_field = None
        total_page_count_field = None

    has_next_candidates: list[str] = []
    if total_page_count_field is not None:
        total_pages = _required_integer(
            pagination_objects[0][total_page_count_field],
            total_page_count_field,
        )
        for field_name in field_names:
            values = [pagination[field_name] for pagination in pagination_objects]
            if all(isinstance(value, bool) for value in values) and values == [
                page < total_pages for page in pages
            ]:
                has_next_candidates.append(field_name)
    has_next_page_field = _single_candidate(has_next_candidates)

    assignments = {
        "current_page_field": current_page_field,
        "page_size_field": page_size_field,
        "total_record_count_field": total_record_count_field,
        "total_page_count_field": total_page_count_field,
        "has_next_page_field": has_next_page_field,
    }
    assignment_labels = {
        current_page_field: "current_page",
        page_size_field: "page_size",
        total_record_count_field: "total_record_count",
        total_page_count_field: "total_page_count",
        has_next_page_field: "has_next_page",
    }
    assignment_labels.pop(None, None)
    for field_name, semantic in assignment_labels.items():
        profiles[field_name]["semantic_assignment"] = semantic
        profiles[field_name]["semantic_status"] = "relationship_verified"

    pagination_semantics_verified = all(
        assignments[field_name] is not None
        for field_name in (
            "current_page_field",
            "page_size_field",
            "total_record_count_field",
            "total_page_count_field",
        )
    )
    termination_condition_verified = pagination_semantics_verified
    ready_for_manifest_capture = termination_condition_verified

    checks = {
        "bounded_evidence_receipt_verified": True,
        "private_evidence_sha256_verified": True,
        "private_page_metadata_matches_receipt": True,
        "report_id_sets_match_scalar_free_hashes": True,
        "pagination_shapes_match_scalar_free_hashes": True,
        "pagination_field_set_stable_across_pages": True,
        "requested_page_relations_evaluated": True,
        "requested_limit_relations_evaluated": True,
        "total_record_page_pair_evaluated": True,
        "source_scalar_values_excluded_from_review_receipt": True,
    }
    return {
        "schema_version": _REVIEW_SCHEMA_VERSION,
        "review_kind": "report_pagination_semantic_review",
        "review_version": _REVIEW_VERSION,
        "generated_at": _generated_at(),
        "source_evidence_receipt_name": evidence_receipt_path.name,
        "source_evidence_receipt_sha256": _sha256_bytes(receipt_body),
        "source_private_evidence_name": private_evidence_path.name,
        "source_private_evidence_sha256": _sha256_bytes(private_body),
        "target": {
            "guild_label": expected_guild_label,
            "guild_identity_status": "operator_named_target_unresolved",
        },
        "request": {
            "route_template": _EXPECTED_ROUTE,
            "reviewed_pages": pages,
            "limit": limits[0],
            "sort_by": "created_at",
            "sort_order": "desc",
        },
        "field_contracts": [profiles[field_name] for field_name in field_names],
        "semantic_assignments": {
            **assignments,
            "current_page_candidate_count": len(current_page_candidates),
            "page_size_candidate_count": len(page_size_candidates),
            "total_record_page_pair_candidate_count": len(unique_total_pairs),
            "has_next_page_candidate_count": len(has_next_candidates),
        },
        "termination_contract": {
            "status": (
                "verified_from_unique_cross_page_relations"
                if termination_condition_verified
                else "unresolved"
            ),
            "strategy": (
                "request_pages_1_through_total_page_count_inclusive"
                if termination_condition_verified
                else None
            ),
            "current_page_field": current_page_field,
            "total_page_count_field": total_page_count_field,
            "inclusive_last_page": True if termination_condition_verified else None,
            "automatic_network_collection_allowed": False,
        },
        "integrity_checks": checks,
        "decision_boundary": {
            "status": "pagination_semantics_reviewed",
            "pagination_field_semantics_verified": pagination_semantics_verified,
            "termination_condition_verified": termination_condition_verified,
            "limit_behavior_above_5_verified": False,
            "cross_page_deduplication_key": "/reports/*/id",
            "cross_page_deduplication_policy_verified": False,
            "ready_for_exhaustive_public_report_manifest_capture": ready_for_manifest_capture,
            "ready_for_full_guild_crawl": False,
            "ready_for_guild_identity_review": False,
            "ready_for_guild_filtering": False,
            "ready_for_multi_report_character_graph": False,
            "ready_for_performance_model": False,
            "ready_for_global_benchmark": False,
            "ready_for_bis25_scoring": False,
            "planner_scoring_allowed": False,
            "private_evidence_contains_source_scalar_values": True,
        },
        "summary": {
            "reviewed_page_count": len(private_pages),
            "pagination_direct_field_count": len(field_names),
            "relationship_verified_field_count": len(assignment_labels),
            "unresolved_field_count": len(field_names) - len(assignment_labels),
            "current_page_candidate_count": len(current_page_candidates),
            "page_size_candidate_count": len(page_size_candidates),
            "total_record_page_pair_candidate_count": len(unique_total_pairs),
            "has_next_page_candidate_count": len(has_next_candidates),
            "pagination_field_semantics_verified": pagination_semantics_verified,
            "termination_condition_verified": termination_condition_verified,
            "ready_for_exhaustive_public_report_manifest_capture": ready_for_manifest_capture,
            "ready_for_full_guild_crawl": False,
            "ready_for_bis25_scoring": False,
            "integrity_check_count": len(checks),
            "all_integrity_checks_passed": True,
            "contains_source_scalar_values": False,
            "private_evidence_contains_source_scalar_values": True,
        },
    }
