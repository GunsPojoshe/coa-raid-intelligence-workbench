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
) -> None:
    if expected_name != source_path.name:
        raise ValueError(f"{label} source file name mismatch")
    expected_hash = _required_sha256(expected_sha256, f"{label}.sha256")
    if _sha256_bytes(source_body) != expected_hash:
        raise ValueError(f"{label} source SHA-256 mismatch")


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
    if summary.get("all_integrity_checks_passed") is not True:
        raise ValueError("full-crawl contract integrity checks failed")
    if summary.get("full_crawl_collection_contract_reviewed") is not True:
        raise ValueError("full-crawl contract is not reviewed")
    if summary.get("ready_for_bounded_route_semantics_capture") is not True:
        raise ValueError("full-crawl contract does not allow bounded route capture")
    if summary.get("contains_source_scalar_values") is not False:
        raise ValueError("full-crawl contract contains source scalar values")

    boundary = _required_object(
        contract.get("decision_boundary"),
        "contract.decision_boundary",
    )
    if boundary.get("automatic_full_guild_crawl_allowed") is not False:
        raise ValueError("full-crawl contract unexpectedly enables automatic crawl")
    if boundary.get("guild_api_route_semantics_verified") is not False:
        raise ValueError("full-crawl contract already claims route semantics")
    if boundary.get("ready_for_full_guild_crawl") is not False:
        raise ValueError("full-crawl contract already claims crawl readiness")
    if boundary.get("planner_scoring_allowed") is not False:
        raise ValueError("full-crawl contract already enables planner scoring")


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
    if boundary.get("ready_for_profiled_guild_search_probe") is not True:
        raise ValueError("public access diagnostic is not ready for profiled probing")
    if boundary.get("selected_access_profile") != _SELECTED_PROFILE:
        raise ValueError("public access diagnostic boundary profile mismatch")
    if boundary.get("guild_api_route_semantics_verified") is not False:
        raise ValueError("public access diagnostic already claims route semantics")
    if boundary.get("ready_for_full_guild_crawl") is not False:
        raise ValueError("public access diagnostic already claims crawl readiness")
    if boundary.get("planner_scoring_allowed") is not False:
        raise ValueError("public access diagnostic already enables planner scoring")


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
    if set(result) != set(_EXPECTED_CASES):
        raise ValueError("route-semantics capture case set mismatch")
    return result


