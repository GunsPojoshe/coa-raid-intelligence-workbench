from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

_REVIEW_KIND = "guild_limit_semantics_review"
_REVIEW_VERSION = "guild-limit-semantics-review-v1"
_CAPTURE_KIND = "guild_limit_semantics_capture"
_CAPTURE_VERSION = "guild-limit-semantics-capture-v1"
_ROUTE_REVIEW_KIND = "guild_route_semantics_review"
_ROUTE_REVIEW_VERSION = "guild-route-semantics-review-v1"
_ROUTE = "/api/guilds/search"
_FIELDS = [
    {"field": "id", "types": ["integer"]},
    {"field": "name", "types": ["string"]},
    {"field": "realm", "types": ["string"]},
    {"field": "report_count", "types": ["string"]},
]
_CASE_LIMITS = {"low_limit": 1, "high_limit": 25, "high_limit_repeat": 25}
_FALSE_GATES = (
    "pagination_semantics_verified",
    "termination_semantics_verified",
    "completeness_verified",
    "guild_api_route_semantics_verified",
    "ready_for_full_guild_crawl",
    "planner_scoring_allowed",
)


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _document_hashes(value: bytes) -> set[str]:
    lf = value.replace(b"\r\n", b"\n")
    crlf = lf.replace(b"\n", b"\r\n")
    return {_sha256(value), _sha256(lf), _sha256(crlf)}


def _load(path: Path, label: str) -> tuple[dict[str, Any], bytes]:
    try:
        body = path.read_bytes()
        payload = json.loads(body)
    except OSError as exc:
        raise ValueError(f"unable to read {label}: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"{label} is not valid JSON: {path}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"{label} must contain a JSON object")
    return payload, body


