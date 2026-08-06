from __future__ import annotations

import gzip
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from coa_workbench.normalizer.canonical import NormalizationMapping, normalize_payload

from .report_slice_review import review_observed_report_slice_capture

_VALIDATION_SCHEMA_VERSION = 1
_SELECTION_KIND = "observed_report_slice_field_selection"
_EXPECTED_MAPPINGS = {
    "coa-report-detail-v1": {
        "mapping_file": "coa_report_detail_v1.json",
        "route_template": "/api/reports/{template}",
        "endpoint_kind": "report_detail",
        "field_contract_count": 19,
        "entity_names": {"reports", "encounters"},
        "expected_counts": {
            "reports": 1,
            "encounters": 14,
            "actors": 0,
            "participants": 0,
            "aura_events": 0,
            "rejects": 0,
        },
    },
    "coa-encounter-detail-v1": {
        "mapping_file": "coa_encounter_detail_v1.json",
        "route_template": "/api/reports/{template}/encounters/{template}",
        "endpoint_kind": "encounter_detail",
        "field_contract_count": 35,
        "entity_names": {"reports", "encounters", "actors", "participants"},
        "expected_counts": {
            "reports": 1,
            "encounters": 1,
            "actors": 31,
            "participants": 31,
            "aura_events": 0,
            "rejects": 0,
        },
    },
}
_EXPECTED_DEFERRED_SCOPES = {
    ("combatants_info", "/combatants/*"),
    ("combatants_info", "/combatants/*/ci_resolved"),
    ("combatants_info", "/combatants/*/ci_resolved/specialization"),
}


def _generated_at() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _load_object(path: Path, description: str) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{description} must contain a JSON object")
    return payload


def _required_object(value: object, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"mapping validation field {field_name} must be an object")
    return value


def _required_list(value: object, field_name: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"mapping validation field {field_name} must be an array")
    return value


def _required_string(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"mapping validation field {field_name} must be a non-empty string")
    return value


def _required_boolean(value: object, field_name: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"mapping validation field {field_name} must be a boolean")
    return value


def _required_integer(value: object, field_name: str, *, minimum: int = 0) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < minimum:
        raise ValueError(
            f"mapping validation field {field_name} must be an integer greater than or equal to "
            f"{minimum}"
        )
    return value


def _required_sha256(value: object, field_name: str) -> str:
    prepared = _required_string(value, field_name).casefold()
    if len(prepared) != 64 or any(char not in "0123456789abcdef" for char in prepared):
        raise ValueError(f"mapping validation field {field_name} must be a SHA-256 digest")
    return prepared