def _validate_attempt(
    attempt: Mapping[str, Any],
    *,
    expected_query_keys: list[str],
    expected_limit: int | None,
) -> dict[str, Any]:
    if attempt.get("route_template") != _ROUTE_TEMPLATE:
        raise ValueError("route-semantics attempt route template mismatch")
    if attempt.get("query_keys") != expected_query_keys:
        raise ValueError("route-semantics attempt query keys mismatch")
    if attempt.get("limit") != expected_limit:
        raise ValueError("route-semantics attempt limit mismatch")
    if attempt.get("return_code") != 0:
        raise ValueError("route-semantics attempt curl return code mismatch")
    if attempt.get("http_status") != 200:
        raise ValueError("route-semantics attempt HTTP status mismatch")
    if attempt.get("failure_class") is not None:
        raise ValueError("route-semantics attempt contains a failure class")
    if attempt.get("body_captured") is not True:
        raise ValueError("route-semantics attempt body was not captured")
    if attempt.get("json_valid") is not True:
        raise ValueError("route-semantics attempt body is not valid JSON")
    if attempt.get("response_candidate") is not True:
        raise ValueError("route-semantics attempt is not a response candidate")
    if attempt.get("contains_error_text") is not False:
        raise ValueError("route-semantics attempt publishes error text")
    if attempt.get("contains_source_scalar_values") is not False:
        raise ValueError("route-semantics attempt publishes source scalar values")

    body_bytes = attempt.get("body_bytes")
    if isinstance(body_bytes, bool) or not isinstance(body_bytes, int) or body_bytes < 1:
        raise ValueError("route-semantics attempt body byte count is invalid")

    capture = _required_object(attempt.get("capture"), "attempt.capture")
    _required_sha256(capture.get("raw_id"), "attempt.capture.raw_id")
    _required_sha256(capture.get("observation_id"), "attempt.capture.observation_id")
    _required_sha256(capture.get("payload_hash"), "attempt.capture.payload_hash")
    _required_sha256(
        capture.get("schema_fingerprint"),
        "attempt.capture.schema_fingerprint",
    )
    if capture.get("bytes_uncompressed") != body_bytes:
        raise ValueError("route-semantics attempt captured byte count mismatch")

    shape = _required_object(attempt.get("shape_summary"), "attempt.shape_summary")
    if shape.get("top_level_kind") != "object":
        raise ValueError("route-semantics response top-level kind mismatch")
    if shape.get("top_level_keys") != _EXPECTED_TOP_LEVEL_KEYS:
        raise ValueError("route-semantics response top-level keys mismatch")
    if shape.get("guild_collection_observed") is not True:
        raise ValueError("route-semantics response guild collection is missing")
    if shape.get("guild_field_inventory") != _EXPECTED_GUILD_FIELDS:
        raise ValueError("route-semantics guild field inventory mismatch")
    if shape.get("guild_object_count") != 1:
        raise ValueError("route-semantics response must contain one guild object")
    if shape.get("guild_result_count") != 1:
        raise ValueError("route-semantics response must contain one guild result")
    if shape.get("distinct_non_null_id_count") != 1:
        raise ValueError("route-semantics response guild ID count mismatch")
    if shape.get("target_name_casefold_match_count") != 1:
        raise ValueError("route-semantics response target name match count mismatch")
    if shape.get("pagination_object_observed") is not False:
        raise ValueError("route-semantics response unexpectedly claims pagination")
    if shape.get("pagination_keys") != []:
        raise ValueError("route-semantics response pagination keys are not empty")
    if shape.get("pagination_field_types") != []:
        raise ValueError("route-semantics response pagination types are not empty")
    if shape.get("contains_source_scalar_values") is not False:
        raise ValueError("route-semantics shape summary contains source scalar values")

    return shape


