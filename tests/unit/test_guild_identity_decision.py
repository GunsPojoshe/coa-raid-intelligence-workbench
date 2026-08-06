from __future__ import annotations

import json
from pathlib import Path

import pytest

from coa_workbench.collector.guild_identity_decision import decide_guild_identity


def _write_json(path: Path, payload: object) -> bytes:
    body = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(body)
    return body


def _sha256(body: bytes) -> str:
    import hashlib

    return hashlib.sha256(body).hexdigest()


def _build_inputs(tmp_path: Path) -> dict[str, Path]:
    public_manifest_path = tmp_path / "public-manifest.json"
    private_manifest_path = tmp_path / "private-manifest.json"
    public_snapshot_path = tmp_path / "public-snapshot.json"
    private_snapshot_path = tmp_path / "private-snapshot.json"
    public_mapping_path = tmp_path / "public-mapping.json"
    private_mapping_path = tmp_path / "private-mapping.json"

    source_hashes = {
        "source_terminal_receipt_sha256": "a" * 64,
        "source_terminal_private_sha256": "b" * 64,
        "source_mapping_sha256": "c" * 64,
    }
    private_manifest = {
        "schema_version": 1,
        "manifest_kind": "public_report_manifest_private_batch",
        "manifest_version": "public-report-manifest-v1",
        "target_guild_label": "Argentum",
        **source_hashes,
        "summary": {
            "contains_source_scalar_values": True,
            "report_count": 3,
        },
        "reports": [
            {"id": 1, "guild_id": 101, "guild_name": "ARGENTUM"},
            {"id": 2, "guild_id": 101, "guild_name": "Argentum"},
            {"id": 3, "guild_id": 202, "guild_name": "Other"},
        ],
    }
    private_manifest_body = _write_json(private_manifest_path, private_manifest)

    public_manifest = {
        "schema_version": 1,
        "manifest_kind": "public_report_manifest_capture",
        "manifest_version": "public-report-manifest-v1",
        **source_hashes,
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
        "guild_field_summary": {
            "target_label_exact_match_report_count": 2,
            "target_label_distinct_non_null_guild_id_count": 1,
        },
        "decision_boundary": {
            "guild_identity_verified": False,
            "ready_for_guild_filtering": False,
        },
    }
    public_manifest_body = _write_json(public_manifest_path, public_manifest)

    private_snapshot = {
        "schema_version": 1,
        "review_kind": "guild_identity_snapshot_private_review",
        "review_version": "guild-identity-snapshot-review-v1",
        "target_guild_label": "Argentum",
        "candidate_source_guild_id": 101,
        "exact_label_report_ids": [1, 2],
    }
    private_snapshot_body = _write_json(private_snapshot_path, private_snapshot)

    public_snapshot = {
        "schema_version": 1,
        "review_kind": "guild_identity_snapshot_review",
        "review_version": "guild-identity-snapshot-review-v1",
        "source_public_manifest_receipt_sha256": _sha256(public_manifest_body),
        "source_private_manifest_sha256": _sha256(private_manifest_body),
        "source_private_review_sha256": _sha256(private_snapshot_body),
        "target": {
            "guild_label": "Argentum",
            "source_guild_id_published": False,
        },
        "summary": {
            "all_integrity_checks_passed": True,
            "contains_source_scalar_values": False,
            "exact_label_report_count": 2,
            "candidate_guild_id_report_count": 2,
            "candidate_guild_id_conflicting_non_empty_name_count": 0,
        },
        "decision_boundary": {
            "snapshot_internal_identity_consistent": True,
            "ready_for_independent_source_identity_review": True,
            "guild_identity_verified": False,
        },
    }
    _write_json(public_snapshot_path, public_snapshot)

    capture_binding = {
        "bytes_uncompressed": 93,
        "observation_id": "d" * 64,
        "payload_hash": "e" * 64,
        "raw_id": "f" * 64,
        "schema_fingerprint": "1" * 64,
    }
    mapped_fields = [
        {"semantic_name": "guild_id"},
        {"semantic_name": "guild_name"},
        {"semantic_name": "realm"},
        {"semantic_name": "report_count"},
    ]
    private_mapping = {
        "schema_version": 1,
        "mapping_kind": "guild_identity_search_mapping_review_private",
        "mapping_version": "guild-identity-search-mapping-review-v1",
        "target_guild_label": "Argentum",
        "candidate_source_guild_id": 101,
        "capture_binding": capture_binding,
        "reviewed_guild_object": {
            "guild_id": 101,
            "guild_name": "ARGENTUM",
            "realm": "Test Realm",
            "report_count": "2",
        },
        "mapped_fields": mapped_fields,
    }
    private_mapping_body = _write_json(private_mapping_path, private_mapping)

    public_mapping = {
        "schema_version": 1,
        "mapping_kind": "guild_identity_search_mapping_review",
        "mapping_version": "guild-identity-search-mapping-review-v1",
        "source_private_review_sha256": _sha256(private_mapping_body),
        "target": {
            "guild_label": "Argentum",
            "raw_payload_published": False,
            "source_guild_id_published": False,
        },
        "capture_binding": capture_binding,
        "summary": {
            "all_integrity_checks_passed": True,
            "cross_endpoint_identity_candidate_observed": True,
            "ready_for_guild_identity_decision_review": True,
            "contains_raw_payload": False,
            "contains_source_scalar_values": False,
        },
        "evidence_summary": {
            "guild_search_result_count": 1,
            "guild_id_source_candidate_match_count": 1,
            "guild_name_casefold_match_count": 1,
            "cross_endpoint_identity_candidate_observed": True,
        },
        "decision_boundary": {
            "independent_source_identity_candidate_observed": True,
            "guild_identity_verified": False,
            "ready_for_guild_filtering": False,
        },
    }
    _write_json(public_mapping_path, public_mapping)

    return {
        "public_manifest_path": public_manifest_path,
        "private_manifest_path": private_manifest_path,
        "public_snapshot_review_path": public_snapshot_path,
        "private_snapshot_review_path": private_snapshot_path,
        "public_mapping_review_path": public_mapping_path,
        "private_mapping_review_path": private_mapping_path,
        "private_output_path": tmp_path / "private-decision.json",
        "receipt_output_path": tmp_path / "decision.json",
    }


