from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from . import public_report_manifest as _implementation
from .report_discovery import REPORT_DISCOVERY_PROMOTED_LIMIT

TERMINAL_PRIVATE_SEARCH_KIND = "report_pagination_terminal_search_private_batch"
_PROMOTED_TERMINAL_VERSION = "report-pagination-terminal-search-v2"


def _required_object(value: object, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"promoted manifest terminal field {field_name} must be an object")
    return value


def _required_list(value: object, field_name: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"promoted manifest terminal field {field_name} must be an array")
    return value


def _required_integer(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"promoted manifest terminal field {field_name} must be an integer")
    return value


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _validate_promoted_terminal_receipt(
    receipt: Mapping[str, Any], expected_guild_label: str
) -> tuple[int, int, int]:
    expected_root = {
        "schema_version": 1,
        "search_kind": "report_pagination_terminal_search",
        "search_version": _PROMOTED_TERMINAL_VERSION,
    }
    for field_name, expected in expected_root.items():
        if receipt.get(field_name) != expected:
            raise ValueError(f"promoted pagination terminal receipt mismatch: {field_name}")

    target = _required_object(receipt.get("target"), "target")
    if target.get("guild_label") != expected_guild_label:
        raise ValueError("promoted pagination terminal guild label mismatch")
    if target.get("guild_identity_status") != "operator_named_target_unresolved":
        raise ValueError("guild identity was unexpectedly resolved before manifest capture")

    request = _required_object(receipt.get("request"), "request")
    if request.get("route_template") != "/api/reports/public":
        raise ValueError("promoted pagination terminal route mismatch")
    if request.get("limit") != REPORT_DISCOVERY_PROMOTED_LIMIT:
        raise ValueError("promoted pagination terminal limit mismatch")
    if request.get("sort_by") != "created_at" or request.get("sort_order") != "desc":
        raise ValueError("promoted pagination terminal sorting mismatch")

    summary = _required_object(receipt.get("summary"), "summary")
    if summary.get("all_integrity_checks_passed") is not True:
        raise ValueError("promoted pagination terminal integrity summary failed")
    if summary.get("contains_source_scalar_values") is not False:
        raise ValueError("promoted pagination terminal receipt is not scalar-free")
    if summary.get("promoted_limit") != REPORT_DISCOVERY_PROMOTED_LIMIT:
        raise ValueError("promoted pagination terminal summary limit mismatch")
    if summary.get("ready_for_exhaustive_public_report_manifest_capture") is not True:
        raise ValueError("promoted pagination terminal is not ready for manifest capture")

    boundary = _required_object(receipt.get("decision_boundary"), "decision_boundary")
    if boundary.get("status") != "promoted_limit_pagination_terminal_contract_verified":
        raise ValueError("promoted pagination terminal status mismatch")
    required_true = (
        "page_semantics_verified",
        "page_size_semantics_verified",
        "promoted_limit_verified",
        "offset_semantics_verified",
        "has_previous_semantics_verified",
        "has_more_semantics_verified",
        "termination_condition_verified",
        "terminal_page_verified",
        "ready_for_exhaustive_public_report_manifest_capture",
    )
    if any(boundary.get(field_name) is not True for field_name in required_true):
        raise ValueError("promoted pagination terminal boundary checks are incomplete")
    if boundary.get("ready_for_guild_filtering") is not False:
        raise ValueError("promoted terminal receipt prematurely enables guild filtering")
    if boundary.get("planner_scoring_allowed") is not False:
        raise ValueError("promoted terminal receipt prematurely enables planner scoring")

    contract = _required_object(receipt.get("terminal_contract"), "terminal_contract")
    if contract.get("status") != "verified_adjacent_transition":
        raise ValueError("promoted pagination terminal transition is not verified")
    if contract.get("strategy") != "request_pages_1_through_terminal_page_inclusive":
        raise ValueError("promoted pagination terminal strategy mismatch")
    if contract.get("inclusive_terminal_page") is not True:
        raise ValueError("promoted pagination terminal page is not inclusive")
    if contract.get("deduplication_key") != "/reports/*/id":
        raise ValueError("promoted pagination terminal deduplication key mismatch")

    terminal_page = _required_integer(contract.get("terminal_page"), "terminal_page")
    terminal_count = _required_integer(
        contract.get("terminal_page_report_count"), "terminal_page_report_count"
    )
    successor_page = _required_integer(contract.get("successor_page"), "successor_page")
    if terminal_page < 2 or successor_page != terminal_page + 1:
        raise ValueError("promoted pagination terminal page relationship is invalid")
    if terminal_count < 1 or terminal_count > REPORT_DISCOVERY_PROMOTED_LIMIT:
        raise ValueError("promoted pagination terminal report count is invalid")
    if summary.get("terminal_page") != terminal_page:
        raise ValueError("promoted pagination terminal summary page mismatch")
    if summary.get("terminal_page_report_count") != terminal_count:
        raise ValueError("promoted pagination terminal summary count mismatch")

    for field_name in (
        "source_limit_promotion_sha256",
        "source_limit_probe_sha256",
        "source_limit_probe_private_sha256",
    ):
        value = receipt.get(field_name)
        if not isinstance(value, str) or len(value) != 64:
            raise ValueError(f"promoted pagination terminal missing {field_name}")
    return terminal_page, terminal_count, REPORT_DISCOVERY_PROMOTED_LIMIT


