from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

_CONTRACT_VERSION = "guild-full-crawl-contract-v1"
_PUBLIC_MANIFEST_KIND = "public_report_manifest_capture"
_PUBLIC_MANIFEST_VERSION = "public-report-manifest-v1"
_IDENTITY_KIND = "guild_identity_decision"
_IDENTITY_VERSION = "guild-identity-decision-v1"
_GUILD_MANIFEST_KIND = "verified_guild_report_manifest"
_GUILD_MANIFEST_VERSION = "verified-guild-report-manifest-v1"


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _load_object(path: Path, label: str) -> tuple[dict[str, Any], bytes]:
    body = path.read_bytes()
    payload = json.loads(body)
    if not isinstance(payload, dict):
        raise ValueError(f"{label} must contain a JSON object")
    return payload, body


def _required_object(value: object, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    return value


def _required_integer(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{label} must be an integer")
    return value


def _validate_public_manifest(
    receipt: Mapping[str, Any],
    *,
    expected_guild_label: str,
) -> int:
    if receipt.get("schema_version") != 1:
        raise ValueError("public manifest schema mismatch")
    if receipt.get("manifest_kind") != _PUBLIC_MANIFEST_KIND:
        raise ValueError("public manifest kind mismatch")
    if receipt.get("manifest_version") != _PUBLIC_MANIFEST_VERSION:
        raise ValueError("public manifest version mismatch")

    target = _required_object(receipt.get("target"), "public manifest target")
    if target.get("guild_label") != expected_guild_label:
        raise ValueError("public manifest guild label mismatch")

    summary = _required_object(receipt.get("summary"), "public manifest summary")
    if summary.get("all_integrity_checks_passed") is not True:
        raise ValueError("public manifest integrity checks failed")
    if summary.get("contains_source_scalar_values") is not False:
        raise ValueError("public manifest contains source scalar values")
    report_count = _required_integer(
        summary.get("report_occurrence_count"),
        "public manifest report count",
    )
    if summary.get("unique_report_id_count") != report_count:
        raise ValueError("public manifest report IDs are not unique")
    if summary.get("duplicate_report_occurrence_count") != 0:
        raise ValueError("public manifest contains duplicate report occurrences")

    boundary = _required_object(
        receipt.get("decision_boundary"),
        "public manifest decision boundary",
    )
    if boundary.get("manifest_page_range_completed") is not True:
        raise ValueError("public manifest page range is incomplete")
    if boundary.get("ready_for_full_guild_crawl") is not False:
        raise ValueError("public manifest enables full guild crawl")
    if boundary.get("planner_scoring_allowed") is not False:
        raise ValueError("public manifest enables planner scoring")
    return report_count


def _validate_identity_decision(
    receipt: Mapping[str, Any],
    *,
    receipt_body: bytes,
    public_manifest_body: bytes,
    expected_guild_label: str,
) -> None:
    if receipt.get("schema_version") != 1:
        raise ValueError("identity decision schema mismatch")
    if receipt.get("decision_kind") != _IDENTITY_KIND:
        raise ValueError("identity decision kind mismatch")
    if receipt.get("decision_version") != _IDENTITY_VERSION:
        raise ValueError("identity decision version mismatch")
    if receipt.get("source_public_manifest_sha256") != _sha256_bytes(public_manifest_body):
        raise ValueError("identity decision public manifest SHA-256 mismatch")

    target = _required_object(receipt.get("target"), "identity decision target")
    if target.get("guild_label") != expected_guild_label:
        raise ValueError("identity decision guild label mismatch")
    if target.get("source_guild_id_published") is not False:
        raise ValueError("identity decision publishes source guild ID")

    summary = _required_object(receipt.get("summary"), "identity decision summary")
    if summary.get("all_integrity_checks_passed") is not True:
        raise ValueError("identity decision integrity checks failed")
    if summary.get("guild_identity_verified") is not True:
        raise ValueError("guild identity is not verified")
    if summary.get("ready_for_guild_filtering") is not True:
        raise ValueError("identity decision does not allow guild filtering")
    if summary.get("contains_source_scalar_values") is not False:
        raise ValueError("identity decision contains source scalar values")

    boundary = _required_object(
        receipt.get("decision_boundary"),
        "identity decision boundary",
    )
    if boundary.get("guild_api_route_semantics_verified") is not False:
        raise ValueError("identity decision overclaims guild API route semantics")
    if boundary.get("ready_for_full_guild_crawl") is not False:
        raise ValueError("identity decision enables full guild crawl")
    if boundary.get("planner_scoring_allowed") is not False:
        raise ValueError("identity decision enables planner scoring")

    if len(receipt_body) == 0:
        raise ValueError("identity decision body is empty")


def _validate_guild_manifest(
    receipt: Mapping[str, Any],
    *,
    public_manifest_body: bytes,
    identity_decision_body: bytes,
    expected_guild_label: str,
    expected_source_report_count: int,
) -> int:
    if receipt.get("schema_version") != 1:
        raise ValueError("guild report manifest schema mismatch")
    if receipt.get("manifest_kind") != _GUILD_MANIFEST_KIND:
        raise ValueError("guild report manifest kind mismatch")
    if receipt.get("manifest_version") != _GUILD_MANIFEST_VERSION:
        raise ValueError("guild report manifest version mismatch")
    if receipt.get("source_public_manifest_sha256") != _sha256_bytes(public_manifest_body):
        raise ValueError("guild report manifest public manifest SHA-256 mismatch")
    if receipt.get("source_public_identity_decision_sha256") != _sha256_bytes(
        identity_decision_body
    ):
        raise ValueError("guild report manifest identity decision SHA-256 mismatch")

    target = _required_object(receipt.get("target"), "guild report manifest target")
    if target.get("guild_label") != expected_guild_label:
        raise ValueError("guild report manifest label mismatch")
    for field_name in (
        "raw_report_records_published",
        "report_ids_published",
        "source_guild_id_published",
    ):
        if target.get(field_name) is not False:
            raise ValueError(f"guild report manifest privacy boundary mismatch: {field_name}")

    summary = _required_object(receipt.get("summary"), "guild report manifest summary")
    if summary.get("all_integrity_checks_passed") is not True:
        raise ValueError("guild report manifest integrity checks failed")
    if summary.get("guild_identity_verified") is not True:
        raise ValueError("guild report manifest identity boundary mismatch")
    if summary.get("guild_filtering_completed") is not True:
        raise ValueError("guild report filtering is incomplete")
    if summary.get("contains_source_scalar_values") is not False:
        raise ValueError("guild report manifest contains source scalar values")
    if summary.get("source_report_count") != expected_source_report_count:
        raise ValueError("guild report manifest source count mismatch")
    selected_count = _required_integer(
        summary.get("selected_report_count"),
        "guild report manifest selected count",
    )
    if summary.get("unique_selected_report_id_count") != selected_count:
        raise ValueError("guild report manifest selected IDs are not unique")
    if summary.get("duplicate_selected_report_occurrence_count") != 0:
        raise ValueError("guild report manifest contains duplicate selections")

    boundary = _required_object(
        receipt.get("decision_boundary"),
        "guild report manifest decision boundary",
    )
    if boundary.get("guild_report_manifest_deduplicated") is not True:
        raise ValueError("guild report manifest is not deduplicated")
    if boundary.get("full_crawl_collection_contract_reviewed") is not False:
        raise ValueError("guild report manifest overclaims contract review")
    if boundary.get("guild_api_route_semantics_verified") is not False:
        raise ValueError("guild report manifest overclaims route semantics")
    if boundary.get("ready_for_full_guild_crawl") is not False:
        raise ValueError("guild report manifest enables full guild crawl")
    if boundary.get("planner_scoring_allowed") is not False:
        raise ValueError("guild report manifest enables planner scoring")
    return selected_count


def build_guild_full_crawl_contract(
    public_manifest_path: Path,
    identity_decision_path: Path,
    guild_manifest_path: Path,
    *,
    expected_guild_label: str = "Argentum",
) -> dict[str, Any]:
    """Review the pre-crawl evidence boundary without enabling a full guild crawl."""
    public_manifest, public_manifest_body = _load_object(
        public_manifest_path,
        "public report manifest",
    )
    identity_decision, identity_decision_body = _load_object(
        identity_decision_path,
        "guild identity decision",
    )
    guild_manifest, guild_manifest_body = _load_object(
        guild_manifest_path,
        "verified guild report manifest",
    )

    source_report_count = _validate_public_manifest(
        public_manifest,
        expected_guild_label=expected_guild_label,
    )
    _validate_identity_decision(
        identity_decision,
        receipt_body=identity_decision_body,
        public_manifest_body=public_manifest_body,
        expected_guild_label=expected_guild_label,
    )
    selected_report_count = _validate_guild_manifest(
        guild_manifest,
        public_manifest_body=public_manifest_body,
        identity_decision_body=identity_decision_body,
        expected_guild_label=expected_guild_label,
        expected_source_report_count=source_report_count,
    )

    checks = {
        "public_manifest_verified": True,
        "public_manifest_report_ids_unique": True,
        "identity_decision_verified": True,
        "identity_decision_public_manifest_sha256_verified": True,
        "guild_manifest_verified": True,
        "guild_manifest_public_manifest_sha256_verified": True,
        "guild_manifest_identity_decision_sha256_verified": True,
        "guild_manifest_selected_report_ids_unique": True,
        "guild_manifest_privacy_boundary_verified": True,
        "full_crawl_remains_disabled": True,
        "route_semantics_remain_unverified": True,
        "planner_scoring_remains_disabled": True,
    }

    return {
        "schema_version": 1,
        "contract_kind": "guild_full_crawl_collection_contract",
        "contract_version": _CONTRACT_VERSION,
        "source_public_manifest_name": public_manifest_path.name,
        "source_public_manifest_sha256": _sha256_bytes(public_manifest_body),
        "source_identity_decision_name": identity_decision_path.name,
        "source_identity_decision_sha256": _sha256_bytes(identity_decision_body),
        "source_guild_manifest_name": guild_manifest_path.name,
        "source_guild_manifest_sha256": _sha256_bytes(guild_manifest_body),
        "target": {
            "guild_label": expected_guild_label,
            "source_guild_id_published": False,
            "report_ids_published": False,
        },
        "verified_baseline": {
            "source_public_report_count": source_report_count,
            "selected_guild_report_count": selected_report_count,
            "selected_report_ids_unique": True,
            "selection_source": "verified_public_manifest_filter",
            "selection_order": "source_manifest_order",
        },
        "route_semantics_requirements": [
            "verify_exact_route_template_and_query_parameters",
            "archive_complete_raw_response_before_interpretation",
            "bind_response_to_exact_payload_sha256_and_schema_fingerprint",
            "review_response_field_types_nullability_and_collection_shape",
            "verify_pagination_offset_limit_and_page_relations_if_present",
            "verify_deterministic_termination_and_successor_behavior",
            "verify_completeness_boundary_and_capture_time_scope",
            "publish_explicit_scalar_free_route_semantics_decision",
        ],
        "set_comparison_contract": {
            "baseline": "verified_public_manifest_filter",
            "candidate": "future_guild_api_report_set",
            "deduplication_key": "source_report_id",
            "required_partitions": [
                "matching_reports",
                "missing_from_guild_api",
                "extra_in_guild_api",
                "conflicting_report_records",
            ],
            "contradicting_evidence_preserved": True,
            "report_ids_published": False,
        },
        "capture_failure_contract": {
            "partial_results_must_not_be_marked_complete": True,
            "failed_requests_preserved_as_observations": True,
            "resume_requires_exact_contract_and_checkpoint_binding": True,
            "automatic_retry_must_be_bounded": True,
        },
        "integrity_checks": checks,
        "decision_boundary": {
            "status": "full_crawl_collection_contract_reviewed",
            "guild_identity_verified": True,
            "guild_filtering_completed": True,
            "guild_report_manifest_deduplicated": True,
            "full_crawl_collection_contract_reviewed": True,
            "ready_for_bounded_route_semantics_capture": True,
            "guild_api_route_semantics_verified": False,
            "automatic_full_guild_crawl_allowed": False,
            "ready_for_full_guild_crawl": False,
            "ready_for_multi_report_character_graph": False,
            "ready_for_performance_model": False,
            "ready_for_bis25_scoring": False,
            "planner_scoring_allowed": False,
        },
        "summary": {
            "all_integrity_checks_passed": all(checks.values()),
            "integrity_check_count": len(checks),
            "source_public_report_count": source_report_count,
            "selected_guild_report_count": selected_report_count,
            "full_crawl_collection_contract_reviewed": True,
            "ready_for_bounded_route_semantics_capture": True,
            "guild_api_route_semantics_verified": False,
            "ready_for_full_guild_crawl": False,
            "contains_source_scalar_values": False,
            "planner_scoring_allowed": False,
        },
    }


__all__ = ["build_guild_full_crawl_contract"]
