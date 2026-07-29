from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from coa_workbench.collector import report_slice_mapping_promotion as promotion_module
from coa_workbench.collector.report_slice_mapping_promotion import (
    promote_observed_report_slice_candidate_mappings,
)


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _candidate_mapping(mapping_id: str, field_count: int) -> dict[str, object]:
    return {
        "mapping_schema_version": 1,
        "mapping_id": mapping_id,
        "source_code": "coa_ascension_logs",
        "mapping_version": "1",
        "status": "candidate",
        "entities": {},
        "event_type_map": {},
        "field_contracts": [
            {
                "entity": "fixture",
                "canonical_field": f"field_{index}",
                "expression": f"@item/field_{index}",
                "semantic_status": "reviewed_candidate",
            }
            for index in range(field_count)
        ],
        "review_notes": ["Fixture candidate mapping."],
    }


def _fixture(tmp_path: Path) -> dict[str, object]:
    report_mapping = _candidate_mapping("coa-report-detail-v1", 19)
    encounter_mapping = _candidate_mapping("coa-encounter-detail-v1", 35)
    mapping_dir = tmp_path / "candidate-mappings"
    _write_json(mapping_dir / "coa_report_detail_v1.json", report_mapping)
    _write_json(mapping_dir / "coa_encounter_detail_v1.json", encounter_mapping)

    selection = {
        "schema_version": 1,
        "selection_kind": "observed_report_slice_field_selection",
        "mappings": [
            {
                "mapping_file": "coa_report_detail_v1.json",
                "mapping": report_mapping,
                "selected_field_contract_count": 19,
            },
            {
                "mapping_file": "coa_encounter_detail_v1.json",
                "mapping": encounter_mapping,
                "selected_field_contract_count": 35,
            },
        ],
        "deferred_scopes": [
            {
                "endpoint_kind": "combatants_info",
                "scope": "/combatants/*",
                "decision": "deferred",
                "reason": "fixture",
            },
            {
                "endpoint_kind": "combatants_info",
                "scope": "/combatants/*/ci_resolved",
                "decision": "deferred",
                "reason": "fixture",
            },
            {
                "endpoint_kind": "combatants_info",
                "scope": "/combatants/*/ci_resolved/specialization",
                "decision": "deferred",
                "reason": "fixture",
            },
        ],
    }
    selection_path = tmp_path / "field-selection.json"
    _write_json(selection_path, selection)

    validation = {
        "schema_version": 1,
        "validation_kind": "observed_report_slice_candidate_mapping_validation",
        "generated_at": "2026-07-29T15:27:38Z",
        "mappings": [
            {
                "mapping_id": "coa-encounter-detail-v1",
                "mapping_file": "coa_encounter_detail_v1.json",
                "status": "candidate",
                "candidate_file_matches_selection": True,
                "raw_archive_verified": True,
                "dry_run_counts_match": True,
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
                "status": "candidate",
                "candidate_file_matches_selection": True,
                "raw_archive_verified": True,
                "dry_run_counts_match": True,
                "dry_run_counts": {
                    "reports": 1,
                    "encounters": 14,
                    "actors": 0,
                    "participants": 0,
                    "aura_events": 0,
                    "rejects": 0,
                },
            },
        ],
        "cross_payload_checks": {
            "exact_encounter_present_in_report_list": True,
            "participant_actor_references_resolved": True,
            "participant_encounter_references_resolved": True,
            "report_id_consistent": True,
            "single_report_id_in_each_payload": True,
        },
        "decision_boundary": {
            "status": "candidate",
            "automatic_promotion": False,
            "can_promote": False,
            "ready_for_manual_promotion": True,
            "manual_promotion_required": True,
            "semantic_verification_required": True,
            "normalization_allowed": False,
        },
        "summary": {
            "mapping_count": 2,
            "exact_raw_archive_count": 2,
            "field_contract_count": 54,
            "all_candidate_files_match_selection": True,
            "all_raw_archives_verified": True,
            "all_dry_run_counts_match": True,
            "cross_payload_consistent": True,
            "contains_source_scalar_values": False,
            "ready_for_manual_promotion": True,
            "normalization_allowed": False,
        },
    }
    validation_path = tmp_path / "validation.json"
    _write_json(validation_path, validation)
    return {
        "selection_path": selection_path,
        "validation_path": validation_path,
        "mapping_dir": mapping_dir,
        "validation": validation,
    }


def _promote(
    fixture: dict[str, object],
    monkeypatch: pytest.MonkeyPatch,
    *,
    reviewed_at: str = "2026-07-29T18:28:00+03:00",
) -> dict[str, object]:
    validation = deepcopy(fixture["validation"])
    monkeypatch.setattr(
        promotion_module,
        "validate_observed_report_slice_candidate_mappings",
        lambda *args, **kwargs: deepcopy(validation),
    )
    return promote_observed_report_slice_candidate_mappings(
        fixture["selection_path"],
        fixture["validation_path"],
        mapping_dir=fixture["mapping_dir"],
        capture_path=Path("capture.json"),
        route_inventory_path=Path("routes.json"),
        raw_root=Path("raw"),
        reviewed_by="GunsPojoshe (operator), OpenAI-assisted review",
        reviewed_at=reviewed_at,
    )


def test_manual_promotion_builds_two_verified_mappings(tmp_path, monkeypatch):
    fixture = _fixture(tmp_path)

    promotion = _promote(fixture, monkeypatch)

    assert promotion["summary"] == {
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
    }
    assert promotion["decision_boundary"] == {
        "status": "verified",
        "automatic_promotion": False,
        "manual_promotion_completed": True,
        "automatic_publication": False,
        "manual_publication_required": True,
        "ready_to_publish_verified_mappings": True,
        "mechanic_semantics_verified": False,
        "normalization_allowed": False,
    }
    assert {row["mapping_id"] for row in promotion["verified_mappings"]} == {
        "coa-report-detail-v1",
        "coa-encounter-detail-v1",
    }
    assert all(row["mapping"]["status"] == "verified" for row in promotion["verified_mappings"])
    assert all(
        contract["semantic_status"] == "verified_parser_field"
        for row in promotion["verified_mappings"]
        for contract in row["mapping"]["field_contracts"]
    )
    assert all(
        row["mapping"]["mechanic_semantics_verified"] is False
        for row in promotion["verified_mappings"]
    )


def test_manual_promotion_rejects_changed_validation_packet(tmp_path, monkeypatch):
    fixture = _fixture(tmp_path)
    submitted = json.loads(fixture["validation_path"].read_text(encoding="utf-8"))
    submitted["summary"]["mapping_count"] = 3
    _write_json(fixture["validation_path"], submitted)

    with pytest.raises(ValueError, match="does not match exact recomputed validation"):
        _promote(fixture, monkeypatch)


def test_manual_promotion_rejects_changed_candidate_file(tmp_path, monkeypatch):
    fixture = _fixture(tmp_path)
    candidate_path = fixture["mapping_dir"] / "coa_report_detail_v1.json"
    candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
    candidate["status"] = "verified"
    _write_json(candidate_path, candidate)

    with pytest.raises(ValueError, match="candidate mapping file changed after selection"):
        _promote(fixture, monkeypatch)


def test_manual_promotion_requires_timezone_aware_review_timestamp(tmp_path, monkeypatch):
    fixture = _fixture(tmp_path)

    with pytest.raises(ValueError, match="must include a timezone offset"):
        _promote(fixture, monkeypatch, reviewed_at="2026-07-29T18:28:00")