def _validate_promoted_terminal_private(
    private: Mapping[str, Any],
    private_body: bytes,
    receipt: Mapping[str, Any],
    expected_guild_label: str,
    terminal_page: int,
) -> None:
    if private.get("schema_version") != 1:
        raise ValueError("promoted private pagination terminal schema mismatch")
    if private.get("search_kind") != TERMINAL_PRIVATE_SEARCH_KIND:
        raise ValueError("promoted private pagination terminal kind mismatch")
    if private.get("search_version") != _PROMOTED_TERMINAL_VERSION:
        raise ValueError("promoted private pagination terminal version mismatch")
    if private.get("target_guild_label") != expected_guild_label:
        raise ValueError("promoted private pagination terminal guild label mismatch")
    if _sha256_bytes(private_body) != receipt.get("source_private_search_sha256"):
        raise ValueError("promoted private pagination terminal hash changed")

    for field_name in (
        "source_limit_promotion_sha256",
        "source_limit_probe_sha256",
        "source_limit_probe_private_sha256",
    ):
        if private.get(field_name) != receipt.get(field_name):
            raise ValueError(f"promoted private pagination terminal mismatch: {field_name}")

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
            raise ValueError(f"promoted private pagination terminal request mismatch: {field_name}")

    rows = [
        _required_object(item, "private.pages[]")
        for item in _required_list(private.get("pages"), "private.pages")
    ]
    phases = {(row.get("phase"), row.get("page")): row for row in rows}
    terminal_count = _required_integer(
        _required_object(receipt.get("summary"), "summary").get("terminal_page_report_count"),
        "terminal_page_report_count",
    )
    for phase, page, expected_has_more, expected_count in (
        ("final_predecessor", terminal_page - 1, True, REPORT_DISCOVERY_PROMOTED_LIMIT),
        ("final_terminal", terminal_page, False, terminal_count),
        ("final_successor", terminal_page + 1, False, 0),
    ):
        row = phases.get((phase, page))
        if row is None:
            raise ValueError(f"promoted private pagination terminal is missing {phase}")
        pagination = _required_object(row.get("pagination"), f"private.pages[{phase}].pagination")
        if pagination.get("page") != page:
            raise ValueError(f"promoted private terminal page relation failed in {phase}")
        if pagination.get("limit") != REPORT_DISCOVERY_PROMOTED_LIMIT:
            raise ValueError(f"promoted private terminal limit relation failed in {phase}")
        if pagination.get("offset") != (page - 1) * REPORT_DISCOVERY_PROMOTED_LIMIT:
            raise ValueError(f"promoted private terminal offset relation failed in {phase}")
        if pagination.get("hasMore") is not expected_has_more:
            raise ValueError(f"promoted private terminal hasMore relation failed in {phase}")
        report_ids = _required_list(row.get("source_report_ids"), "source_report_ids")
        if len(report_ids) != expected_count:
            raise ValueError(f"promoted private terminal report count changed in {phase}")


def capture_public_report_manifest(*args: Any, **kwargs: Any) -> dict[str, Any]:
    terminal_path = kwargs.get("terminal_receipt_path")
    version = None
    if isinstance(terminal_path, Path) and terminal_path.exists():
        payload = json.loads(terminal_path.read_bytes())
        if isinstance(payload, dict):
            version = payload.get("search_version")

    previous_kind = _implementation._TERMINAL_PRIVATE_KIND
    _implementation._TERMINAL_PRIVATE_KIND = TERMINAL_PRIVATE_SEARCH_KIND
    if version != _PROMOTED_TERMINAL_VERSION:
        try:
            return _implementation.capture_public_report_manifest(*args, **kwargs)
        finally:
            _implementation._TERMINAL_PRIVATE_KIND = previous_kind

    previous_version = _implementation._TERMINAL_VERSION
    previous_receipt_validator = _implementation._validate_terminal_receipt
    previous_private_validator = _implementation._validate_terminal_private
    previous_capture = _implementation.capture_public_report_discovery

    def capture_with_promoted_limit(*capture_args: Any, **capture_kwargs: Any):
        capture_kwargs["allow_promoted_limit"] = True
        return previous_capture(*capture_args, **capture_kwargs)

    _implementation._TERMINAL_VERSION = _PROMOTED_TERMINAL_VERSION
    _implementation._validate_terminal_receipt = _validate_promoted_terminal_receipt
    _implementation._validate_terminal_private = _validate_promoted_terminal_private
    _implementation.capture_public_report_discovery = capture_with_promoted_limit
    try:
        return _implementation.capture_public_report_manifest(*args, **kwargs)
    finally:
        _implementation._TERMINAL_PRIVATE_KIND = previous_kind
        _implementation._TERMINAL_VERSION = previous_version
        _implementation._validate_terminal_receipt = previous_receipt_validator
        _implementation._validate_terminal_private = previous_private_validator
        _implementation.capture_public_report_discovery = previous_capture


__all__ = ["TERMINAL_PRIVATE_SEARCH_KIND", "capture_public_report_manifest"]
