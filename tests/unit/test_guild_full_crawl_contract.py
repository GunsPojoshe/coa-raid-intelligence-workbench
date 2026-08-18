from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from coa_workbench.collector.guild_full_crawl_contract import (
    build_guild_full_crawl_contract,
)


def _write_json(path: Path, payload: object) -> bytes:
    body = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode()
    path.write_bytes(body)
    return body


def _sha256(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def _build_inputs(tmp_path: Path) -> dict[str, Path]:
    public_manifest_path = tmp_path / "public-manifest.json"
    identity_decision_path = tmp_path / "identity-decision.json"
    guild_manifest_path = tmp_path / "guild-manifest.json"

    public_manifest = {
        "schema_version": 1,
        "manifest_kind": "public_report_manifest_capture",
        "manifest_version": "public-report-manifest-v1",
        "target": {"guild_label": "Argentum"},
        "summary": {
            "all_integrity_checks_passed": True,
            "contains_source_scalar_values": False,
            "report_occurrence_count": 3,
            "unique_report_id_count": 3,
            "duplicate_report_occurrence_count": 0,
        },
        "decision_boundary": {
            "manifest_page_range_completed": True,
            "ready_for_full_guild_crawl": False,
            "planner_scoring_allowed": False,
        },
    }
    public_manifest_body = _write_json(public_manifest_path, public_manifest)

    identity_decision = {
        "schema_version": 1,
        "decision_kind": "guild_identity_decision",
        "decision_version": "guild-identity-decision-v1",
        "source_public_manifest_sha256": _sha256(public_manifest_body),
        "target": {
            "guild_label": "Argentum",
            "source_guild_id_published": False,
        },
        "summary": {
            "all_integrity_checks_passed": True,
            "guild_identity_verified": True,
            "ready_for_guild_filtering": True,
            "contains_source_scalar_values": False,
        },
        "decision_boundary": {
            "guild_api_route_semantics_verified": False,
            "ready_for_full_guild_crawl": False,
            "planner_scoring_allowed": False,
        },
    }
    identity_decision_body = _write_json(identity_decision_path, identity_decision)

    guild_manifest = {
        "schema_version": 1,
        "manifest_kind": "verified_guild_report_manifest",
        "manifest_version": "verified-guild-report-manifest-v1",
        "source_public_manifest_sha256": _sha256(public_manifest_body),
        "source_public_identity_decision_sha256": _sha256(identity_decision_body),
        "target": {
            "guild_label": "Argentum",
            "raw_report_records_published": False,
            "report_ids_published": False,
            "source_guild_id_published": False,
        },
        "summary": {
            "all_integrity_checks_passed": True,
            "guild_identity_verified": True,
            "guild_filtering_completed": True,
            "contains_source_scalar_values": False,
            "source_report_count": 3,
            "selected_report_count": 2,
            "unique_selected_report_id_count": 2,
            "duplicate_selected_report_occurrence_count": 0,
        },
        "decision_boundary": {
            "guild_report_manifest_deduplicated": True,
            "full_crawl_collection_contract_reviewed": False,
            "guild_api_route_semantics_verified": False,
            "ready_for_full_guild_crawl": False,
            "planner_scoring_allowed": False,
        },
    }
    _write_json(guild_manifest_path, guild_manifest)

    return {
        "public_manifest_path": public_manifest_path,
        "identity_decision_path": identity_decision_path,
        "guild_manifest_path": guild_manifest_path,
    }


def test_contract_reviews_pre_crawl_boundary_without_enabling_crawl(
    tmp_path: Path,
) -> None:
    paths = _build_inputs(tmp_path)

    contract = build_guild_full_crawl_contract(**paths)

    assert contract["verified_baseline"]["source_public_report_count"] == 3
    assert contract["verified_baseline"]["selected_guild_report_count"] == 2
    boundary = contract["decision_boundary"]
    assert boundary["full_crawl_collection_contract_reviewed"] is True
    assert boundary["ready_for_bounded_route_semantics_capture"] is True
    assert boundary["guild_api_route_semantics_verified"] is False
    assert boundary["ready_for_full_guild_crawl"] is False
    assert boundary["planner_scoring_allowed"] is False


def test_contract_rejects_identity_manifest_hash_mismatch(tmp_path: Path) -> None:
    paths = _build_inputs(tmp_path)
    identity = json.loads(paths["identity_decision_path"].read_text())
    identity["source_public_manifest_sha256"] = "0" * 64
    _write_json(paths["identity_decision_path"], identity)

    with pytest.raises(ValueError, match="identity decision public manifest SHA-256"):
        build_guild_full_crawl_contract(**paths)


def test_contract_rejects_guild_manifest_that_enables_full_crawl(
    tmp_path: Path,
) -> None:
    paths = _build_inputs(tmp_path)
    guild_manifest = json.loads(paths["guild_manifest_path"].read_text())
    guild_manifest["decision_boundary"]["ready_for_full_guild_crawl"] = True
    _write_json(paths["guild_manifest_path"], guild_manifest)

    with pytest.raises(ValueError, match="guild report manifest enables full guild crawl"):
        build_guild_full_crawl_contract(**paths)


def test_contract_public_output_contains_no_report_or_guild_ids(tmp_path: Path) -> None:
    paths = _build_inputs(tmp_path)

    contract = build_guild_full_crawl_contract(**paths)
    encoded = json.dumps(contract, sort_keys=True)

    assert '"report_ids"' not in encoded
    assert "candidate_source_guild_id" not in encoded
    assert "verified_source_guild_id" not in encoded
    assert contract["target"]["report_ids_published"] is False
    assert contract["target"]["source_guild_id_published"] is False
