from __future__ import annotations

import json
from pathlib import Path

import pytest

from coa_workbench.collector import report_slice_field_selection as selection_module
from coa_workbench.collector.report_slice_field_selection import (
    select_observed_report_slice_fields,
)
from coa_workbench.normalizer.canonical import NormalizationMapping


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _review_fixture(tmp_path: Path) -> Path:
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


def _load(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_field_selection_builds_two_candidate_mappings(tmp_path):
    path = _review_fixture(tmp_path)

    selection = select_observed_report_slice_fields(path)

    assert selection["summary"] == {
        "mapping_count": 2,
        "selected_scope_count": 4,
        "selected_field_contract_count": 54,
        "deferred_scope_count": 3,
        "contains_source_scalar_values": False,
        "all_source_scopes_consistent": True,
        "candidate_mapping_files_ready": True,
        "normalization_allowed": False,
    }
    assert selection["decision_boundary"] == {
        "status": "candidate",
        "automatic_promotion": False,
        "can_promote": False,
        "semantic_verification_required": True,
        "normalization_allowed": False,
        "manual_mapping_review_required": True,
    }

    mappings = {row["mapping"]["mapping_id"]: row for row in selection["mappings"]}
    assert mappings["coa-report-detail-v1"]["selected_field_contract_count"] == 19
    assert mappings["coa-encounter-detail-v1"]["selected_field_contract_count"] == 35
    assert set(mappings["coa-report-detail-v1"]["mapping"]["entities"]) == {
        "reports",
        "encounters",
    }
    assert set(mappings["coa-encounter-detail-v1"]["mapping"]["entities"]) == {
        "reports",
        "encounters",
        "actors",
        "participants",
    }
    assert all(row["mapping"]["status"] == "candidate" for row in mappings.values())
    assert all(
        not NormalizationMapping.from_dict(row["mapping"]).production_ready
        for row in mappings.values()
    )
    assert {
        (row["endpoint_kind"], row["scope"]) for row in selection["deferred_scopes"]
    } == {
        ("combatants_info", "/combatants/*"),
        ("combatants_info", "/combatants/*/ci_resolved"),
        ("combatants_info", "/combatants/*/ci_resolved/specialization"),
    }


def test_field_selection_rejects_missing_selected_field(tmp_path):
    path = _review_fixture(tmp_path)
    review = _load(path)
    report_scope = next(
        scope
        for scope in review["scopes"]
        if scope["endpoint_kind"] == "report_detail" and scope["scope"] == "/report"
    )
    report_scope["direct_fields"] = [
        field for field in report_scope["direct_fields"] if field["path"] != "/report/title"
    ]
    _write_json(path, review)

    with pytest.raises(ValueError, match="selected review path not found"):
        select_observed_report_slice_fields(path)


def test_field_selection_rejects_selected_type_change(tmp_path):
    path = _review_fixture(tmp_path)
    review = _load(path)
    report_scope = next(
        scope
        for scope in review["scopes"]
        if scope["endpoint_kind"] == "report_detail" and scope["scope"] == "/report"
    )
    title = next(field for field in report_scope["direct_fields"] if field["path"] == "/report/title")
    title["types"] = ["integer"]
    _write_json(path, review)

    with pytest.raises(ValueError, match="selected field type mismatch"):
        select_observed_report_slice_fields(path)


def test_field_selection_rejects_privacy_gate_change(tmp_path):
    path = _review_fixture(tmp_path)
    review = _load(path)
    review["summary"]["contains_source_scalar_values"] = True
    _write_json(path, review)

    with pytest.raises(ValueError, match="contains_source_scalar_values"):
        select_observed_report_slice_fields(path)


def test_field_selection_rejects_payload_hash_change(tmp_path):
    path = _review_fixture(tmp_path)
    review = _load(path)
    review["scopes"][0]["payload_hash"] = "f" * 64
    _write_json(path, review)

    with pytest.raises(ValueError, match="payload hash mismatch"):
        select_observed_report_slice_fields(path)
