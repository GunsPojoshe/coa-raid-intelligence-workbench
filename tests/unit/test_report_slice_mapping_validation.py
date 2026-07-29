from __future__ import annotations

import json
from pathlib import Path

import pytest

from coa_workbench.collector import report_slice_field_selection as selection_module
from coa_workbench.collector import report_slice_mapping_validation as validation_module
from coa_workbench.collector.report_slice_field_selection import (
    select_observed_report_slice_fields,
)
from coa_workbench.collector.report_slice_mapping_validation import (
    validate_observed_report_slice_candidate_mappings,
)


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _scope_review_path(tmp_path: Path) -> Path:
    fields_by_scope: dict[tuple[str, str], dict[str, dict[str, object]]] = {
        key: {} for key in selection_module._EXPECTED_SCOPES
    }
    for blueprint in selection_module._MAPPING_BLUEPRINTS:
        endpoint_kind = str(blueprint["endpoint_kind"])
        for entity in blueprint["entities"].values():
            for contract in entity["fields"]:
                key = (endpoint_kind, str(contract["review_scope"]))
                fields_by_scope[key][str(contract["review_path"])] = {
                    "name": str(contract["review_path"]).rsplit("/", 1)[-1],
                    "path": contract["review_path"],
                    "types": list(contract["types"]),
                    "type_counts": {value_type: 1 for value_type in contract["types"]},
                    "nullable": contract["nullable"],
                    "occurrence_count": 1,
                    "observed_on_all_scope_occurrences": True,
                    "is_array": "array" in contract["types"],
                    "is_object": "object" in contract["types"],
                }

    scopes = []
    for endpoint_kind, scope_path in sorted(selection_module._EXPECTED_SCOPES):
        endpoint = selection_module._ENDPOINTS[endpoint_kind]
        scopes.append(
            {
                "endpoint_kind": endpoint_kind,
                "route_template": endpoint["route_template"],
                "payload_hash": endpoint["payload_hash"],
                "schema_fingerprint": endpoint["schema_fingerprint"],
                "scope": scope_path,
                "review_label": "fixture",
                "review_status": "candidate",
                "semantic_status": "unverified_candidate",
                "manual_decision_required": True,
                "scope_shape": {
                    "path": scope_path,
                    "types": ["object"],
                    "nullable": False,
                    "occurrence_count": 1,
                    "is_array": False,
                    "is_object": True,
                },
                "direct_fields": list(fields_by_scope[(endpoint_kind, scope_path)].values()),
                "summary": {
                    "scope_occurrence_count": 1,
                    "direct_field_count": len(fields_by_scope[(endpoint_kind, scope_path)]),
                    "nullable_direct_field_count": 0,
                },
            }
        )

    path = tmp_path / "scope-review.json"
    _write_json(
        path,
        {
            "schema_version": 1,
            "review_kind": "observed_report_slice_scope_review",
            "scopes": scopes,
            "decision_boundary": {
                "status": "candidate",
                "automatic_scope_selection": False,
                "automatic_field_selection": False,
                "can_promote": False,
                "semantic_verification_required": True,
                "normalization_allowed": False,
            },
            "summary": {
                "endpoint_count": 3,
                "scope_candidate_count": 7,
                "direct_field_count": 120,
                "all_archives_consistent": True,
                "contains_source_scalar_values": False,
                "semantic_verification_required": True,
                "normalization_allowed": False,
                "ready_for_manual_field_selection": True,
            },
        },
    )
    return path


def _selection_fixture(tmp_path: Path) -> tuple[Path, Path, dict[str, object]]:
    selection = select_observed_report_slice_fields(_scope_review_path(tmp_path))
    selection_path = tmp_path / "selection.json"
    mapping_dir = tmp_path / "candidate-mappings"
    _write_json(selection_path, selection)
    for row in selection["mappings"]:
        _write_json(mapping_dir / row["mapping_file"], row["mapping"])
    return selection_path, mapping_dir, selection


def _report_payload() -> dict[str, object]:
    return {
        "report": {
            "id": 7,
            "title": "fixture",
            "created_at": "2026-01-01T00:00:00Z",
            "start_time": "2026-01-01T00:00:00Z",
            "end_time": "2026-01-01T01:00:00Z",
            "visibility": "public",
            "timezone": "UTC",
            "realm": "fixture",
            "zone": "fixture",
            "status": "ready",
            "has_telemetry": True,
        },
        "encounters": [
            {
                "id": 100 + index,
                "name": f"encounter-{index}",
                "start_time": "2026-01-01T00:00:00Z",
                "end_time": "2026-01-01T00:05:00Z",
                "success": index == 0,
                "kill_time": None,
                "wipe_percent": None,
            }
            for index in range(14)
        ],
    }


def _encounter_payload(*, report_id: int = 7) -> dict[str, object]:
    return {
        "encounter": {
            "id": 100,
            "report_id": report_id,
            "report_realm": "fixture",
            "name": "encounter-0",
            "start_time": "2026-01-01T00:00:00Z",
            "end_time": "2026-01-01T00:05:00Z",
            "success": True,
            "difficulty": "fixture",
            "duration_seconds": "300.0",
            "player_count": 31,
            "zone": "fixture",
            "is_boss_encounter": True,
            "boss_id": 1,
            "creature_id": 2,
            "trial_level": None,
            "wipe_percent": None,
        },
        "character_stats": [
            {
                "character_id": 1000 + index,
                "name": f"actor-{index}",
                "character_type": "Player",
                "class": None if index == 0 else "fixture",
                "spec": None if index == 0 else "fixture",
                "level": None,
                "encounter_id": 100,
                "avg_dps": float(index),
                "avg_hps": index,
                "damage_taken": index,
                "deaths": 0,
                "effective_healing": index,
                "encounter_duration": 300.0,
                "is_consolidated": False,
                "total_absorbs": index,
                "total_damage": index,
                "total_healing": index,
            }
            for index in range(31)
        ],
    }


