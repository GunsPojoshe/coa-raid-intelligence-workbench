from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from coa_workbench.collector.guild_identity_search_capture_review import (
    _load_object,
    _required_list,
    _required_object,
    _sha256_bytes,
    _write_json,
)

_FILTER_VERSION = "verified-guild-report-manifest-v1"
_PUBLIC_MANIFEST_KIND = "public_report_manifest_capture"
_PUBLIC_MANIFEST_VERSION = "public-report-manifest-v1"
_PRIVATE_MANIFEST_KIND = "public_report_manifest_private_batch"
_PUBLIC_DECISION_KIND = "guild_identity_decision"
_PRIVATE_DECISION_KIND = "guild_identity_decision_private"
_DECISION_VERSION = "guild-identity-decision-v1"


def _required_integer(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{label} must be an integer")
    return value


def _required_nonempty_string(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string")
    return value.strip()


def _identity_key(value: object) -> tuple[str, str]:
    if isinstance(value, bool) or not isinstance(value, (int, str)):
        raise ValueError("verified source guild ID must be an integer or string scalar")
    return type(value).__name__, str(value)


def _canonical_json(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _sha256_json(value: object) -> str:
    return hashlib.sha256(_canonical_json(value)).hexdigest()


def _validate_public_manifest(
    manifest: Mapping[str, Any],
    *,
    private_manifest_body: bytes,
    expected_guild_label: str,
) -> int:
    if manifest.get("schema_version") != 1:
        raise ValueError("public manifest schema mismatch")
    if manifest.get("manifest_kind") != _PUBLIC_MANIFEST_KIND:
        raise ValueError("public manifest kind mismatch")
    if manifest.get("manifest_version") != _PUBLIC_MANIFEST_VERSION:
        raise ValueError("public manifest version mismatch")

    target = _required_object(manifest.get("target"), "manifest.target")
    if target.get("guild_label") != expected_guild_label:
        raise ValueError("public manifest guild label mismatch")

    summary = _required_object(manifest.get("summary"), "manifest.summary")
    if summary.get("all_integrity_checks_passed") is not True:
        raise ValueError("public manifest integrity checks failed")
    if summary.get("contains_source_scalar_values") is not False:
        raise ValueError("public manifest contains source scalar values")
    if summary.get("ready_for_guild_identity_review") is not True:
        raise ValueError("public manifest identity-review boundary mismatch")

    expected_private_hash = _required_nonempty_string(
        manifest.get("source_private_manifest_sha256"),
        "public manifest private SHA-256",
    )
    if len(expected_private_hash) != 64:
        raise ValueError("public manifest private SHA-256 length mismatch")
    if _sha256_bytes(private_manifest_body) != expected_private_hash:
        raise ValueError("private manifest SHA-256 mismatch")

    return _required_integer(
        summary.get("report_occurrence_count"),
        "public manifest report occurrence count",
    )


def _validate_public_decision(
    decision: Mapping[str, Any],
    *,
    public_manifest_body: bytes,
    private_decision_body: bytes,
    expected_guild_label: str,
) -> None:
    if decision.get("schema_version") != 1:
        raise ValueError("public identity decision schema mismatch")
    if decision.get("decision_kind") != _PUBLIC_DECISION_KIND:
        raise ValueError("public identity decision kind mismatch")
    if decision.get("decision_version") != _DECISION_VERSION:
        raise ValueError("public identity decision version mismatch")

    target = _required_object(decision.get("target"), "decision.target")
    if target.get("guild_label") != expected_guild_label:
        raise ValueError("public identity decision guild label mismatch")
    if target.get("source_guild_id_published") is not False:
        raise ValueError("public identity decision publishes the source guild ID")
    if target.get("raw_payload_published") is not False:
        raise ValueError("public identity decision publishes a raw payload")

    promotion = _required_object(decision.get("promotion"), "decision.promotion")
    if promotion.get("explicit_operator_promotion") is not True:
        raise ValueError("public identity decision lacks explicit operator promotion")
    if promotion.get("promotion_mechanism") != "required_cli_flag":
        raise ValueError("public identity decision promotion mechanism mismatch")

    if decision.get("source_public_manifest_sha256") != _sha256_bytes(
        public_manifest_body
    ):
        raise ValueError("identity decision public-manifest SHA-256 mismatch")
    if decision.get("source_private_decision_sha256") != _sha256_bytes(
        private_decision_body
    ):
        raise ValueError("identity decision private-decision SHA-256 mismatch")

    checks = _required_object(decision.get("integrity_checks"), "decision.integrity_checks")
    if not checks or any(value is not True for value in checks.values()):
        raise ValueError("identity decision integrity checks are incomplete")

    summary = _required_object(decision.get("summary"), "decision.summary")
    expected_summary = {
        "all_integrity_checks_passed": True,
        "independent_source_identity_verified": True,
        "guild_identity_verified": True,
        "ready_for_guild_filtering": True,
        "contains_raw_payload": False,
        "contains_source_scalar_values": False,
    }
    for field_name, expected in expected_summary.items():
        if summary.get(field_name) is not expected:
            raise ValueError(f"identity decision summary mismatch: {field_name}")

    boundary = _required_object(decision.get("decision_boundary"), "decision.boundary")
    expected_boundary = {
        "status": "guild_identity_verified",
        "independent_source_identity_verified": True,
        "guild_identity_verified": True,
        "ready_for_guild_filtering": True,
        "guild_api_route_semantics_verified": False,
        "ready_for_full_guild_crawl": False,
        "ready_for_multi_report_character_graph": False,
        "ready_for_performance_model": False,
        "ready_for_bis25_scoring": False,
        "planner_scoring_allowed": False,
    }
    for field_name, expected in expected_boundary.items():
        if boundary.get(field_name) != expected:
            raise ValueError(f"identity decision boundary mismatch: {field_name}")


def _validate_private_decision(
    decision: Mapping[str, Any],
    *,
    public_decision: Mapping[str, Any],
    public_manifest_body: bytes,
    private_manifest_body: bytes,
    expected_guild_label: str,
) -> object:
    if decision.get("schema_version") != 1:
        raise ValueError("private identity decision schema mismatch")
    if decision.get("decision_kind") != _PRIVATE_DECISION_KIND:
        raise ValueError("private identity decision kind mismatch")
    if decision.get("decision_version") != _DECISION_VERSION:
        raise ValueError("private identity decision version mismatch")
    if decision.get("target_guild_label") != expected_guild_label:
        raise ValueError("private identity decision guild label mismatch")
    if decision.get("explicit_operator_promotion") is not True:
        raise ValueError("private identity decision lacks explicit operator promotion")
    if decision.get("guild_identity_verified") is not True:
        raise ValueError("private identity decision did not verify identity")

    if decision.get("source_public_manifest_sha256") != _sha256_bytes(
        public_manifest_body
    ):
        raise ValueError("private identity decision public-manifest SHA-256 mismatch")
    if decision.get("source_private_manifest_sha256") != _sha256_bytes(
        private_manifest_body
    ):
        raise ValueError("private identity decision private-manifest SHA-256 mismatch")

    for field_name in (
        "source_public_snapshot_review_sha256",
        "source_public_mapping_review_sha256",
    ):
        if public_decision.get(field_name) != decision.get(field_name):
            raise ValueError(f"public/private identity decision mismatch: {field_name}")

    checks = _required_object(
        decision.get("integrity_checks"),
        "private_decision.integrity_checks",
    )
    if not checks or any(value is not True for value in checks.values()):
        raise ValueError("private identity decision integrity checks are incomplete")

    candidate_source_guild_id = decision.get("candidate_source_guild_id")
    _identity_key(candidate_source_guild_id)
    return candidate_source_guild_id


def _filter_private_manifest(
    manifest: Mapping[str, Any],
    *,
    expected_report_count: int,
    expected_guild_label: str,
    verified_source_guild_id: object,
    private_decision: Mapping[str, Any],
) -> list[dict[str, Any]]:
    if manifest.get("schema_version") != 1:
        raise ValueError("private manifest schema mismatch")
    if manifest.get("manifest_kind") != _PRIVATE_MANIFEST_KIND:
        raise ValueError("private manifest kind mismatch")
    if manifest.get("manifest_version") != _PUBLIC_MANIFEST_VERSION:
        raise ValueError("private manifest version mismatch")
    if manifest.get("target_guild_label") != expected_guild_label:
        raise ValueError("private manifest guild label mismatch")

    summary = _required_object(manifest.get("summary"), "private_manifest.summary")
    if summary.get("contains_source_scalar_values") is not True:
        raise ValueError("private manifest scalar boundary mismatch")
    if summary.get("report_count") != expected_report_count:
        raise ValueError("private manifest report count mismatch")

    reports = [
        _required_object(value, "private_manifest.reports[]")
        for value in _required_list(manifest.get("reports"), "private_manifest.reports")
    ]
    if len(reports) != expected_report_count:
        raise ValueError("private manifest reports array count mismatch")

    report_ids = [
        _required_integer(report.get("id"), "private report ID") for report in reports
    ]
    if len(report_ids) != len(set(report_ids)):
        raise ValueError("private manifest contains duplicate report IDs")

    verified_key = _identity_key(verified_source_guild_id)
    selected = [
        dict(report)
        for report in reports
        if report.get("guild_id") is not None
        and _identity_key(report.get("guild_id")) == verified_key
    ]
    if not selected:
        raise ValueError("verified guild filter selected no reports")

    normalized_target = expected_guild_label.strip().casefold()
    for report in selected:
        guild_name = report.get("guild_name")
        if (
            not isinstance(guild_name, str)
            or guild_name.strip().casefold() != normalized_target
        ):
            raise ValueError("verified guild filter selected a conflicting guild name")

    snapshot_review = _required_object(
        private_decision.get("snapshot_review"),
        "private_decision.snapshot_review",
    )
    expected_selected_count = _required_integer(
        snapshot_review.get("candidate_guild_id_report_count"),
        "private decision candidate report count",
    )
    if len(selected) != expected_selected_count:
        raise ValueError("verified guild report count differs from the identity decision")

    exact_report_ids = [
        _required_integer(value, "private decision exact-label report ID")
        for value in _required_list(
            snapshot_review.get("exact_label_report_ids"),
            "private_decision.snapshot_review.exact_label_report_ids",
        )
    ]
    if [report["id"] for report in selected] != exact_report_ids:
        raise ValueError(
            "verified guild report order or membership differs from the identity decision"
        )

    return selected


def filter_verified_guild_reports(
    *,
    public_manifest_path: Path,
    private_manifest_path: Path,
    public_identity_decision_path: Path,
    private_identity_decision_path: Path,
    private_output_path: Path,
    receipt_output_path: Path,
    expected_guild_label: str = "Argentum",
) -> dict[str, Any]:
    """Filter the exhaustive private snapshot by an explicitly verified source guild ID."""
    public_manifest, public_manifest_body = _load_object(
        public_manifest_path,
        "public report manifest receipt",
    )
    private_manifest, private_manifest_body = _load_object(
        private_manifest_path,
        "private report manifest",
    )
    public_decision, public_decision_body = _load_object(
        public_identity_decision_path,
        "public guild identity decision",
    )
    private_decision, private_decision_body = _load_object(
        private_identity_decision_path,
        "private guild identity decision",
    )

    report_count = _validate_public_manifest(
        public_manifest,
        private_manifest_body=private_manifest_body,
        expected_guild_label=expected_guild_label,
    )
    _validate_public_decision(
        public_decision,
        public_manifest_body=public_manifest_body,
        private_decision_body=private_decision_body,
        expected_guild_label=expected_guild_label,
    )
    verified_source_guild_id = _validate_private_decision(
        private_decision,
        public_decision=public_decision,
        public_manifest_body=public_manifest_body,
        private_manifest_body=private_manifest_body,
        expected_guild_label=expected_guild_label,
    )
    selected_reports = _filter_private_manifest(
        private_manifest,
        expected_report_count=report_count,
        expected_guild_label=expected_guild_label,
        verified_source_guild_id=verified_source_guild_id,
        private_decision=private_decision,
    )

    selected_report_ids = [report["id"] for report in selected_reports]
    ordered_ids_hash = _sha256_json(selected_report_ids)
    ordered_records_hash = _sha256_json(selected_reports)

    checks = {
        "public_manifest_verified": True,
        "private_manifest_sha256_verified": True,
        "public_identity_decision_verified": True,
        "private_identity_decision_sha256_verified": True,
        "explicit_operator_promotion_verified": True,
        "verified_source_guild_id_loaded_from_private_decision": True,
        "source_manifest_report_ids_unique": True,
        "selected_report_ids_unique": len(selected_report_ids)
        == len(set(selected_report_ids)),
        "selected_reports_match_verified_source_guild_id": True,
        "selected_reports_match_target_label_casefold": True,
        "selected_report_membership_matches_identity_decision": True,
        "public_receipt_contains_no_source_scalar_values": True,
        "source_guild_id_not_published": True,
        "raw_report_records_not_published": True,
    }
    all_checks_passed = all(checks.values())

    private_payload = {
        "schema_version": 1,
        "manifest_kind": "verified_guild_report_manifest_private",
        "manifest_version": _FILTER_VERSION,
        "target_guild_label": expected_guild_label,
        "verified_source_guild_id": verified_source_guild_id,
        "source_public_manifest_name": public_manifest_path.name,
        "source_public_manifest_sha256": _sha256_bytes(public_manifest_body),
        "source_private_manifest_name": private_manifest_path.name,
        "source_private_manifest_sha256": _sha256_bytes(private_manifest_body),
        "source_public_identity_decision_name": public_identity_decision_path.name,
        "source_public_identity_decision_sha256": _sha256_bytes(public_decision_body),
        "source_private_identity_decision_name": private_identity_decision_path.name,
        "source_private_identity_decision_sha256": _sha256_bytes(private_decision_body),
        "selection_order": "source_manifest_order",
        "deduplication_key": "/reports/*/id",
        "reports": selected_reports,
        "manifest_hashes": {
            "ordered_report_ids_sha256": ordered_ids_hash,
            "ordered_report_records_sha256": ordered_records_hash,
        },
        "integrity_checks": checks,
        "summary": {
            "source_report_count": report_count,
            "selected_report_count": len(selected_reports),
            "unique_selected_report_id_count": len(set(selected_report_ids)),
            "duplicate_selected_report_occurrence_count": 0,
            "contains_source_scalar_values": True,
        },
    }
    private_body = _write_json(private_output_path, private_payload)

    receipt = {
        "schema_version": 1,
        "manifest_kind": "verified_guild_report_manifest",
        "manifest_version": _FILTER_VERSION,
        "source_public_manifest_name": public_manifest_path.name,
        "source_public_manifest_sha256": _sha256_bytes(public_manifest_body),
        "source_public_identity_decision_name": public_identity_decision_path.name,
        "source_public_identity_decision_sha256": _sha256_bytes(public_decision_body),
        "source_private_guild_manifest_name": private_output_path.name,
        "source_private_guild_manifest_sha256": _sha256_bytes(private_body),
        "target": {
            "guild_label": expected_guild_label,
            "source_guild_id_published": False,
            "report_ids_published": False,
            "raw_report_records_published": False,
        },
        "selection_contract": {
            "filter_field": "/reports/*/guild_id",
            "filter_operation": "equals_verified_private_source_guild_id",
            "deduplication_key": "/reports/*/id",
            "selection_order": "source_manifest_order",
        },
        "manifest_hashes": {
            "ordered_report_ids_sha256": ordered_ids_hash,
            "ordered_report_records_sha256": ordered_records_hash,
        },
        "integrity_checks": checks,
        "summary": {
            "all_integrity_checks_passed": all_checks_passed,
            "source_report_count": report_count,
            "selected_report_count": len(selected_reports),
            "unique_selected_report_id_count": len(set(selected_report_ids)),
            "duplicate_selected_report_occurrence_count": 0,
            "contains_raw_payload": False,
            "contains_source_scalar_values": False,
            "guild_identity_verified": True,
            "guild_filtering_completed": all_checks_passed,
            "ready_for_full_guild_crawl": False,
            "planner_scoring_allowed": False,
        },
        "decision_boundary": {
            "status": (
                "verified_guild_report_manifest_filtered"
                if all_checks_passed
                else "verified_guild_report_manifest_failed"
            ),
            "guild_identity_verified": True,
            "ready_for_guild_filtering": True,
            "guild_filtering_completed": all_checks_passed,
            "guild_report_manifest_deduplicated": all_checks_passed,
            "guild_api_route_semantics_verified": False,
            "full_crawl_collection_contract_reviewed": False,
            "ready_for_full_guild_crawl": False,
            "ready_for_multi_report_character_graph": False,
            "ready_for_performance_model": False,
            "ready_for_bis25_scoring": False,
            "planner_scoring_allowed": False,
        },
    }
    _write_json(receipt_output_path, receipt)
    return receipt


__all__ = ["filter_verified_guild_reports"]
