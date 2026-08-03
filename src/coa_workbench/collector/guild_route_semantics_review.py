from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

_REVIEW_KIND = "guild_route_semantics_review"
_REVIEW_VERSION = "guild-route-semantics-review-v1"
_CAPTURE_KIND = "guild_route_semantics_capture"
_CAPTURE_VERSION = "guild-route-semantics-capture-v1"
_CONTRACT_KIND = "guild_full_crawl_collection_contract"
_CONTRACT_VERSION = "guild-full-crawl-contract-v1"
_ACCESS_KIND = "guild_identity_search_access_diagnostic"
_ACCESS_VERSION = "guild-identity-search-access-diagnostic-v1"
_ROUTE_TEMPLATE = "/api/guilds/search"
_SELECTED_PROFILE = "spa_fetch_context"
_EXPECTED_TOP_LEVEL_KEYS = ["guilds", "success"]
_EXPECTED_GUILD_FIELDS = [
    {"field": "id", "types": ["integer"]},
    {"field": "name", "types": ["string"]},
    {"field": "realm", "types": ["string"]},
    {"field": "report_count", "types": ["string"]},
]
_EXPECTED_CASES: dict[str, tuple[list[str], int | None]] = {
    "exact_label_limit_1": (["q", "limit"], 1),
    "exact_label_limit_reviewed": (["q", "limit"], 25),
    "exact_label_without_limit": (["q"], None),
}


def _generated_at() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _document_hashes(value: bytes) -> set[str]:
    """Return raw, LF and CRLF hashes for one text document."""
    normalized_lf = value.replace(b"\r\n", b"\n")
    normalized_crlf = normalized_lf.replace(b"\n", b"\r\n")
    return {
        _sha256_bytes(value),
        _sha256_bytes(normalized_lf),
        _sha256_bytes(normalized_crlf),
    }


def _load_object(path: Path, label: str) -> tuple[dict[str, Any], bytes]:
    try:
        body = path.read_bytes()
    except OSError as exc:
        raise ValueError(f"unable to read {label}: {path}") from exc
    try:
        payload = json.loads(body)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{label} is not valid JSON: {path}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"{label} must contain a JSON object")
    return payload, body


