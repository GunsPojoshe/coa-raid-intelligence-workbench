from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

_REVIEW_VERSION = "guild-identity-snapshot-review-v1"
_MANIFEST_KIND = "public_report_manifest_capture"
_MANIFEST_VERSION = "public-report-manifest-v1"
_PRIVATE_MANIFEST_KIND = "public_report_manifest_private_batch"


def _generated_at() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _required_object(value: object, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"guild identity review field {field_name} must be an object")
    return value


def _required_list(value: object, field_name: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"guild identity review field {field_name} must be an array")
    return value


def _required_integer(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"guild identity review field {field_name} must be an integer")
    return value


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
    body = (json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode()
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_bytes(body)
    temporary.replace(path)
    return body


def _normalized_name(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    return normalized if normalized else None


def _identity_key(value: object) -> tuple[str, str] | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, str)):
        raise ValueError("guild identity values must be null, integer or string scalars")
    return type(value).__name__, str(value)


def _validate_public_manifest_receipt(
    receipt: Mapping[str, Any],
    *,
    private_manifest_body: bytes,
    expected_guild_label: str,
) -> tuple[int, int, int]:
    if receipt.get("schema_version") != 1:
        raise ValueError("public manifest receipt schema mismatch")
    if receipt.get("manifest_kind") != _MANIFEST_KIND:
        raise ValueError("public manifest receipt kind mismatch")
    if receipt.get("manifest_version") != _MANIFEST_VERSION:
        raise ValueError("public manifest receipt version mismatch")

    target = _required_object(receipt.get("target"), "manifest.target")
    if target.get("guild_label") != expected_guild_label:
        raise ValueError("public manifest receipt guild label mismatch")
    if target.get("guild_identity_status") != "operator_named_target_unresolved":
        raise ValueError("public manifest receipt unexpectedly resolves guild identity")

    summary = _required_object(receipt.get("summary"), "manifest.summary")
    if summary.get("all_integrity_checks_passed") is not True:
        raise ValueError("public manifest integrity checks did not pass")
    if summary.get("contains_source_scalar_values") is not False:
        raise ValueError("public manifest receipt is not scalar-free")
    if summary.get("ready_for_guild_identity_review") is not True:
        raise ValueError("public manifest receipt is not ready for identity review")

    boundary = _required_object(receipt.get("decision_boundary"), "manifest.decision_boundary")
    if boundary.get("guild_identity_verified") is not False:
        raise ValueError("guild identity was already marked verified")
    if boundary.get("ready_for_guild_filtering") is not False:
        raise ValueError("guild filtering was enabled before identity review")

    expected_private_hash = receipt.get("source_private_manifest_sha256")
    if not isinstance(expected_private_hash, str) or len(expected_private_hash) != 64:
        raise ValueError("public manifest receipt private hash is missing")
    if _sha256_bytes(private_manifest_body) != expected_private_hash:
        raise ValueError("private manifest SHA-256 does not match the public receipt")

    guild_summary = _required_object(
        receipt.get("guild_field_summary"), "manifest.guild_field_summary"
    )
    exact_match_count = _required_integer(
        guild_summary.get("target_label_exact_match_report_count"),
        "target_label_exact_match_report_count",
    )
    distinct_target_id_count = _required_integer(
        guild_summary.get("target_label_distinct_non_null_guild_id_count"),
        "target_label_distinct_non_null_guild_id_count",
    )
    report_count = _required_integer(summary.get("report_occurrence_count"), "report_occurrence_count")
    return report_count, exact_match_count, distinct_target_id_count