def _validate_selection(selection: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    if selection.get("schema_version") != 1:
        raise ValueError("unsupported report slice field selection schema version")
    if selection.get("selection_kind") != _SELECTION_KIND:
        raise ValueError("unexpected report slice field selection kind")

    summary = _required_object(selection.get("summary"), "summary")
    expected_summary = {
        "mapping_count": 2,
        "selected_scope_count": 4,
        "selected_field_contract_count": 54,
        "deferred_scope_count": 3,
    }
    for field_name, expected in expected_summary.items():
        actual = _required_integer(summary.get(field_name), f"summary.{field_name}")
        if actual != expected:
            raise ValueError(f"report slice field selection {field_name} mismatch")
    if _required_boolean(
        summary.get("all_source_scopes_consistent"),
        "summary.all_source_scopes_consistent",
    ) is not True:
        raise ValueError("report slice selected source scopes are not consistent")
    if _required_boolean(
        summary.get("candidate_mapping_files_ready"),
        "summary.candidate_mapping_files_ready",
    ) is not True:
        raise ValueError("report slice candidate mapping files are not ready")
    if _required_boolean(
        summary.get("contains_source_scalar_values"),
        "summary.contains_source_scalar_values",
    ) is not False:
        raise ValueError("report slice field selection privacy gate failed")
    if _required_boolean(
        summary.get("normalization_allowed"),
        "summary.normalization_allowed",
    ) is not False:
        raise ValueError("report slice field selection enabled normalization")

    boundary = _required_object(selection.get("decision_boundary"), "decision_boundary")
    if boundary.get("status") != "candidate":
        raise ValueError("report slice field selection must remain candidate")
    expected_boundary = {
        "automatic_promotion": False,
        "can_promote": False,
        "semantic_verification_required": True,
        "normalization_allowed": False,
        "manual_mapping_review_required": True,
    }
    for field_name, expected in expected_boundary.items():
        actual = _required_boolean(boundary.get(field_name), f"decision_boundary.{field_name}")
        if actual is not expected:
            raise ValueError(f"report slice field selection boundary mismatch: {field_name}")

    deferred_rows = _required_list(selection.get("deferred_scopes"), "deferred_scopes")
    deferred_scopes: set[tuple[str, str]] = set()
    for raw_row in deferred_rows:
        row = _required_object(raw_row, "deferred_scopes[]")
        if row.get("decision") != "deferred":
            raise ValueError("report slice deferred scope has an unexpected decision")
        _required_string(row.get("reason"), "deferred_scopes[].reason")
        deferred_scopes.add(
            (
                _required_string(row.get("endpoint_kind"), "deferred_scopes[].endpoint_kind"),
                _required_string(row.get("scope"), "deferred_scopes[].scope"),
            )
        )
    if deferred_scopes != _EXPECTED_DEFERRED_SCOPES:
        raise ValueError("report slice deferred scope set mismatch")

    mapping_rows = _required_list(selection.get("mappings"), "mappings")
    mappings: dict[str, dict[str, Any]] = {}
    selected_contract_count = 0
    for raw_row in mapping_rows:
        row = _required_object(raw_row, "mappings[]")
        mapping = _required_object(row.get("mapping"), "mappings[].mapping")
        mapping_id = _required_string(mapping.get("mapping_id"), "mapping_id")
        if mapping_id not in _EXPECTED_MAPPINGS or mapping_id in mappings:
            raise ValueError(f"unsupported or duplicated report slice mapping: {mapping_id}")
        expected = _EXPECTED_MAPPINGS[mapping_id]
        if row.get("mapping_file") != expected["mapping_file"]:
            raise ValueError(f"report slice mapping file mismatch for {mapping_id}")
        if mapping.get("status") != "candidate":
            raise ValueError(f"report slice mapping {mapping_id} must remain candidate")
        if mapping.get("route_template") != expected["route_template"]:
            raise ValueError(f"report slice mapping route mismatch for {mapping_id}")
        _required_sha256(mapping.get("reviewed_payload_hash"), "reviewed_payload_hash")
        _required_sha256(mapping.get("schema_fingerprint"), "schema_fingerprint")
        if mapping.get("source_code") != "coa_ascension_logs":
            raise ValueError(f"report slice mapping source mismatch for {mapping_id}")
        if mapping.get("provenance_type") != "upstream_derived":
            raise ValueError(f"report slice mapping provenance mismatch for {mapping_id}")
        if mapping.get("event_type_map") != {}:
            raise ValueError(f"report slice mapping {mapping_id} must not define aura event semantics")

        contract_count = _required_integer(
            row.get("selected_field_contract_count"),
            "selected_field_contract_count",
            minimum=1,
        )
        if contract_count != expected["field_contract_count"]:
            raise ValueError(f"report slice field contract count mismatch for {mapping_id}")
        contracts = _required_list(mapping.get("field_contracts"), "field_contracts")
        if len(contracts) != contract_count:
            raise ValueError(f"report slice embedded field contract count mismatch for {mapping_id}")
        entities = _required_object(mapping.get("entities"), "entities")
        if set(entities) != expected["entity_names"]:
            raise ValueError(f"report slice entity set mismatch for {mapping_id}")

        contract_fields: dict[tuple[str, str], str] = {}
        for raw_contract in contracts:
            contract = _required_object(raw_contract, "field_contracts[]")
            entity = _required_string(contract.get("entity"), "field_contracts[].entity")
            canonical_field = _required_string(
                contract.get("canonical_field"),
                "field_contracts[].canonical_field",
            )
            expression = _required_string(contract.get("expression"), "field_contracts[].expression")
            if contract.get("semantic_status") != "reviewed_candidate":
                raise ValueError("report slice field contract is not a reviewed candidate")
            key = (entity, canonical_field)
            if key in contract_fields:
                raise ValueError(f"duplicated report slice field contract: {key}")
            contract_fields[key] = expression

        entity_field_count = 0
        for entity_name, raw_entity in entities.items():
            entity = _required_object(raw_entity, f"entities.{entity_name}")
            fields = _required_object(entity.get("fields"), f"entities.{entity_name}.fields")
            entity_field_count += len(fields)
            for field_name, expression in fields.items():
                if contract_fields.get((entity_name, field_name)) != expression:
                    raise ValueError(
                        f"report slice entity field does not match its contract: "
                        f"{entity_name}.{field_name}"
                    )
        if entity_field_count != contract_count or len(contract_fields) != contract_count:
            raise ValueError(f"report slice entity field total mismatch for {mapping_id}")

        selected_contract_count += contract_count
        mappings[mapping_id] = {
            "mapping_file": row["mapping_file"],
            "mapping": mapping,
            "expected": expected,
        }

    if set(mappings) != set(_EXPECTED_MAPPINGS):
        raise ValueError("report slice mapping set mismatch")
    if selected_contract_count != 54:
        raise ValueError("report slice selected field contract total mismatch")
    return mappings


def _load_archived_payload(endpoint: Mapping[str, Any], *, raw_root: Path) -> Any:
    root = raw_root.resolve()
    relative_path = _required_string(endpoint.get("payload_path"), "payload_path")
    path = (root / relative_path).resolve()
    if not path.is_relative_to(root) or not path.is_file() or not path.name.endswith(".json.gz"):
        raise ValueError("report slice reviewed payload path is not a gzip JSON archive below raw-root")
    body = gzip.decompress(path.read_bytes())
    expected_hash = _required_sha256(endpoint.get("payload_hash"), "payload_hash")
    if hashlib.sha256(body).hexdigest() != expected_hash:
        raise ValueError("report slice reviewed payload hash changed after structural review")
    return json.loads(body)


def _dry_run_mapping(mapping: Mapping[str, Any], payload: Any) -> Any:
    promoted = dict(mapping)
    promoted["status"] = "verified"
    contract = NormalizationMapping.from_dict(promoted)
    return normalize_payload(
        payload,
        contract,
        schema_fingerprint=_required_sha256(mapping.get("schema_fingerprint"), "schema_fingerprint"),
    )


def validate_observed_report_slice_candidate_mappings(
    selection_path: Path,
    *,
    mapping_dir: Path,
    capture_path: Path,
    route_inventory_path: Path,
    raw_root: Path,
) -> dict[str, Any]:
    """Validate exact candidate mappings with in-memory dry runs; never promote files."""
    selection = _load_object(selection_path, "report slice field selection")
    mappings = _validate_selection(selection)
    structural_review = review_observed_report_slice_capture(
        capture_path,
        route_inventory_path=route_inventory_path,
        raw_root=raw_root,
    )
    endpoints = {
        _required_string(row.get("endpoint_kind"), "endpoints[].endpoint_kind"): row
        for raw_row in _required_list(structural_review.get("endpoints"), "endpoints")
        for row in [_required_object(raw_row, "endpoints[]")]
    }

    batches: dict[str, Any] = {}
    validation_rows: list[dict[str, Any]] = []
    aggregate_counts = {
        "reports": 0,
        "encounters": 0,
        "actors": 0,
        "participants": 0,
        "aura_events": 0,
        "rejects": 0,
    }

    for mapping_id in sorted(mappings):
        row = mappings[mapping_id]
        embedded_mapping = row["mapping"]
        expected = row["expected"]
        candidate_path = mapping_dir / row["mapping_file"]
        candidate_mapping = _load_object(candidate_path, f"candidate mapping {mapping_id}")
        if candidate_mapping != embedded_mapping:
            raise ValueError(f"candidate mapping file does not match field selection: {mapping_id}")

        endpoint = endpoints.get(expected["endpoint_kind"])
        if endpoint is None:
            raise ValueError(f"structural review endpoint is missing: {expected['endpoint_kind']}")
        if endpoint.get("route_template") != embedded_mapping.get("route_template"):
            raise ValueError(f"candidate mapping route does not match structural review: {mapping_id}")
        if endpoint.get("payload_hash") != embedded_mapping.get("reviewed_payload_hash"):
            raise ValueError(f"candidate mapping payload hash does not match structural review: {mapping_id}")
        if endpoint.get("schema_fingerprint") != embedded_mapping.get("schema_fingerprint"):
            raise ValueError(
                f"candidate mapping fingerprint does not match structural review: {mapping_id}"
            )

        payload = _load_archived_payload(endpoint, raw_root=raw_root)
        batch = _dry_run_mapping(embedded_mapping, payload)
        counts = batch.counts()
        if counts != expected["expected_counts"]:
            raise ValueError(
                f"candidate mapping dry-run counts mismatch for {mapping_id}: "
                f"expected={expected['expected_counts']} actual={counts}"
            )
        for name, count in counts.items():
            aggregate_counts[name] += count
        batches[mapping_id] = batch
        validation_rows.append(
            {
                "mapping_id": mapping_id,
                "mapping_file": row["mapping_file"],
                "status": "candidate",
                "route_template": embedded_mapping["route_template"],
                "reviewed_payload_hash": embedded_mapping["reviewed_payload_hash"],
                "schema_fingerprint": embedded_mapping["schema_fingerprint"],
                "field_contract_count": expected["field_contract_count"],
                "entity_count": len(embedded_mapping["entities"]),
                "candidate_file_matches_selection": True,
                "raw_archive_verified": True,
                "dry_run_counts": counts,
                "expected_counts": dict(expected["expected_counts"]),
                "dry_run_counts_match": True,
            }
        )

    report_batch = batches["coa-report-detail-v1"]
    encounter_batch = batches["coa-encounter-detail-v1"]
    report_ids = {row["report_id"] for row in report_batch.reports}
    encounter_report_ids = {row["report_id"] for row in encounter_batch.reports}
    report_encounter_ids = {row["encounter_id"] for row in report_batch.encounters}
    exact_encounter_ids = {row["encounter_id"] for row in encounter_batch.encounters}
    actor_ids = {row["actor_id"] for row in encounter_batch.actors}

    cross_payload_checks = {
        "single_report_id_in_each_payload": len(report_ids) == 1 and len(encounter_report_ids) == 1,
        "report_id_consistent": report_ids == encounter_report_ids,
        "exact_encounter_present_in_report_list": len(exact_encounter_ids) == 1
        and exact_encounter_ids.issubset(report_encounter_ids),
        "participant_actor_references_resolved": all(
            row["actor_id"] in actor_ids for row in encounter_batch.participants
        ),
        "participant_encounter_references_resolved": all(
            row["encounter_id"] in exact_encounter_ids for row in encounter_batch.participants
        ),
    }
    failed_cross_checks = sorted(
        name for name, passed in cross_payload_checks.items() if not passed
    )
    if failed_cross_checks:
        raise ValueError(
            "report slice cross-payload validation failed: " + ", ".join(failed_cross_checks)
        )

    return {
        "schema_version": _VALIDATION_SCHEMA_VERSION,
        "validation_kind": "observed_report_slice_candidate_mapping_validation",
        "generated_at": _generated_at(),
        "source_selection_name": selection_path.name,
        "source_capture_name": capture_path.name,
        "mappings": validation_rows,
        "cross_payload_checks": cross_payload_checks,
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
            "mapping_count": len(validation_rows),
            "exact_raw_archive_count": len(validation_rows),
            "field_contract_count": sum(row["field_contract_count"] for row in validation_rows),
            "aggregate_dry_run_counts": aggregate_counts,
            "all_candidate_files_match_selection": True,
            "all_raw_archives_verified": True,
            "all_dry_run_counts_match": True,
            "cross_payload_consistent": True,
            "contains_source_scalar_values": False,
            "ready_for_manual_promotion": True,
            "normalization_allowed": False,
        },
    }