def _write(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    body = (json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_bytes(body)
    temporary.replace(path)


def _object(value: object, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    return value


def _array(value: object, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"{label} must be an array")
    return value


def _integer(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{label} must be an integer")
    return value


def _hash(value: object, label: str) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise ValueError(f"{label} must be SHA-256")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{label} must be hexadecimal") from exc
    return value


def _expect(source: Mapping[str, Any], expected: Mapping[str, object], label: str) -> None:
    for field, value in expected.items():
        if source.get(field) != value:
            raise ValueError(f"{label} mismatch: {field}")


def _expect_false_gates(source: Mapping[str, Any], label: str) -> None:
    _expect(source, {field: False for field in _FALSE_GATES}, label)


def _validate_route_review(review: Mapping[str, Any]) -> None:
    _expect(
        review,
        {
            "schema_version": 1,
            "review_kind": _ROUTE_REVIEW_KIND,
            "review_version": _ROUTE_REVIEW_VERSION,
        },
        "route review",
    )
    checks = _object(review.get("integrity_checks"), "route review integrity_checks")
    if len(checks) != 22 or any(value is not True for value in checks.values()):
        raise ValueError("route review integrity checks failed")

    summary = _object(review.get("summary"), "route review summary")
    _expect(
        summary,
        {
            "all_integrity_checks_passed": True,
            "integrity_check_count": 22,
            "route_shape_and_response_schema_reviewed": True,
            "limit_parameter_accepted": True,
            "ready_for_bounded_limit_semantics_capture": True,
            "limit_truncation_semantics_verified": False,
            "contains_raw_payload": False,
            "contains_source_scalar_values": False,
        },
        "route review summary",
    )
    _expect_false_gates(summary, "route review summary")

    route = _object(review.get("route_review"), "route review route_review")
    _expect(
        route,
        {
            "route_template": _ROUTE,
            "route_template_verified": True,
            "query_parameter_q_observed": True,
            "query_shape_with_limit_verified": True,
            "limit_parameter_accepted": True,
            "limit_truncation_semantics_verified": False,
            "contains_query_values": False,
        },
        "route review route",
    )
    schema = _object(review.get("response_schema_review"), "route review schema")
    _expect(
        schema,
        {
            "top_level_kind": "object",
            "top_level_keys": ["guilds", "success"],
            "guild_collection_field": "guilds",
            "guild_record_fields": _FIELDS,
            "response_envelope_verified": True,
            "guild_record_schema_verified": True,
            "schema_fingerprint_stable": True,
            "pagination_object_observed": False,
            "pagination_semantics_verified": False,
            "contains_source_scalar_values": False,
        },
        "route review schema",
    )
    boundary = _object(review.get("decision_boundary"), "route review boundary")
    _expect(
        boundary,
        {
            "guild_route_template_verified": True,
            "guild_query_shapes_verified": True,
            "guild_response_schema_verified": True,
            "limit_parameter_accepted": True,
            "ready_for_bounded_limit_semantics_capture": True,
            "limit_truncation_semantics_verified": False,
            "automatic_full_guild_crawl_allowed": False,
            "ready_for_multi_report_character_graph": False,
            "ready_for_performance_model": False,
            "ready_for_bis25_scoring": False,
        },
        "route review boundary",
    )
    _expect_false_gates(boundary, "route review boundary")


def _attempts(capture: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    rows = [_object(row, "capture attempt") for row in _array(capture.get("attempts"), "attempts")]
    if len(rows) != 3:
        raise ValueError("limit capture must contain exactly three attempts")
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        case = row.get("case")
        if not isinstance(case, str) or case not in _CASE_LIMITS or case in result:
            raise ValueError("limit capture case set mismatch")
        result[case] = row
    if set(result) != set(_CASE_LIMITS):
        raise ValueError("limit capture case set mismatch")
    return result


def _validate_attempt(row: Mapping[str, Any], case: str) -> dict[str, Any]:
    _expect(
        row,
        {
            "case": case,
            "route_template": _ROUTE,
            "query_keys": ["q", "limit"],
            "limit": _CASE_LIMITS[case],
            "return_code": 0,
            "http_status": 200,
            "failure_class": None,
            "body_captured": True,
            "json_valid": True,
            "response_candidate": True,
            "contains_error_text": False,
            "contains_source_scalar_values": False,
        },
        f"limit capture attempt {case}",
    )
    body_bytes = _integer(row.get("body_bytes"), f"{case}.body_bytes")
    if body_bytes < 1:
        raise ValueError(f"{case}.body_bytes must be positive")
    archive = _object(row.get("capture"), f"{case}.capture")
    for field in ("raw_id", "observation_id", "payload_hash", "schema_fingerprint"):
        _hash(archive.get(field), f"{case}.capture.{field}")
    if archive.get("bytes_uncompressed") != body_bytes:
        raise ValueError(f"{case} archived byte count mismatch")

    shape = _object(row.get("shape_summary"), f"{case}.shape_summary")
    _expect(
        shape,
        {
            "top_level_kind": "object",
            "top_level_keys": ["guilds", "success"],
            "guild_collection_observed": True,
            "guild_field_inventory": _FIELDS,
            "all_records_have_supported_id": True,
            "contains_source_scalar_values": False,
        },
        f"limit capture shape {case}",
    )
    count = _integer(shape.get("guild_result_count"), f"{case}.guild_result_count")
    if shape.get("guild_object_count") != count or shape.get("distinct_non_null_id_count") != count:
        raise ValueError(f"{case} guild count mismatch")
    for field in (
        "guild_field_inventory_sha256",
        "ordered_record_set_sha256",
        "ordered_source_id_hashes_sha256",
    ):
        _hash(shape.get(field), f"{case}.shape.{field}")
    return shape


def review_guild_limit_semantics(
    *,
    capture_path: Path,
    route_review_path: Path,
    receipt_output_path: Path,
) -> dict[str, Any]:
    """Promote only bounded limit truncation semantics from scalar-free evidence."""
    capture, capture_body = _load(capture_path, "guild limit capture")
    route_review, route_body = _load(route_review_path, "guild route review")
    _validate_route_review(route_review)
    _expect(
        capture,
        {
            "schema_version": 1,
            "capture_kind": _CAPTURE_KIND,
            "capture_version": _CAPTURE_VERSION,
            "source_route_review_name": route_review_path.name,
        },
        "limit capture",
    )
    bound_route_hash = _hash(
        capture.get("source_route_review_sha256"),
        "capture.source_route_review_sha256",
    )
    if bound_route_hash not in _document_hashes(route_body):
        raise ValueError("capture route review SHA-256 mismatch")

    checks_in = _object(capture.get("integrity_checks"), "capture integrity_checks")
    if len(checks_in) != 15 or any(value is not True for value in checks_in.values()):
        raise ValueError("limit capture integrity checks failed")
    _expect(
        _object(capture.get("target"), "capture target"),
        {
            "query_value_published": False,
            "request_urls_published": False,
            "source_guild_ids_published": False,
            "raw_records_published": False,
        },
        "limit capture privacy boundary",
    )
    _expect(
        _object(capture.get("request_contract"), "capture request_contract"),
        {
            "route_template": _ROUTE,
            "query_keys": ["q", "limit"],
            "case_count": 3,
            "low_limit": 1,
            "high_limit": 25,
            "high_limit_repeat_count": 1,
            "selected_profile": "spa_fetch_context",
            "transport": "curl_http1_1",
            "redirects_allowed": False,
            "credentials_supplied": False,
        },
        "limit capture request contract",
    )

    attempts = _attempts(capture)
    shapes = {case: _validate_attempt(attempts[case], case) for case in _CASE_LIMITS}
    counts = {
        case: _integer(shape.get("guild_result_count"), f"{case}.guild_result_count")
        for case, shape in shapes.items()
    }
    cross = _object(capture.get("cross_case_evidence"), "capture cross_case_evidence")
    _expect(
        cross,
        {
            "all_responses_completed": True,
            "response_schema_consistent": True,
            "observed_result_counts": [1, 7],
            "low_limit_saturated": True,
            "multi_result_observed": True,
            "high_limit_respected": True,
            "high_limit_repeat_stable": True,
            "high_limit_source_id_order_stable_by_hash": True,
            "low_result_is_high_result_prefix_by_id_hash": True,
            "limit_truncation_evidence_observed": True,
            "contains_source_scalar_values": False,
        },
        "limit capture cross-case evidence",
    )
    summary_in = _object(capture.get("summary"), "capture summary")
    _expect(
        summary_in,
        {
            "all_integrity_checks_passed": True,
            "integrity_check_count": 15,
            "attempt_count": 3,
            "completed_attempt_count": 3,
            "all_responses_completed": True,
            "multi_result_observed": True,
            "limit_truncation_evidence_observed": True,
            "ready_for_limit_semantics_review": True,
            "contains_raw_payload": False,
            "contains_source_scalar_values": False,
            "limit_truncation_semantics_verified": False,
        },
        "limit capture summary",
    )
    _expect_false_gates(summary_in, "limit capture summary")
    boundary_in = _object(capture.get("decision_boundary"), "capture boundary")
    _expect(
        boundary_in,
        {
            "status": "guild_limit_semantics_capture_review_ready",
            "guild_route_shape_and_schema_reviewed": True,
            "bounded_limit_semantics_capture_completed": True,
            "multi_result_observed": True,
            "limit_truncation_evidence_observed": True,
            "ready_for_limit_semantics_review": True,
            "limit_truncation_semantics_verified": False,
            "automatic_full_guild_crawl_allowed": False,
            "ready_for_multi_report_character_graph": False,
            "ready_for_performance_model": False,
            "ready_for_bis25_scoring": False,
        },
        "limit capture boundary",
    )
    _expect_false_gates(boundary_in, "limit capture boundary")

    field_hashes = {str(shape["guild_field_inventory_sha256"]) for shape in shapes.values()}
    schema_hashes = {
        str(_object(row["capture"], "attempt capture")["schema_fingerprint"])
        for row in attempts.values()
    }
    high = shapes["high_limit"]
    repeat = shapes["high_limit_repeat"]
    checks = {
        "route_review_contract_verified": True,
        "route_review_integrity_checks_verified": True,
        "route_review_privacy_boundary_verified": True,
        "capture_route_review_name_verified": True,
        "capture_route_review_sha256_verified": True,
        "capture_contract_verified": True,
        "capture_integrity_checks_verified": True,
        "capture_privacy_boundary_verified": True,
        "request_route_verified": True,
        "request_case_set_verified": True,
        "request_limits_verified": True,
        "credentials_not_supplied": True,
        "redirects_disabled": True,
        "all_three_responses_completed": True,
        "response_envelope_verified": True,
        "guild_record_schema_verified": True,
        "response_schema_stable": len(field_hashes) == 1 and len(schema_hashes) == 1,
        "low_limit_saturated": counts["low_limit"] == 1,
        "multi_result_observed": counts["high_limit"] > counts["low_limit"],
        "high_limit_respected": counts["high_limit"] <= 25,
        "high_limit_repeat_count_stable": counts["high_limit"] == counts["high_limit_repeat"],
        "high_limit_ordered_records_stable": (
            high["ordered_record_set_sha256"] == repeat["ordered_record_set_sha256"]
        ),
        "high_limit_source_id_order_stable_by_hash": (
            high["ordered_source_id_hashes_sha256"]
            == repeat["ordered_source_id_hashes_sha256"]
        ),
        "low_result_prefix_evidence_verified": True,
        "capture_did_not_pre_promote_limit_semantics": True,
        "pagination_not_overclaimed": True,
        "termination_not_overclaimed": True,
        "completeness_not_overclaimed": True,
        "full_crawl_remains_disabled": True,
        "planner_scoring_remains_disabled": True,
    }
    failed = sorted(name for name, value in checks.items() if value is not True)
    if failed:
        raise ValueError("limit semantics review checks failed: " + ", ".join(failed))

    receipt = {
        "schema_version": 1,
        "review_kind": _REVIEW_KIND,
        "review_version": _REVIEW_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "source_capture_name": capture_path.name,
        "source_capture_sha256": _sha256(capture_body),
        "source_route_review_name": route_review_path.name,
        "source_route_review_sha256": _sha256(route_body),
        "source_binding_review": {
            "capture_bound_route_review_sha256": bound_route_hash,
            "route_review_line_endings_normalized": bound_route_hash != _sha256(route_body),
            "semantic_document_identity_preserved": True,
        },
        "target": {
            "query_value_published": False,
            "request_urls_published": False,
            "source_guild_ids_published": False,
            "raw_records_published": False,
            "raw_payload_published": False,
        },
        "reviewed_request_contract": {
            "route_template": _ROUTE,
            "query_keys": ["q", "limit"],
            "low_limit": 1,
            "high_limit": 25,
            "high_limit_repeat_count": 1,
            "observed_result_counts": [
                counts["low_limit"],
                counts["high_limit"],
                counts["high_limit_repeat"],
            ],
            "contains_query_values": False,
        },
        "cross_case_evidence": {
            "attempt_count": 3,
            "completed_attempt_count": 3,
            "low_result_count": counts["low_limit"],
            "high_result_count": counts["high_limit"],
            "high_repeat_result_count": counts["high_limit_repeat"],
            "response_schema_consistent": True,
            "low_limit_saturated": True,
            "multi_result_observed": True,
            "high_limit_respected": True,
            "high_limit_repeat_stable": True,
            "high_limit_source_id_order_stable_by_hash": True,
            "low_result_is_high_result_prefix_by_id_hash": True,
            "limit_truncation_evidence_observed": True,
            "contains_source_scalar_values": False,
        },
        "integrity_checks": checks,
        "summary": {
            "all_integrity_checks_passed": True,
            "integrity_check_count": len(checks),
            "limit_truncation_evidence_observed": True,
            "limit_truncation_semantics_verified": True,
            "ready_for_bounded_pagination_semantics_capture": True,
            "pagination_semantics_verified": False,
            "termination_semantics_verified": False,
            "completeness_verified": False,
            "guild_api_route_semantics_verified": False,
            "ready_for_full_guild_crawl": False,
            "planner_scoring_allowed": False,
            "contains_raw_payload": False,
            "contains_source_scalar_values": False,
        },
        "decision_boundary": {
            "status": "guild_limit_truncation_semantics_reviewed",
            "guild_route_shape_and_schema_reviewed": True,
            "bounded_limit_semantics_capture_completed": True,
            "multi_result_observed": True,
            "limit_truncation_evidence_observed": True,
            "limit_truncation_semantics_verified": True,
            "ready_for_bounded_pagination_semantics_capture": True,
            "pagination_semantics_verified": False,
            "termination_semantics_verified": False,
            "completeness_verified": False,
            "guild_api_route_semantics_verified": False,
            "automatic_full_guild_crawl_allowed": False,
            "ready_for_full_guild_crawl": False,
            "ready_for_multi_report_character_graph": False,
            "ready_for_performance_model": False,
            "ready_for_bis25_scoring": False,
            "planner_scoring_allowed": False,
        },
    }
    _write(receipt_output_path, receipt)
    return receipt


__all__ = ["review_guild_limit_semantics"]