def _validate_private_manifest(
    private: Mapping[str, Any],
    public_receipt: Mapping[str, Any],
    *,
    expected_guild_label: str,
    expected_report_count: int,
) -> list[dict[str, Any]]:
    if private.get("schema_version") != 1:
        raise ValueError("private manifest schema mismatch")
    if private.get("manifest_kind") != _PRIVATE_MANIFEST_KIND:
        raise ValueError("private manifest kind mismatch")
    if private.get("manifest_version") != _MANIFEST_VERSION:
        raise ValueError("private manifest version mismatch")
    if private.get("target_guild_label") != expected_guild_label:
        raise ValueError("private manifest guild label mismatch")

    for field_name in (
        "source_terminal_receipt_sha256",
        "source_terminal_private_sha256",
        "source_mapping_sha256",
    ):
        if private.get(field_name) != public_receipt.get(field_name):
            raise ValueError(f"private/public manifest mismatch: {field_name}")

    private_summary = _required_object(private.get("summary"), "private.summary")
    if private_summary.get("contains_source_scalar_values") is not True:
        raise ValueError("private manifest scalar boundary mismatch")
    if private_summary.get("report_count") != expected_report_count:
        raise ValueError("private manifest report count mismatch")

    reports = [
        _required_object(value, "private.reports[]")
        for value in _required_list(private.get("reports"), "private.reports")
    ]
    if len(reports) != expected_report_count:
        raise ValueError("private manifest reports array count mismatch")
    return reports


