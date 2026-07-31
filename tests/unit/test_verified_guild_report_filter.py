from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from coa_workbench.collector.verified_guild_report_filter import (
    filter_verified_guild_reports,
)


def _write_json(path: Path, payload: object) -> bytes:
    body = (
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(body)
    return body


def _sha256(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def _build_inputs(tmp_path: Path) -> dict[str, Path]:
    public_manifest_path = tmp_path / "public-manifest.json"
    private_manifest_path = tmp_path / "private-manifest.json"
    public_decision_path = tmp_path / "public-decision.json"
    private_decision_path = tmp_path / "private-decision.json"

    private_manifest = {
        "schema_version": 1,
        "manifest_kind": "public_report_manifest_private_batch",
        "manifest_version": "public-report-manifest-v1",
        "target_guild_label": "Argentum",
        "summary": {"contains_source_scalar_values": True, "report_count": 3},
        "reports": [
            {
                "id": 11,
                "guild_id": 101,
                "guild_name": "Argentum",
                "title": "A",
            },
            {"id": 12, "guild_id": 202, "guild_name": "Other", "title": "B"},
            {
                "id": 13,
                "guild_id": 101,
                "guild_name": "ARGENTUM",
                "title": "C",
            },
        ],
    }
    private_manifest_body = _write_json(private_manifest_path, private_manifest)

    public_manifest = {
        "schema_version": 1,
        "manifest_kind": "public_report_manifest_capture",
        "manifest_version": "public-report-manifest-v1",
        "source_private_manifest_sha256": _sha256(private_manifest_body),
        "target": {
            "guild_label": "Argentum",
            "guild_identity_status": "operator_named_target_unresolved",
        },
        "summary": {
            "all_integrity_checks_passed": True,
            "contains_source_scalar_values": False,
            "ready_for_guild_identity_review": True,
            "report_occurrence_count": 3,
        },
    }
    public_manifest_body = _write_json(public_manifest_path, public_manifest)

    private_decision = {
        "schema_version": 1,
        "decision_kind": "guild_identity_decision_private",
        "decision_version": "guild-identity-decision-v1",
        "target_guild_label": "Argentum",
        "explicit_operator_promotion": True,
        "candidate_source_guild_id": 101,
        "source_public_manifest_sha256": _sha256(public_manifest_body),
        "source_private_manifest_sha256": _sha256(private_manifest_body),
        "source_public_snapshot_review_sha256": "a" * 64,
        "source_public_mapping_review_sha256": "b" * 64,
        "snapshot_review": {
            "candidate_guild_id_report_count": 2,
            "exact_label_report_ids": [11, 13],
        },
        "integrity_checks": {"all": True},
        "guild_identity_verified": True,
    }
    private_decision_body = _write_json(private_decision_path, private_decision)

    public_decision = {
        "schema_version": 1,
        "decision_kind": "guild_identity_decision",
        "decision_version": "guild-identity-decision-v1",
        "source_public_manifest_sha256": _sha256(public_manifest_body),
        "source_public_snapshot_review_sha256": "a" * 64,
        "source_public_mapping_review_sha256": "b" * 64,
        "source_private_decision_sha256": _sha256(private_decision_body),
        "target": {
            "guild_label": "Argentum",
            "source_guild_id_published": False,
            "raw_payload_published": False,
        },
        "promotion": {
            "explicit_operator_promotion": True,
            "promotion_mechanism": "required_cli_flag",
        },
        "integrity_checks": {"all": True},
        "summary": {
            "all_integrity_checks_passed": True,
            "independent_source_identity_verified": True,
            "guild_identity_verified": True,
            "ready_for_guild_filtering": True,
            "contains_raw_payload": False,
            "contains_source_scalar_values": False,
        },
        "decision_boundary": {
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
        },
    }
    _write_json(public_decision_path, public_decision)

    return {
        "public_manifest_path": public_manifest_path,
        "private_manifest_path": private_manifest_path,
        "public_identity_decision_path": public_decision_path,
        "private_identity_decision_path": private_decision_path,
        "private_output_path": tmp_path / "guild-manifest.private.json",
        "receipt_output_path": tmp_path / "guild-manifest.json",
    }


def test_filter_builds_scalar_free_deduplicated_receipt(tmp_path: Path) -> None:
    paths = _build_inputs(tmp_path)

    receipt = filter_verified_guild_reports(**paths)

    assert receipt["summary"]["selected_report_count"] == 2
    assert receipt["summary"]["unique_selected_report_id_count"] == 2
    assert receipt["decision_boundary"]["guild_filtering_completed"] is True
    assert receipt["decision_boundary"]["ready_for_full_guild_crawl"] is False
    assert receipt["decision_boundary"]["planner_scoring_allowed"] is False

    encoded = paths["receipt_output_path"].read_text(encoding="utf-8")
    assert '"guild_id": 101' not in encoded
    assert '"id": 11' not in encoded
    assert '"title": "A"' not in encoded

    private = json.loads(
        paths["private_output_path"].read_text(encoding="utf-8")
    )
    assert [report["id"] for report in private["reports"]] == [11, 13]


def test_filter_rejects_unverified_public_decision(tmp_path: Path) -> None:
    paths = _build_inputs(tmp_path)
    decision = json.loads(
        paths["public_identity_decision_path"].read_text(encoding="utf-8")
    )
    decision["decision_boundary"]["guild_identity_verified"] = False
    _write_json(paths["public_identity_decision_path"], decision)

    with pytest.raises(ValueError, match="identity decision boundary mismatch"):
        filter_verified_guild_reports(**paths)


def test_filter_rejects_conflicting_selected_name(tmp_path: Path) -> None:
    paths = _build_inputs(tmp_path)
    manifest = json.loads(
        paths["private_manifest_path"].read_text(encoding="utf-8")
    )
    manifest["reports"][2]["guild_name"] = "Conflict"
    private_manifest_body = _write_json(paths["private_manifest_path"], manifest)

    public_manifest = json.loads(
        paths["public_manifest_path"].read_text(encoding="utf-8")
    )
    public_manifest["source_private_manifest_sha256"] = _sha256(
        private_manifest_body
    )
    public_manifest_body = _write_json(
        paths["public_manifest_path"], public_manifest
    )

    private_decision = json.loads(
        paths["private_identity_decision_path"].read_text(encoding="utf-8")
    )
    private_decision["source_public_manifest_sha256"] = _sha256(
        public_manifest_body
    )
    private_decision["source_private_manifest_sha256"] = _sha256(
        private_manifest_body
    )
    private_decision_body = _write_json(
        paths["private_identity_decision_path"], private_decision
    )

    public_decision = json.loads(
        paths["public_identity_decision_path"].read_text(encoding="utf-8")
    )
    public_decision["source_public_manifest_sha256"] = _sha256(
        public_manifest_body
    )
    public_decision["source_private_decision_sha256"] = _sha256(
        private_decision_body
    )
    _write_json(paths["public_identity_decision_path"], public_decision)

    with pytest.raises(ValueError, match="conflicting guild name"):
        filter_verified_guild_reports(**paths)