def review_guild_route_semantics(
    *,
    capture_path: Path,
    full_crawl_contract_path: Path,
    public_access_diagnostic_path: Path,
    receipt_output_path: Path,
    expected_guild_label: str = "Argentum",
) -> dict[str, Any]:
    """Review bounded route and schema evidence without promoting full-crawl semantics."""
    capture, capture_body = _load_object(capture_path, "route-semantics capture")
    contract, contract_body = _load_object(
        full_crawl_contract_path,
        "full-crawl contract",
    )
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

    _validate_source_binding(
        source_path=full_crawl_contract_path,
        source_body=contract_body,
        expected_name=capture.get("source_contract_name"),
        expected_sha256=capture.get("source_contract_sha256"),
        label="full-crawl contract",
    )
    _validate_source_binding(
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

    summary = _required_object(capture.get("summary"), "capture.summary")
    if summary.get("all_integrity_checks_passed") is not True:
        raise ValueError("route-semantics capture integrity checks failed")
    if summary.get("all_responses_completed") is not True:
        raise ValueError("route-semantics capture responses are incomplete")
    if summary.get("attempt_count") != 3 or summary.get("completed_attempt_count") != 3:
        raise ValueError("route-semantics capture attempt counts mismatch")
    if summary.get("ready_for_route_semantics_review") is not True:
        raise ValueError("route-semantics capture is not ready for review")
    if summary.get("response_shape_consistent") is not True:
        raise ValueError("route-semantics response shape is inconsistent")
    if summary.get("contains_raw_payload") is not False:
        raise ValueError("route-semantics capture contains raw payload")
    if summary.get("contains_source_scalar_values") is not False:
        raise ValueError("route-semantics capture contains source scalar values")
    if summary.get("guild_api_route_semantics_verified") is not False:
        raise ValueError("route-semantics capture already claims semantic verification")
    if summary.get("ready_for_full_guild_crawl") is not False:
        raise ValueError("route-semantics capture already claims full-crawl readiness")
    if summary.get("planner_scoring_allowed") is not False:
        raise ValueError("route-semantics capture already enables planner scoring")

    request_contract = _required_object(
        capture.get("request_contract"),
        "capture.request_contract",
    )
    if request_contract.get("case_count") != 3:
        raise ValueError("route-semantics request case count mismatch")
    if request_contract.get("route_template") != _ROUTE_TEMPLATE:
        raise ValueError("route-semantics request route template mismatch")
    if request_contract.get("selected_profile") != _SELECTED_PROFILE:
        raise ValueError("route-semantics request profile mismatch")
    if request_contract.get("observed_query_shapes") != [["q", "limit"], ["q"]]:
        raise ValueError("route-semantics request query shapes mismatch")
    if request_contract.get("credentials_supplied") is not False:
        raise ValueError("route-semantics request supplied credentials")
    if request_contract.get("redirects_allowed") is not False:
        raise ValueError("route-semantics request allowed redirects")

    attempts = _attempts_by_case(capture)
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
        _required_sha256(
            shape.get("guild_field_inventory_sha256"),
            "shape.guild_field_inventory_sha256",
        )
        for shape in shapes.values()
    }
    ordered_record_hashes = {
        _required_sha256(
            shape.get("ordered_guild_records_sha256"),
            "shape.ordered_guild_records_sha256",
        )
        for shape in shapes.values()
    }
    id_set_hashes = {
        _required_sha256(
            shape.get("id_value_set_sha256"),
            "shape.id_value_set_sha256",
        )
        for shape in shapes.values()
    }
    result_counts = {int(shape["guild_result_count"]) for shape in shapes.values()}

    cross_case = _required_object(
        capture.get("cross_case_review"),
        "capture.cross_case_review",
    )
    required_true = (
        "all_responses_completed",
        "guild_collection_observed_on_all_cases",
        "limit_parameter_accepted",
        "response_shape_consistent",
        "route_shapes_observed",
        "source_id_set_stable_by_hash",
        "target_name_casefold_match_stable",
    )
    for field_name in required_true:
        if cross_case.get(field_name) is not True:
            raise ValueError(f"route-semantics cross-case evidence mismatch: {field_name}")
    for field_name in (
        "contains_source_scalar_values",
        "limit_truncation_semantics_verified",
        "pagination_object_observed",
        "pagination_semantics_verified",
    ):
        if cross_case.get(field_name) is not False:
            raise ValueError(f"route-semantics cross-case boundary mismatch: {field_name}")

    checks = {
        "full_crawl_contract_verified": True,
        "public_access_diagnostic_verified": True,
        "capture_source_bindings_verified": True,
        "capture_integrity_checks_verified": True,
        "capture_privacy_boundary_verified": True,
        "request_case_set_verified": set(attempts) == set(_EXPECTED_CASES),
        "route_template_verified": all(
            attempt.get("route_template") == _ROUTE_TEMPLATE
            for attempt in attempts.values()
        ),
        "query_shapes_verified": True,
        "all_three_responses_completed": True,
        "response_envelope_verified": all(
            shape.get("top_level_keys") == _EXPECTED_TOP_LEVEL_KEYS
            for shape in shapes.values()
        ),
        "guild_record_schema_verified": all(
            shape.get("guild_field_inventory") == _EXPECTED_GUILD_FIELDS
            for shape in shapes.values()
        ),
        "payload_hash_stable": len(payload_hashes) == 1,
        "schema_fingerprint_stable": len(schema_fingerprints) == 1,
        "field_inventory_stable": len(field_inventory_hashes) == 1,
        "ordered_record_set_stable": len(ordered_record_hashes) == 1,
        "source_id_set_stable_by_hash": len(id_set_hashes) == 1,
        "target_name_casefold_match_stable": all(
            shape.get("target_name_casefold_match_count") == 1
            for shape in shapes.values()
        ),
        "single_result_observed_in_all_cases": result_counts == {1},
        "limit_truncation_not_overclaimed": True,
        "pagination_not_overclaimed": True,
        "full_crawl_remains_disabled": True,
        "planner_scoring_remains_disabled": True,
    }

    route_shape_and_schema_reviewed = all(
        checks[field_name]
        for field_name in (
            "route_template_verified",
            "query_shapes_verified",
            "all_three_responses_completed",
            "response_envelope_verified",
            "guild_record_schema_verified",
            "payload_hash_stable",
            "schema_fingerprint_stable",
            "field_inventory_stable",
            "ordered_record_set_stable",
            "source_id_set_stable_by_hash",
            "target_name_casefold_match_stable",
        )
    )

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