def review_guild_identity_snapshot(
    *,
    private_manifest_path: Path,
    public_manifest_receipt_path: Path,
    private_output_path: Path,
    receipt_output_path: Path,
    expected_guild_label: str = "Argentum",
) -> dict[str, Any]:
    """Review one private public-report snapshot without promoting guild identity."""
    private, private_body = _load_object(private_manifest_path, "private public-report manifest")
    public_receipt, public_receipt_body = _load_object(
        public_manifest_receipt_path, "public manifest receipt"
    )
    expected_report_count, expected_exact_count, expected_distinct_id_count = (
        _validate_public_manifest_receipt(
            public_receipt,
            private_manifest_body=private_body,
            expected_guild_label=expected_guild_label,
        )
    )
    reports = _validate_private_manifest(
        private,
        public_receipt,
        expected_guild_label=expected_guild_label,
        expected_report_count=expected_report_count,
    )

    normalized_target = expected_guild_label.strip().casefold()
    exact_rows: list[dict[str, Any]] = []
    target_identity_keys: set[tuple[str, str]] = set()
    identity_values: dict[tuple[str, str], object] = {}
    all_report_ids: list[int] = []

    for report in reports:
        report_id = _required_integer(report.get("id"), "private.reports[].id")
        all_report_ids.append(report_id)
        guild_name = _normalized_name(report.get("guild_name"))
        guild_key = _identity_key(report.get("guild_id"))
        if guild_key is not None:
            identity_values[guild_key] = report.get("guild_id")
        if guild_name is not None and guild_name.casefold() == normalized_target:
            exact_rows.append(report)
            if guild_key is not None:
                target_identity_keys.add(guild_key)

    if len(set(all_report_ids)) != len(all_report_ids):
        raise ValueError("private manifest contains duplicate report IDs")

    candidate_key = next(iter(target_identity_keys)) if len(target_identity_keys) == 1 else None
    candidate_value = identity_values.get(candidate_key) if candidate_key is not None else None
    candidate_rows = [
        report for report in reports if _identity_key(report.get("guild_id")) == candidate_key
    ] if candidate_key is not None else []
    candidate_names = {
        name.casefold()
        for report in candidate_rows
        if (name := _normalized_name(report.get("guild_name"))) is not None
    }
    conflicting_names = {name for name in candidate_names if name != normalized_target}
    exact_null_id_count = sum(report.get("guild_id") is None for report in exact_rows)
    candidate_empty_name_count = sum(
        _normalized_name(report.get("guild_name")) is None for report in candidate_rows
    )
    exact_report_ids = [_required_integer(report.get("id"), "target report id") for report in exact_rows]

    checks = {
        "private_manifest_sha256_verified": True,
        "private_manifest_contract_verified": True,
        "public_manifest_boundary_preserved": True,
        "public_manifest_report_count_verified": len(reports) == expected_report_count,
        "exact_label_count_matches_public_receipt": len(exact_rows) == expected_exact_count,
        "distinct_target_id_count_matches_public_receipt": (
            len(target_identity_keys) == expected_distinct_id_count
        ),
        "all_exact_label_rows_have_non_null_guild_id": exact_null_id_count == 0,
        "exact_label_rows_have_one_source_guild_id": len(target_identity_keys) == 1,
        "exact_label_report_ids_unique": len(set(exact_report_ids)) == len(exact_report_ids),
        "candidate_id_has_no_conflicting_non_empty_guild_name": not conflicting_names,
    }
    snapshot_consistent = all(checks.values())

    private_review = {
        "schema_version": 1,
        "review_kind": "guild_identity_snapshot_private_review",
        "review_version": _REVIEW_VERSION,
        "generated_at": _generated_at(),
        "source_private_manifest_name": private_manifest_path.name,
        "source_private_manifest_sha256": _sha256_bytes(private_body),
        "source_public_manifest_receipt_name": public_manifest_receipt_path.name,
        "source_public_manifest_receipt_sha256": _sha256_bytes(public_receipt_body),
        "target_guild_label": expected_guild_label,
        "candidate_source_guild_id": candidate_value,
        "exact_label_report_ids": exact_report_ids,
        "candidate_id_rows": [
            {
                "report_id": _required_integer(report.get("id"), "candidate report id"),
                "guild_id": report.get("guild_id"),
                "guild_name": report.get("guild_name"),
            }
            for report in candidate_rows
        ],
        "summary": {
            "exact_label_report_count": len(exact_rows),
            "exact_label_null_guild_id_count": exact_null_id_count,
            "distinct_exact_label_guild_id_count": len(target_identity_keys),
            "candidate_guild_id_report_count": len(candidate_rows),
            "candidate_guild_id_empty_name_count": candidate_empty_name_count,
            "candidate_guild_id_distinct_non_empty_name_count": len(candidate_names),
            "candidate_guild_id_conflicting_non_empty_name_count": len(conflicting_names),
            "contains_source_scalar_values": True,
        },
        "integrity_checks": checks,
        "decision_boundary": {
            "snapshot_internal_identity_consistent": snapshot_consistent,
            "independent_source_identity_verified": False,
            "guild_identity_verified": False,
            "ready_for_independent_source_identity_review": snapshot_consistent,
            "ready_for_guild_filtering": False,
            "ready_for_full_guild_crawl": False,
            "planner_scoring_allowed": False,
        },
    }
    private_review_body = _write_json(private_output_path, private_review)

    receipt = {
        "schema_version": 1,
        "review_kind": "guild_identity_snapshot_review",
        "review_version": _REVIEW_VERSION,
        "generated_at": _generated_at(),
        "source_private_manifest_name": private_manifest_path.name,
        "source_private_manifest_sha256": _sha256_bytes(private_body),
        "source_public_manifest_receipt_name": public_manifest_receipt_path.name,
        "source_public_manifest_receipt_sha256": _sha256_bytes(public_receipt_body),
        "source_private_review_name": private_output_path.name,
        "source_private_review_sha256": _sha256_bytes(private_review_body),
        "target": {
            "guild_label": expected_guild_label,
            "source_guild_id_published": False,
        },
        "summary": {
            "exact_label_report_count": len(exact_rows),
            "exact_label_null_guild_id_count": exact_null_id_count,
            "distinct_exact_label_guild_id_count": len(target_identity_keys),
            "candidate_guild_id_report_count": len(candidate_rows),
            "candidate_guild_id_empty_name_count": candidate_empty_name_count,
            "candidate_guild_id_distinct_non_empty_name_count": len(candidate_names),
            "candidate_guild_id_conflicting_non_empty_name_count": len(conflicting_names),
            "integrity_check_count": len(checks),
            "all_integrity_checks_passed": snapshot_consistent,
            "contains_source_scalar_values": False,
        },
        "integrity_checks": checks,
        "decision_boundary": {
            "status": (
                "snapshot_internal_guild_identity_candidate"
                if snapshot_consistent
                else "snapshot_internal_guild_identity_review_failed"
            ),
            "snapshot_internal_identity_consistent": snapshot_consistent,
            "independent_source_identity_verified": False,
            "guild_identity_verified": False,
            "ready_for_independent_source_identity_review": snapshot_consistent,
            "ready_for_guild_filtering": False,
            "ready_for_full_guild_crawl": False,
            "ready_for_multi_report_character_graph": False,
            "ready_for_performance_model": False,
            "ready_for_bis25_scoring": False,
            "planner_scoring_allowed": False,
        },
    }
    _write_json(receipt_output_path, receipt)
    return receipt


__all__ = ["review_guild_identity_snapshot"]
