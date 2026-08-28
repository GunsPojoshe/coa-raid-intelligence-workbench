from __future__ import annotations

import json
from pathlib import Path

import pytest

from coa_workbench.collector.report_slice_mapping_publication import (
    publish_observed_report_slice_mappings,
)

_REVIEWED_BY = "operator"
_REVIEWED_AT = "2026-07-29T18:28:00+03:00"


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _mapping(mapping_id: str, contract_count: int, fingerprint: str) -> dict[str, object]:
    return {
        "mapping_id": mapping_id,
        "source_code": "coa_ascension_logs",
        "schema_fingerprint": fingerprint,
        "mapping_version": "1",
        "status": "verified",
        "entities": {},
        "event_type_map": {},
        "field_contracts": [
            {"semantic_status": "verified_parser_field", "ordinal": index}
            for index in range(contract_count)
        ],
        "reviewed_by": _REVIEWED_BY,
        "reviewed_at": _REVIEWED_AT,
        "mechanic_semantics_verified": False,
        "verification_scope": (
            "parser_schema_raw_archive_dry_run_and_cross_payload_linkage_only"
        ),
    }


def _promotion_fixture(tmp_path: Path) -> tuple[Path, Path]:
    staged = tmp_path / "staged"
    mappings = [
        {
            "mapping_id": "coa-encounter-detail-v1",
            "mapping_file": "coa_encounter_detail_v1.json",
            "field_contract_count": 35,
            "mapping": _mapping("coa-encounter-detail-v1", 35, "a" * 64),
            "raw_archive_verified": True,
            "cross_payload_consistent": True,
            "dry_run_counts": {
                "reports": 1,
                "encounters": 1,
                "actors": 31,
                "participants": 31,
                "aura_events": 0,
                "rejects": 0,
            },
        },
        {
            "mapping_id": "coa-report-detail-v1",
            "mapping_file": "coa_report_detail_v1.json",
            "field_contract_count": 19,
            "mapping": _mapping("coa-report-detail-v1", 19, "b" * 64),
            "raw_archive_verified": True,
            "cross_payload_consistent": True,
            "dry_run_counts": {
                "reports": 1,
                "encounters": 14,
                "actors": 0,
                "participants": 0,
                "aura_events": 0,
                "rejects": 0,
            },
        },
    ]
    for row in mappings:
        _write_json(staged / str(row["mapping_file"]), row["mapping"])

    promotion = {
        "schema_version": 1,
        "promotion_kind": "observed_report_slice_manual_mapping_promotion",
        "reviewed_by": _REVIEWED_BY,
        "reviewed_at": _REVIEWED_AT,
        "verified_mappings": mappings,
        "deferred_scopes": [
            {
                "decision": "deferred",
                "endpoint_kind": "combatants_info",
                "scope": "/combatants/*",
                "reason": "separate review",
            },
            {
                "decision": "deferred",
                "endpoint_kind": "combatants_info",
                "scope": "/combatants/*/ci_resolved",
                "reason": "separate review",
            },
            {
                "decision": "deferred",
                "endpoint_kind": "combatants_info",
                "scope": "/combatants/*/ci_resolved/specialization",
                "reason": "separate review",
            },
        ],
        "decision_boundary": {
            "status": "verified",
            "automatic_promotion": False,
            "manual_promotion_completed": True,
            "automatic_publication": False,
            "manual_publication_required": True,
            "ready_to_publish_verified_mappings": True,
            "mechanic_semantics_verified": False,
            "normalization_allowed": False,
        },
        "summary": {
            "mapping_count": 2,
            "field_contract_count": 54,
            "exact_raw_archive_count": 2,
            "deferred_scope_count": 3,
            "all_candidate_files_match_selection": True,
            "all_raw_archives_verified": True,
            "all_dry_run_counts_match": True,
            "cross_payload_consistent": True,
            "contains_source_scalar_values": False,
            "ready_to_publish_verified_mappings": True,
            "normalization_allowed": False,
        },
    }
    path = tmp_path / "promotion.json"
    _write_json(path, promotion)
    return path, staged


def test_publication_writes_exact_verified_mappings_and_is_idempotent(tmp_path):
    promotion_path, staged = _promotion_fixture(tmp_path)
    target = tmp_path / "config" / "mappings"

    receipt = publish_observed_report_slice_mappings(
        promotion_path,
        staged_mapping_dir=staged,
        target_mapping_dir=target,
    )

    assert receipt["summary"] == {
        "mapping_count": 2,
        "field_contract_count": 54,
        "all_staged_files_match_promotion": True,
        "all_targets_published": True,
        "contains_source_scalar_values": False,
        "selected_parser_normalization_allowed": True,
        "mechanic_semantics_verified": False,
        "full_report_slice_complete": False,
    }
    assert receipt["decision_boundary"]["status"] == "published"
    assert receipt["decision_boundary"]["selected_parser_normalization_allowed"] is True
    assert receipt["decision_boundary"]["aura_normalization_available"] is False
    assert all(row["already_current"] is False for row in receipt["published_mappings"])
    assert (target / "coa_encounter_detail_v1.json").is_file()
    assert (target / "coa_report_detail_v1.json").is_file()

    repeated = publish_observed_report_slice_mappings(
        promotion_path,
        staged_mapping_dir=staged,
        target_mapping_dir=target,
    )
    assert all(row["already_current"] is True for row in repeated["published_mappings"])


def test_publication_rejects_changed_staged_mapping(tmp_path):
    promotion_path, staged = _promotion_fixture(tmp_path)
    staged_path = staged / "coa_report_detail_v1.json"
    changed = json.loads(staged_path.read_text(encoding="utf-8"))
    changed["status"] = "candidate"
    _write_json(staged_path, changed)

    with pytest.raises(ValueError, match="staged verified mapping does not match promotion"):
        publish_observed_report_slice_mappings(
            promotion_path,
            staged_mapping_dir=staged,
            target_mapping_dir=tmp_path / "target",
        )


def test_publication_rejects_conflicting_target(tmp_path):
    promotion_path, staged = _promotion_fixture(tmp_path)
    target = tmp_path / "target"
    _write_json(target / "coa_report_detail_v1.json", {"unexpected": True})

    with pytest.raises(ValueError, match="publication target already differs"):
        publish_observed_report_slice_mappings(
            promotion_path,
            staged_mapping_dir=staged,
            target_mapping_dir=target,
        )


def test_publication_rejects_promoted_mechanic_semantics(tmp_path):
    promotion_path, staged = _promotion_fixture(tmp_path)
    promotion = json.loads(promotion_path.read_text(encoding="utf-8"))
    promotion["verified_mappings"][0]["mapping"]["mechanic_semantics_verified"] = True
    _write_json(promotion_path, promotion)

    with pytest.raises(ValueError, match="mechanics boundary changed"):
        publish_observed_report_slice_mappings(
            promotion_path,
            staged_mapping_dir=staged,
            target_mapping_dir=tmp_path / "target",
        )