def test_decision_promotes_bound_cross_endpoint_identity(tmp_path: Path) -> None:
    paths = _build_inputs(tmp_path)

    receipt = decide_guild_identity(
        **paths,
        promote_identity=True,
        expected_guild_label="Argentum",
    )

    boundary = receipt["decision_boundary"]
    assert boundary["independent_source_identity_verified"] is True
    assert boundary["guild_identity_verified"] is True
    assert boundary["ready_for_guild_filtering"] is True
    assert boundary["ready_for_full_guild_crawl"] is False
    assert boundary["planner_scoring_allowed"] is False

    encoded = paths["receipt_output_path"].read_text(encoding="utf-8")
    assert "candidate_source_guild_id" not in encoded
    assert "Test Realm" not in encoded
    assert "ARGENTUM" not in encoded


def test_decision_requires_explicit_promotion(tmp_path: Path) -> None:
    paths = _build_inputs(tmp_path)

    with pytest.raises(ValueError, match="explicit guild identity promotion"):
        decide_guild_identity(
            **paths,
            promote_identity=False,
            expected_guild_label="Argentum",
        )


def test_decision_rejects_cross_endpoint_id_mismatch(tmp_path: Path) -> None:
    paths = _build_inputs(tmp_path)
    private_mapping = json.loads(
        paths["private_mapping_review_path"].read_text(encoding="utf-8")
    )
    private_mapping["candidate_source_guild_id"] = 999
    private_mapping_body = _write_json(
        paths["private_mapping_review_path"],
        private_mapping,
    )
    public_mapping = json.loads(
        paths["public_mapping_review_path"].read_text(encoding="utf-8")
    )
    public_mapping["source_private_review_sha256"] = _sha256(private_mapping_body)
    _write_json(paths["public_mapping_review_path"], public_mapping)

    with pytest.raises(ValueError, match="cross-endpoint guild ID mismatch"):
        decide_guild_identity(
            **paths,
            promote_identity=True,
            expected_guild_label="Argentum",
        )


def test_decision_rejects_snapshot_name_conflict(tmp_path: Path) -> None:
    paths = _build_inputs(tmp_path)
    private_manifest = json.loads(
        paths["private_manifest_path"].read_text(encoding="utf-8")
    )
    private_manifest["reports"][1]["guild_name"] = "Conflicting Name"
    private_manifest_body = _write_json(
        paths["private_manifest_path"],
        private_manifest,
    )
    public_manifest = json.loads(
        paths["public_manifest_path"].read_text(encoding="utf-8")
    )
    public_manifest["source_private_manifest_sha256"] = _sha256(
        private_manifest_body
    )
    public_manifest_body = _write_json(
        paths["public_manifest_path"],
        public_manifest,
    )
    public_snapshot = json.loads(
        paths["public_snapshot_review_path"].read_text(encoding="utf-8")
    )
    public_snapshot["source_public_manifest_receipt_sha256"] = _sha256(
        public_manifest_body
    )
    public_snapshot["source_private_manifest_sha256"] = _sha256(
        private_manifest_body
    )
    _write_json(paths["public_snapshot_review_path"], public_snapshot)

    with pytest.raises(ValueError, match="exact-label count mismatch"):
        decide_guild_identity(
            **paths,
            promote_identity=True,
            expected_guild_label="Argentum",
        )