def _write_json(path: Path, payload: Mapping[str, Any]) -> bytes:
    path.parent.mkdir(parents=True, exist_ok=True)
    body = (json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_bytes(body)
    temporary.replace(path)
    return body


def _required_object(value: object, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"guild route semantics review field {field_name} must be an object")
    return value


def _required_list(value: object, field_name: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"guild route semantics review field {field_name} must be a list")
    return value


def _required_sha256(value: object, field_name: str) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise ValueError(f"guild route semantics review field {field_name} must be SHA-256")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(
            f"guild route semantics review field {field_name} must be hexadecimal"
        ) from exc
    return value


def _validate_source_binding(
    *,
    source_path: Path,
    source_body: bytes,
    expected_name: object,
    expected_sha256: object,
    label: str,
) -> bool:
    if expected_name != source_path.name:
        raise ValueError(f"{label} source file name mismatch")
    expected_hash = _required_sha256(expected_sha256, f"{label}.sha256")
    hashes = _document_hashes(source_body)
    if expected_hash not in hashes:
        raise ValueError(f"{label} source SHA-256 mismatch")
    return expected_hash != _sha256_bytes(source_body)


def _validate_contract(contract: Mapping[str, Any], expected_label: str) -> None:
    if contract.get("schema_version") != 1:
        raise ValueError("full-crawl contract schema mismatch")
    if contract.get("contract_kind") != _CONTRACT_KIND:
        raise ValueError("full-crawl contract kind mismatch")
    if contract.get("contract_version") != _CONTRACT_VERSION:
        raise ValueError("full-crawl contract version mismatch")

    target = _required_object(contract.get("target"), "contract.target")
    if target.get("guild_label") != expected_label:
        raise ValueError("full-crawl contract guild label mismatch")
    if target.get("source_guild_id_published") is not False:
        raise ValueError("full-crawl contract publishes source guild ID")
    if target.get("report_ids_published") is not False:
        raise ValueError("full-crawl contract publishes report IDs")

    summary = _required_object(contract.get("summary"), "contract.summary")
    expected_summary = {
        "all_integrity_checks_passed": True,
        "contains_source_scalar_values": False,
        "full_crawl_collection_contract_reviewed": True,
        "ready_for_bounded_route_semantics_capture": True,
        "guild_api_route_semantics_verified": False,
        "ready_for_full_guild_crawl": False,
        "planner_scoring_allowed": False,
    }
    for field_name, expected in expected_summary.items():
        if summary.get(field_name) is not expected:
            raise ValueError(f"full-crawl contract summary mismatch: {field_name}")

    boundary = _required_object(contract.get("decision_boundary"), "contract.boundary")
    expected_boundary = {
        "automatic_full_guild_crawl_allowed": False,
        "guild_api_route_semantics_verified": False,
        "ready_for_full_guild_crawl": False,
        "planner_scoring_allowed": False,
    }
    for field_name, expected in expected_boundary.items():
        if boundary.get(field_name) is not expected:
            raise ValueError(f"full-crawl contract boundary mismatch: {field_name}")


def _validate_access(access: Mapping[str, Any], expected_label: str) -> None:
    if access.get("schema_version") != 1:
        raise ValueError("public access diagnostic schema mismatch")
    if access.get("diagnostic_kind") != _ACCESS_KIND:
        raise ValueError("public access diagnostic kind mismatch")
    if access.get("diagnostic_version") != _ACCESS_VERSION:
        raise ValueError("public access diagnostic version mismatch")

    target = _required_object(access.get("target"), "access.target")
    if target.get("guild_label") != expected_label:
        raise ValueError("public access diagnostic guild label mismatch")
    if target.get("request_url_published") is not False:
        raise ValueError("public access diagnostic publishes request URL")
    if target.get("source_guild_id_published") is not False:
        raise ValueError("public access diagnostic publishes source guild ID")

    summary = _required_object(access.get("summary"), "access.summary")
    if summary.get("all_integrity_checks_passed") is not True:
        raise ValueError("public access diagnostic integrity checks failed")
    if summary.get("selected_access_profile") != _SELECTED_PROFILE:
        raise ValueError("public access diagnostic profile mismatch")
    if summary.get("contains_source_scalar_values") is not False:
        raise ValueError("public access diagnostic contains source scalar values")

    boundary = _required_object(access.get("decision_boundary"), "access.boundary")
    expected_boundary = {
        "ready_for_profiled_guild_search_probe": True,
        "guild_api_route_semantics_verified": False,
        "ready_for_full_guild_crawl": False,
        "planner_scoring_allowed": False,
    }
    for field_name, expected in expected_boundary.items():
        if boundary.get(field_name) is not expected:
            raise ValueError(f"public access diagnostic boundary mismatch: {field_name}")
    if boundary.get("selected_access_profile") != _SELECTED_PROFILE:
        raise ValueError("public access diagnostic boundary profile mismatch")


def _attempts_by_case(capture: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    attempts = [
        _required_object(value, "capture.attempt")
        for value in _required_list(capture.get("attempts"), "capture.attempts")
    ]
    if len(attempts) != len(_EXPECTED_CASES):
        raise ValueError("route-semantics capture must contain exactly three attempts")

    result: dict[str, dict[str, Any]] = {}
    for attempt in attempts:
        case = attempt.get("case")
        if not isinstance(case, str) or case not in _EXPECTED_CASES:
            raise ValueError("route-semantics capture contains an unexpected case")
        if case in result:
            raise ValueError("route-semantics capture contains a duplicate case")
        result[case] = attempt
    return result


def _validate_attempt(
    attempt: Mapping[str, Any],
    *,
    expected_query_keys: list[str],
    expected_limit: int | None,
) -> dict[str, Any]:
    expected_values = {
        "route_template": _ROUTE_TEMPLATE,
        "query_keys": expected_query_keys,
        "limit": expected_limit,
        "return_code": 0,
        "http_status": 200,
        "failure_class": None,
        "body_captured": True,
        "json_valid": True,
        "response_candidate": True,
        "contains_error_text": False,
        "contains_source_scalar_values": False,
    }
    for field_name, expected in expected_values.items():
        if attempt.get(field_name) != expected:
            raise ValueError(f"route-semantics attempt mismatch: {field_name}")

    body_bytes = attempt.get("body_bytes")
    if isinstance(body_bytes, bool) or not isinstance(body_bytes, int) or body_bytes < 1:
        raise ValueError("route-semantics attempt body byte count is invalid")

    capture = _required_object(attempt.get("capture"), "attempt.capture")
    for field_name in ("raw_id", "observation_id", "payload_hash", "schema_fingerprint"):
        _required_sha256(capture.get(field_name), f"attempt.capture.{field_name}")
    if capture.get("bytes_uncompressed") != body_bytes:
        raise ValueError("route-semantics attempt captured byte count mismatch")

    shape = _required_object(attempt.get("shape_summary"), "attempt.shape_summary")
    expected_shape = {
        "top_level_kind": "object",
        "top_level_keys": _EXPECTED_TOP_LEVEL_KEYS,
        "guild_collection_observed": True,
        "guild_field_inventory": _EXPECTED_GUILD_FIELDS,
        "guild_object_count": 1,
        "guild_result_count": 1,
        "distinct_non_null_id_count": 1,
        "target_name_casefold_match_count": 1,
        "pagination_object_observed": False,
        "pagination_keys": [],
        "pagination_field_types": [],
        "contains_source_scalar_values": False,
    }
    for field_name, expected in expected_shape.items():
        if shape.get(field_name) != expected:
            raise ValueError(f"route-semantics response shape mismatch: {field_name}")
    for field_name in (
        "guild_field_inventory_sha256",
        "ordered_guild_records_sha256",
        "id_value_set_sha256",
    ):
        _required_sha256(shape.get(field_name), f"shape.{field_name}")
    return shape


def review_guild_route_semantics(
    *,
    capture_path: Path,
    full_crawl_contract_path: Path,
    public_access_diagnostic_path: Path,
    receipt_output_path: Path,
    expected_guild_label: str = "Argentum",
) -> dict[str, Any]:
    """Review bounded route and schema evidence without enabling full crawl."""
    capture, capture_body = _load_object(capture_path, "route-semantics capture")
    contract, contract_body = _load_object(full_crawl_contract_path, "full-crawl contract")
    access, access_body = _load_object(
        public_access_diagnostic_path,
        "public access diagnostic",
    )

    _validate_contract(contract, expected_guild_label)
    _validate_access(access, expected_guild_label)

    if capture.get("schema_version") != 1:
        raise ValueError("route-semantics capture schema mismatch")
    if capture.get("capture_kind") != _CAPTURE_KIND:
        raise ValueError("route-semantics capture kind mismatch")
    if capture.get("capture_version") != _CAPTURE_VERSION:
        raise ValueError("route-semantics capture version mismatch")

    contract_line_endings_normalized = _validate_source_binding(
        source_path=full_crawl_contract_path,
        source_body=contract_body,
        expected_name=capture.get("source_contract_name"),
        expected_sha256=capture.get("source_contract_sha256"),
        label="full-crawl contract",
    )
    access_line_endings_normalized = _validate_source_binding(
        source_path=public_access_diagnostic_path,
        source_body=access_body,
        expected_name=capture.get("source_public_access_name"),
        expected_sha256=capture.get("source_public_access_sha256"),
        label="public access diagnostic",
    )

    target = _required_object(capture.get("target"), "capture.target")
    if target.get("guild_label") != expected_guild_label:
        raise ValueError("route-semantics capture guild label mismatch")
    for field_name in (
        "report_ids_published",
        "request_urls_published",
        "source_guild_id_published",
    ):
        if target.get(field_name) is not False:
            raise ValueError(f"route-semantics capture privacy boundary mismatch: {field_name}")

    capture_checks = _required_object(
        capture.get("integrity_checks"),
        "capture.integrity_checks",
    )
    if not capture_checks or any(value is not True for value in capture_checks.values()):
        raise ValueError("route-semantics capture contains failed integrity checks")

    summary = _required_object(capture.get("summary"), "capture.summary")
    expected_summary = {
        "all_integrity_checks_passed": True,
        "all_responses_completed": True,
        "attempt_count": 3,
        "completed_attempt_count": 3,
        "contains_raw_payload": False,
        "contains_source_scalar_values": False,
        "guild_api_route_semantics_verified": False,
        "planner_scoring_allowed": False,
        "ready_for_full_guild_crawl": False,
        "ready_for_route_semantics_review": True,
        "response_shape_consistent": True,
    }
    for field_name, expected in expected_summary.items():
        if summary.get(field_name) != expected:
            raise ValueError(f"route-semantics capture summary mismatch: {field_name}")
    if summary.get("integrity_check_count") != len(capture_checks):
        raise ValueError("route-semantics capture integrity check count mismatch")

    request_contract = _required_object(
        capture.get("request_contract"),
        "capture.request_contract",
    )
    expected_request = {
        "case_count": 3,
        "credentials_supplied": False,
        "observed_query_shapes": [["q", "limit"], ["q"]],
        "redirects_allowed": False,
        "route_template": _ROUTE_TEMPLATE,
        "selected_profile": _SELECTED_PROFILE,
    }
    for field_name, expected in expected_request.items():
        if request_contract.get(field_name) != expected:
            raise ValueError(f"route-semantics request contract mismatch: {field_name}")

    attempts = _attempts_by_case(capture)
    if set(attempts) != set(_EXPECTED_CASES):
        raise ValueError("route-semantics capture case set mismatch")
    shapes: dict[str, dict[str, Any]] = {}
    for case, (query_keys, limit) in _EXPECTED_CASES.items():
        shapes[case] = _validate_attempt(
            attempts[case],
            expected_query_keys=query_keys,
            expected_limit=limit,
        )

    payload_hashes = {
        str(_required_object(attempt["capture"], "attempt.capture")["payload_hash"])
        for attempt in attempts.values()
    }
    schema_fingerprints = {
        str(_required_object(attempt["capture"], "attempt.capture")["schema_fingerprint"])
        for attempt in attempts.values()
    }
    field_inventory_hashes = {
        str(shape["guild_field_inventory_sha256"]) for shape in shapes.values()
    }
    ordered_record_hashes = {
        str(shape["ordered_guild_records_sha256"]) for shape in shapes.values()
    }
    id_set_hashes = {str(shape["id_value_set_sha256"]) for shape in shapes.values()}
    result_counts = {int(shape["guild_result_count"]) for shape in shapes.values()}

    cross_case = _required_object(
        capture.get("cross_case_review"),
        "capture.cross_case_review",
    )
    expected_cross_case = {
        "all_responses_completed": True,
        "contains_source_scalar_values": False,
        "guild_collection_observed_on_all_cases": True,
        "limit_parameter_accepted": True,
        "limit_truncation_semantics_verified": False,
        "pagination_object_observed": False,
        "pagination_semantics_verified": False,
        "response_shape_consistent": True,
        "route_shapes_observed": True,
        "source_id_set_stable_by_hash": True,
        "target_name_casefold_match_stable": True,
    }
    for field_name, expected in expected_cross_case.items():
        if cross_case.get(field_name) != expected:
            raise ValueError(f"route-semantics cross-case mismatch: {field_name}")

    checks = {
        "full_crawl_contract_verified": True,
        "public_access_diagnostic_verified": True,
        "source_bindings_verified_across_line_endings": True,
        "capture_integrity_checks_verified": True,
        "capture_privacy_boundary_verified": True,
        "request_case_set_verified": True,
        "route_template_verified": True,
        "query_shapes_verified": True,
        "all_three_responses_completed": True,
        "response_envelope_verified": True,
        "guild_record_schema_verified": True,
        "payload_hash_stable": len(payload_hashes) == 1,
        "schema_fingerprint_stable": len(schema_fingerprints) == 1,
        "field_inventory_stable": len(field_inventory_hashes) == 1,
        "ordered_record_set_stable": len(ordered_record_hashes) == 1,
        "source_id_set_stable_by_hash": len(id_set_hashes) == 1,
        "target_name_casefold_match_stable": all(
            shape["target_name_casefold_match_count"] == 1 for shape in shapes.values()
        ),
        "single_result_observed_in_all_cases": result_counts == {1},
        "limit_truncation_not_overclaimed": True,
        "pagination_not_overclaimed": True,
        "full_crawl_remains_disabled": True,
        "planner_scoring_remains_disabled": True,
    }
    route_shape_and_schema_reviewed = all(checks.values())

    receipt = {
        "schema_version": 1,
        "review_kind": _REVIEW_KIND,
        "review_version": _REVIEW_VERSION,
        "generated_at": _generated_at(),
        "source_capture_name": capture_path.name,
        "source_capture_sha256": _sha256_bytes(capture_body),
        "source_contract_name": full_crawl_contract_path.name,
        "source_contract_sha256": _sha256_bytes(contract_body),
        "source_public_access_name": public_access_diagnostic_path.name,
        "source_public_access_sha256": _sha256_bytes(access_body),
        "source_binding_review": {
            "contract_line_endings_normalized": contract_line_endings_normalized,
            "access_line_endings_normalized": access_line_endings_normalized,
            "semantic_document_identity_preserved": True,
        },
        "target": {
            "guild_label": expected_guild_label,
            "raw_payload_published": False,
            "request_urls_published": False,
            "source_guild_id_published": False,
            "report_ids_published": False,
        },
        "route_review": {
            "route_template": _ROUTE_TEMPLATE,
            "route_template_verified": True,
            "query_parameter_q_observed": True,
            "query_shape_with_limit_verified": True,
            "query_shape_without_limit_verified": True,
            "limit_parameter_accepted": True,
            "limit_values_observed": [1, 25],
            "limit_truncation_semantics_verified": False,
            "target_query_binding_observed": True,
            "general_search_semantics_verified": False,
            "contains_query_values": False,
        },
        "response_schema_review": {
            "top_level_kind": "object",
            "top_level_keys": _EXPECTED_TOP_LEVEL_KEYS,
            "guild_collection_field": "guilds",
            "guild_record_fields": _EXPECTED_GUILD_FIELDS,
            "response_envelope_verified": True,
            "guild_record_schema_verified": True,
            "schema_fingerprint_stable": len(schema_fingerprints) == 1,
            "pagination_object_observed": False,
            "pagination_semantics_verified": False,
            "contains_source_scalar_values": False,
        },
        "cross_case_evidence": {
            "attempt_count": len(attempts),
            "completed_attempt_count": len(attempts),
            "distinct_payload_hash_count": len(payload_hashes),
            "distinct_schema_fingerprint_count": len(schema_fingerprints),
            "distinct_field_inventory_hash_count": len(field_inventory_hashes),
            "distinct_ordered_record_hash_count": len(ordered_record_hashes),
            "distinct_source_id_set_hash_count": len(id_set_hashes),
            "observed_result_counts": sorted(result_counts),
            "single_result_observed_in_all_cases": result_counts == {1},
            "target_name_casefold_match_stable": True,
            "source_id_set_stable_by_hash": True,
            "contains_source_scalar_values": False,
        },
        "integrity_checks": checks,
        "summary": {
            "all_integrity_checks_passed": all(checks.values()),
            "integrity_check_count": len(checks),
            "route_shape_and_response_schema_reviewed": route_shape_and_schema_reviewed,
            "limit_parameter_accepted": True,
            "limit_truncation_semantics_verified": False,
            "pagination_semantics_verified": False,
            "termination_semantics_verified": False,
            "completeness_verified": False,
            "guild_api_route_semantics_verified": False,
            "ready_for_bounded_limit_semantics_capture": route_shape_and_schema_reviewed,
            "ready_for_full_guild_crawl": False,
            "planner_scoring_allowed": False,
            "contains_raw_payload": False,
            "contains_source_scalar_values": False,
        },
        "decision_boundary": {
            "status": "guild_route_shape_and_schema_reviewed",
            "bounded_route_semantics_capture_completed": True,
            "guild_route_template_verified": True,
            "guild_query_shapes_verified": True,
            "guild_response_schema_verified": True,
            "target_query_binding_observed": True,
            "limit_parameter_accepted": True,
            "limit_truncation_semantics_verified": False,
            "pagination_object_observed": False,
            "pagination_semantics_verified": False,
            "termination_semantics_verified": False,
            "completeness_verified": False,
            "guild_api_route_semantics_verified": False,
            "ready_for_bounded_limit_semantics_capture": route_shape_and_schema_reviewed,
            "automatic_full_guild_crawl_allowed": False,
            "ready_for_full_guild_crawl": False,
            "ready_for_multi_report_character_graph": False,
            "ready_for_performance_model": False,
            "ready_for_bis25_scoring": False,
            "planner_scoring_allowed": False,
        },
    }
    _write_json(receipt_output_path, receipt)
    return receipt
