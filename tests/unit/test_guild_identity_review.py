from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from coa_workbench.collector.guild_identity_review import review_guild_identity_snapshot


def _write_json(path: Path, payload: dict[str, Any]) -> bytes:
    body = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(body)
    return body


def _private_manifest(reports: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "manifest_kind": "public_report_manifest_private_batch",
        "manifest_version": "public-report-manifest-v1",
        "target_guild_label": "Argentum",
        "source_terminal_receipt_sha256": "a" * 64,
        "source_terminal_private_sha256": "b" * 64,
        "source_mapping_sha256": "c" * 64,
        "reports": reports,
        "summary": {
            "report_count": len(reports),
            "contains_source_scalar_values": True,
        },
    }


def _public_receipt(
    *,
    private_body: bytes,
    report_count: int,
    exact_match_count: int = 17,
    distinct_target_id_count: int = 1,
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "manifest_kind": "public_report_manifest_capture",
        "manifest_version": "public-report-manifest-v1",
        "source_private_manifest_sha256": hashlib.sha256(private_body).hexdigest(),
        "source_terminal_receipt_sha256": "a" * 64,
        "source_terminal_private_sha256": "b" * 64,
        "source_mapping_sha256": "c" * 64,
        "target": {
            "guild_label": "Argentum",
            "guild_identity_status": "operator_named_target_unresolved",
        },
        "summary": {
            "all_integrity_checks_passed": True,
            "contains_source_scalar_values": False,
            "ready_for_guild_identity_review": True,
            "report_occurrence_count": report_count,
        },
        "guild_field_summary": {
            "target_label_exact_match_report_count": exact_match_count,
            "target_label_distinct_non_null_guild_id_count": distinct_target_id_count,
        },
        "decision_boundary": {
            "guild_identity_verified": False,
            "ready_for_guild_filtering": False,
        },
    }


def _target_reports() -> list[dict[str, Any]]:
    return [
        {"id": report_id, "guild_id": 700, "guild_name": "Argentum"}
        for report_id in range(1, 18)
    ]


def _contains_value(value: object, expected: object) -> bool:
    if isinstance(value, dict):
        return any(_contains_value(item, expected) for item in value.values())
    if isinstance(value, list):
        return any(_contains_value(item, expected) for item in value)
    return value == expected


def test_snapshot_review_produces_scalar_free_candidate_receipt(tmp_path: Path) -> None:
    reports = _target_reports() + [
        {"id": 18, "guild_id": 701, "guild_name": "Another Guild"}
    ]
    private_path = tmp_path / "private.json"
    private_body = _write_json(private_path, _private_manifest(reports))
    receipt_path = tmp_path / "manifest-receipt.json"
    _write_json(
        receipt_path,
        _public_receipt(private_body=private_body, report_count=len(reports)),
    )
    private_output = tmp_path / "review.private.json"
    output = tmp_path / "review.json"

    receipt = review_guild_identity_snapshot(
        private_manifest_path=private_path,
        public_manifest_receipt_path=receipt_path,
        private_output_path=private_output,
        receipt_output_path=output,
    )

    assert receipt["summary"]["all_integrity_checks_passed"] is True
    assert receipt["summary"]["exact_label_report_count"] == 17
    assert receipt["summary"]["candidate_guild_id_conflicting_non_empty_name_count"] == 0
    assert receipt["decision_boundary"]["snapshot_internal_identity_consistent"] is True
    assert receipt["decision_boundary"]["independent_source_identity_verified"] is False
    assert receipt["decision_boundary"]["guild_identity_verified"] is False
    assert receipt["decision_boundary"]["ready_for_guild_filtering"] is False
    assert receipt["summary"]["contains_source_scalar_values"] is False
    assert _contains_value(receipt, 700) is False

    private_review = json.loads(private_output.read_text(encoding="utf-8"))
    assert private_review["candidate_source_guild_id"] == 700
    assert private_review["exact_label_report_ids"] == list(range(1, 18))


def test_snapshot_review_records_conflicting_name_without_promotion(tmp_path: Path) -> None:
    reports = _target_reports() + [
        {"id": 18, "guild_id": 700, "guild_name": "Conflicting Guild"}
    ]
    private_path = tmp_path / "private.json"
    private_body = _write_json(private_path, _private_manifest(reports))
    receipt_path = tmp_path / "manifest-receipt.json"
    _write_json(
        receipt_path,
        _public_receipt(private_body=private_body, report_count=len(reports)),
    )

    receipt = review_guild_identity_snapshot(
        private_manifest_path=private_path,
        public_manifest_receipt_path=receipt_path,
        private_output_path=tmp_path / "review.private.json",
        receipt_output_path=tmp_path / "review.json",
    )

    assert receipt["summary"]["candidate_guild_id_conflicting_non_empty_name_count"] == 1
    assert receipt["summary"]["all_integrity_checks_passed"] is False
    assert receipt["decision_boundary"]["status"] == (
        "snapshot_internal_guild_identity_review_failed"
    )
    assert receipt["decision_boundary"]["ready_for_independent_source_identity_review"] is False
    assert receipt["decision_boundary"]["guild_identity_verified"] is False


def test_snapshot_review_rejects_private_manifest_hash_mismatch(tmp_path: Path) -> None:
    reports = _target_reports()
    private_path = tmp_path / "private.json"
    private_body = _write_json(private_path, _private_manifest(reports))
    public_receipt = _public_receipt(private_body=private_body, report_count=len(reports))
    public_receipt["source_private_manifest_sha256"] = "0" * 64
    receipt_path = tmp_path / "manifest-receipt.json"
    _write_json(receipt_path, public_receipt)

    with pytest.raises(ValueError, match="private manifest SHA-256"):
        review_guild_identity_snapshot(
            private_manifest_path=private_path,
            public_manifest_receipt_path=receipt_path,
            private_output_path=tmp_path / "review.private.json",
            receipt_output_path=tmp_path / "review.json",
        )