def _structural_review() -> dict[str, object]:
    endpoints = []
    for endpoint_kind in ("report_detail", "encounter_detail", "combatants_info"):
        endpoint = selection_module._ENDPOINTS[endpoint_kind]
        endpoints.append(
            {
                "endpoint_kind": endpoint_kind,
                "route_template": endpoint["route_template"],
                "payload_hash": endpoint["payload_hash"],
                "schema_fingerprint": endpoint["schema_fingerprint"],
                "payload_path": f"{endpoint_kind}.json.gz",
            }
        )
    return {"endpoints": endpoints}


def _patch_sources(monkeypatch, *, encounter_report_id: int = 7) -> None:
    monkeypatch.setattr(
        validation_module,
        "review_observed_report_slice_capture",
        lambda *args, **kwargs: _structural_review(),
    )

    def load_payload(endpoint, *, raw_root):
        del raw_root
        if endpoint["endpoint_kind"] == "report_detail":
            return _report_payload()
        if endpoint["endpoint_kind"] == "encounter_detail":
            return _encounter_payload(report_id=encounter_report_id)
        raise AssertionError("combatants_info must not be loaded for deferred mappings")

    monkeypatch.setattr(validation_module, "_load_archived_payload", load_payload)


def test_candidate_mapping_validation_runs_exact_dry_runs(tmp_path, monkeypatch):
    selection_path, mapping_dir, _selection = _selection_fixture(tmp_path)
    _patch_sources(monkeypatch)

    result = validate_observed_report_slice_candidate_mappings(
        selection_path,
        mapping_dir=mapping_dir,
        capture_path=tmp_path / "capture.json",
        route_inventory_path=tmp_path / "inventory.json",
        raw_root=tmp_path / "raw",
    )

    assert result["summary"] == {
        "mapping_count": 2,
        "exact_raw_archive_count": 2,
        "field_contract_count": 54,
        "aggregate_dry_run_counts": {
            "reports": 2,
            "encounters": 15,
            "actors": 31,
            "participants": 31,
            "aura_events": 0,
            "rejects": 0,
        },
        "all_candidate_files_match_selection": True,
        "all_raw_archives_verified": True,
        "all_dry_run_counts_match": True,
        "cross_payload_consistent": True,
        "contains_source_scalar_values": False,
        "ready_for_manual_promotion": True,
        "normalization_allowed": False,
    }
    assert all(result["cross_payload_checks"].values())
    assert result["decision_boundary"]["ready_for_manual_promotion"] is True
    assert result["decision_boundary"]["can_promote"] is False
    assert result["decision_boundary"]["normalization_allowed"] is False


def test_candidate_mapping_validation_rejects_mapping_file_tampering(tmp_path, monkeypatch):
    selection_path, mapping_dir, selection = _selection_fixture(tmp_path)
    _patch_sources(monkeypatch)
    report_mapping = selection["mappings"][0]["mapping"]
    report_mapping["status"] = "verified"
    _write_json(mapping_dir / selection["mappings"][0]["mapping_file"], report_mapping)

    with pytest.raises(ValueError, match="does not match field selection"):
        validate_observed_report_slice_candidate_mappings(
            selection_path,
            mapping_dir=mapping_dir,
            capture_path=tmp_path / "capture.json",
            route_inventory_path=tmp_path / "inventory.json",
            raw_root=tmp_path / "raw",
        )


def test_candidate_mapping_validation_rejects_dry_run_count_change(tmp_path, monkeypatch):
    selection_path, mapping_dir, _selection = _selection_fixture(tmp_path)
    _patch_sources(monkeypatch)
    original = validation_module._load_archived_payload

    def load_short_report(endpoint, *, raw_root):
        payload = original(endpoint, raw_root=raw_root)
        if endpoint["endpoint_kind"] == "report_detail":
            payload["encounters"] = payload["encounters"][:-1]
        return payload

    monkeypatch.setattr(validation_module, "_load_archived_payload", load_short_report)

    with pytest.raises(ValueError, match="dry-run counts mismatch"):
        validate_observed_report_slice_candidate_mappings(
            selection_path,
            mapping_dir=mapping_dir,
            capture_path=tmp_path / "capture.json",
            route_inventory_path=tmp_path / "inventory.json",
            raw_root=tmp_path / "raw",
        )


def test_candidate_mapping_validation_rejects_cross_payload_report_mismatch(
    tmp_path, monkeypatch
):
    selection_path, mapping_dir, _selection = _selection_fixture(tmp_path)
    _patch_sources(monkeypatch, encounter_report_id=8)

    with pytest.raises(ValueError, match="cross-payload validation failed"):
        validate_observed_report_slice_candidate_mappings(
            selection_path,
            mapping_dir=mapping_dir,
            capture_path=tmp_path / "capture.json",
            route_inventory_path=tmp_path / "inventory.json",
            raw_root=tmp_path / "raw",
        )
