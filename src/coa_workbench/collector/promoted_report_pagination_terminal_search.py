from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from . import report_pagination_terminal_search as _implementation
from .raw_archive import RawArchive
from .report_discovery import REPORT_DISCOVERY_PROMOTED_LIMIT
from .source_registry import SourceRegistry

_PROMOTION_KIND = "report_pagination_limit_promotion"
_PROMOTION_VERSION = "report-pagination-limit-promotion-v1"
_PROBE_KIND = "report_pagination_limit_probe"
_PROBE_VERSION = "report-pagination-limit-probe-v1"
_PRIVATE_PROBE_KIND = "report_pagination_limit_probe_private_batch"
_SEARCH_VERSION = "report-pagination-terminal-search-v2"


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _load_object(path: Path, label: str) -> tuple[dict[str, Any], bytes]:
    body = path.read_bytes()
    payload = json.loads(body)
    if not isinstance(payload, dict):
        raise ValueError(f"{label} must contain a JSON object")
    return payload, body


def _required_object(value: object, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"promoted terminal search field {field_name} must be an object")
    return value


def _required_list(value: object, field_name: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"promoted terminal search field {field_name} must be an array")
    return value


def _required_integer(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"promoted terminal search field {field_name} must be an integer")
    return value


def _write_json(path: Path, payload: object) -> bytes:
    body = (json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(body)
    temporary.replace(path)
    return body


def _find_candidate(payload: Mapping[str, Any], field_name: str) -> dict[str, Any]:
    for row in _required_list(payload.get("candidates"), field_name):
        candidate = _required_object(row, f"{field_name}[]")
        if candidate.get("requested_limit") == REPORT_DISCOVERY_PROMOTED_LIMIT:
            return candidate
    raise ValueError("report limit evidence is missing candidate 25")


def _validate_inputs(
    promotion: Mapping[str, Any],
    promotion_body: bytes,
    probe: Mapping[str, Any],
    probe_body: bytes,
    private_probe: Mapping[str, Any],
    private_probe_body: bytes,
    expected_guild_label: str,
) -> tuple[int, int, int]:
    expected_promotion = {
        "schema_version": 1,
        "promotion_kind": _PROMOTION_KIND,
        "promotion_version": _PROMOTION_VERSION,
        "selected_limit": REPORT_DISCOVERY_PROMOTED_LIMIT,
    }
    for field_name, expected in expected_promotion.items():
        if promotion.get(field_name) != expected:
            raise ValueError(f"report limit promotion mismatch: {field_name}")

    checks = _required_object(promotion.get("integrity_checks"), "promotion.integrity_checks")
    if not checks or any(value is not True for value in checks.values()):
        raise ValueError("report limit promotion integrity checks are incomplete")
    boundary = _required_object(promotion.get("decision_boundary"), "promotion.decision_boundary")
    if boundary.get("status") != "limit_25_manually_promoted_for_terminal_search":
        raise ValueError("report limit promotion status mismatch")
    if boundary.get("ready_for_limit_25_terminal_search") is not True:
        raise ValueError("report limit promotion does not permit terminal search")
    if boundary.get("ready_for_fast_manifest_capture") is not False:
        raise ValueError("report limit promotion prematurely enables fast manifest capture")

    if _sha256_bytes(probe_body) != promotion.get("source_probe_sha256"):
        raise ValueError("report limit probe hash does not match manual promotion")
    if probe.get("schema_version") != 1 or probe.get("probe_kind") != _PROBE_KIND:
        raise ValueError("report limit probe root contract mismatch")
    if probe.get("probe_version") != _PROBE_VERSION:
        raise ValueError("report limit probe version mismatch")
    target = _required_object(probe.get("target"), "probe.target")
    if target.get("guild_label") != expected_guild_label:
        raise ValueError("report limit probe guild label mismatch")
    if target.get("guild_identity_status") != "operator_named_target_unresolved":
        raise ValueError("guild identity was unexpectedly resolved during limit probe")
    probe_candidate = _find_candidate(probe, "probe.candidates")
    if probe_candidate.get("observed_supported") is not True:
        raise ValueError("report limit probe candidate 25 is not supported")
    probe_checks = _required_object(probe_candidate.get("checks"), "probe.candidate.checks")
    if not probe_checks or any(value is not True for value in probe_checks.values()):
        raise ValueError("report limit probe candidate 25 checks are incomplete")
    probe_pages = [
        _required_object(row, "probe.candidate.pages[]")
        for row in _required_list(probe_candidate.get("pages"), "probe.candidate.pages")
    ]
    if [row.get("page") for row in probe_pages] != [1, 2]:
        raise ValueError("report limit probe candidate 25 page set mismatch")
    if any(row.get("report_occurrence_count") != 25 for row in probe_pages):
        raise ValueError("report limit probe candidate 25 pages are not full")

    expected_private_hash = promotion.get("source_private_probe_sha256")
    if _sha256_bytes(private_probe_body) != expected_private_hash:
        raise ValueError("private report limit probe hash does not match manual promotion")
    if probe.get("source_private_probe_sha256") != expected_private_hash:
        raise ValueError("public and private report limit probe hashes disagree")
    if private_probe.get("schema_version") != 1:
        raise ValueError("private report limit probe schema mismatch")
    if private_probe.get("probe_kind") != _PRIVATE_PROBE_KIND:
        raise ValueError("private report limit probe kind mismatch")
    if private_probe.get("probe_version") != _PROBE_VERSION:
        raise ValueError("private report limit probe version mismatch")
    if private_probe.get("target_guild_label") != expected_guild_label:
        raise ValueError("private report limit probe guild label mismatch")
    private_candidate = _find_candidate(private_probe, "private_probe.candidates")
    if private_candidate.get("observed_supported") is not True:
        raise ValueError("private report limit probe candidate 25 is not supported")
    private_checks = _required_object(
        private_candidate.get("checks"), "private_probe.candidate.checks"
    )
    if not private_checks or any(value is not True for value in private_checks.values()):
        raise ValueError("private report limit probe candidate 25 checks are incomplete")
    private_pages = [
        _required_object(row, "private_probe.candidate.pages[]")
        for row in _required_list(private_candidate.get("pages"), "private_probe.candidate.pages")
    ]
    if [row.get("page") for row in private_pages] != [1, 2]:
        raise ValueError("private report limit probe candidate 25 page set mismatch")
    for expected_page, row in zip((1, 2), private_pages, strict=True):
        pagination = _required_object(row.get("pagination"), "private_probe.pagination")
        if pagination.get("page") != expected_page or pagination.get("limit") != 25:
            raise ValueError("private report limit probe page or limit relation failed")
        if pagination.get("offset") != (expected_page - 1) * 25:
            raise ValueError("private report limit probe offset relation failed")
        if pagination.get("hasPrevious") is not (expected_page > 1):
            raise ValueError("private report limit probe hasPrevious relation failed")
        if pagination.get("hasMore") is not True:
            raise ValueError("private report limit probe does not establish a lower bound")
        report_ids = _required_list(row.get("source_report_ids"), "source_report_ids")
        if len(report_ids) != 25 or len(set(report_ids)) != 25:
            raise ValueError("private report limit probe candidate page is not full and unique")

    search = _required_object(promotion.get("search_contract"), "promotion.search_contract")
    lower = _required_integer(search.get("initial_lower_page"), "initial_lower_page")
    upper = _required_integer(
        search.get("fallback_initial_upper_page"), "fallback_initial_upper_page"
    )
    request_budget = _required_integer(
        search.get("maximum_request_count"), "maximum_request_count"
    )
    if lower != 2 or upper != 8192 or request_budget != 20:
        raise ValueError("report limit promotion search contract mismatch")
    if expected_guild_label != "Argentum":
        raise ValueError("report limit promotion is bound to the Argentum operator label")
    if not promotion_body:
        raise ValueError("report limit promotion body is empty")
    return lower, upper, request_budget


def _rewrite_outputs(
    *,
    promotion_path: Path,
    promotion_body: bytes,
    probe_receipt_path: Path,
    probe_body: bytes,
    probe_private_path: Path,
    probe_private_body: bytes,
    private_output_path: Path,
    receipt_output_path: Path,
) -> dict[str, Any]:
    private_payload, _ = _load_object(private_output_path, "promoted private terminal search")
    receipt, _ = _load_object(receipt_output_path, "promoted terminal search receipt")

    for payload in (private_payload, receipt):
        payload.pop("source_boundary_receipt_name", None)
        payload.pop("source_boundary_receipt_sha256", None)
        payload.pop("source_boundary_private_name", None)
        payload.pop("source_boundary_private_sha256", None)
        payload["source_limit_promotion_name"] = promotion_path.name
        payload["source_limit_promotion_sha256"] = _sha256_bytes(promotion_body)
        payload["source_limit_probe_name"] = probe_receipt_path.name
        payload["source_limit_probe_sha256"] = _sha256_bytes(probe_body)
        payload["source_limit_probe_private_name"] = probe_private_path.name
        payload["source_limit_probe_private_sha256"] = _sha256_bytes(probe_private_body)

    private_body = _write_json(private_output_path, private_payload)
    receipt["source_private_search_sha256"] = _sha256_bytes(private_body)
    checks = _required_object(receipt.get("integrity_checks"), "receipt.integrity_checks")
    checks.pop("boundary_receipt_verified", None)
    checks.pop("boundary_private_sha256_verified", None)
    checks.update(
        {
            "limit_promotion_verified": True,
            "limit_probe_receipt_sha256_verified": True,
            "limit_probe_private_sha256_verified": True,
            "promoted_limit_25_verified": True,
        }
    )
    decision = _required_object(receipt.get("decision_boundary"), "receipt.decision_boundary")
    decision["status"] = "promoted_limit_pagination_terminal_contract_verified"
    decision["promoted_limit_verified"] = True
    summary = _required_object(receipt.get("summary"), "receipt.summary")
    summary["promoted_limit"] = REPORT_DISCOVERY_PROMOTED_LIMIT
    summary["integrity_check_count"] = len(checks)
    _write_json(receipt_output_path, receipt)
    return receipt


def capture_promoted_report_pagination_terminal_search(
    registry: SourceRegistry,
    archive: RawArchive,
    *,
    promotion_path: Path,
    probe_receipt_path: Path,
    probe_private_path: Path,
    private_output_path: Path,
    receipt_output_path: Path,
    expected_guild_label: str = "Argentum",
    max_requests: int = 20,
    timeout_seconds: float = 20.0,
    retry_count: int = 1,
    opener: Any | None = None,
) -> dict[str, Any]:
    """Run terminal search under the manually promoted limit-25 contract."""
    promotion, promotion_body = _load_object(promotion_path, "report limit promotion")
    probe, probe_body = _load_object(probe_receipt_path, "report limit probe")
    private_probe, private_probe_body = _load_object(
        probe_private_path, "private report limit probe"
    )
    lower, upper, promoted_budget = _validate_inputs(
        promotion,
        promotion_body,
        probe,
        probe_body,
        private_probe,
        private_probe_body,
        expected_guild_label,
    )
    if max_requests != promoted_budget:
        raise ValueError("terminal search request budget does not match manual promotion")

    previous_version = _implementation._SEARCH_VERSION
    previous_boundary_validator = _implementation._validate_boundary_receipt
    previous_private_validator = _implementation._validate_boundary_private
    previous_capture = _implementation.capture_public_report_discovery

    def validate_boundary(_receipt: Mapping[str, Any], _label: str) -> tuple[int, int, int]:
        return lower, upper, REPORT_DISCOVERY_PROMOTED_LIMIT

    def validate_private(*_args: Any, **_kwargs: Any) -> None:
        return None

    def capture_with_promoted_limit(*args: Any, **kwargs: Any):
        kwargs["allow_promoted_limit"] = True
        return previous_capture(*args, **kwargs)

    _implementation._SEARCH_VERSION = _SEARCH_VERSION
    _implementation._validate_boundary_receipt = validate_boundary
    _implementation._validate_boundary_private = validate_private
    _implementation.capture_public_report_discovery = capture_with_promoted_limit
    try:
        _implementation.capture_report_pagination_terminal_search(
            registry,
            archive,
            boundary_receipt_path=promotion_path,
            boundary_private_path=probe_private_path,
            private_output_path=private_output_path,
            receipt_output_path=receipt_output_path,
            expected_guild_label=expected_guild_label,
            max_requests=max_requests,
            timeout_seconds=timeout_seconds,
            retry_count=retry_count,
            opener=opener,
        )
    finally:
        _implementation._SEARCH_VERSION = previous_version
        _implementation._validate_boundary_receipt = previous_boundary_validator
        _implementation._validate_boundary_private = previous_private_validator
        _implementation.capture_public_report_discovery = previous_capture

    return _rewrite_outputs(
        promotion_path=promotion_path,
        promotion_body=promotion_body,
        probe_receipt_path=probe_receipt_path,
        probe_body=probe_body,
        probe_private_path=probe_private_path,
        probe_private_body=private_probe_body,
        private_output_path=private_output_path,
        receipt_output_path=receipt_output_path,
    )


__all__ = ["capture_promoted_report_pagination_terminal_search"]
