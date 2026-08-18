from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from .report_slice_mapping_validation import (
    validate_observed_report_slice_candidate_mappings,
)

_PROMOTION_SCHEMA_VERSION = 1
_SELECTION_KIND = "observed_report_slice_field_selection"
_VALIDATION_KIND = "observed_report_slice_candidate_mapping_validation"
_EXPECTED_MAPPING_FILES = {
    "coa-report-detail-v1": "coa_report_detail_v1.json",
    "coa-encounter-detail-v1": "coa_encounter_detail_v1.json",
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
        raise ValueError(f"mapping promotion field {field_name} must be an object")
    return value


def _required_list(value: object, field_name: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"mapping promotion field {field_name} must be an array")
    return value


def _required_string(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"mapping promotion field {field_name} must be a non-empty string")
    prepared = value.strip()
    if "\n" in prepared or "\r" in prepared:
        raise ValueError(f"mapping promotion field {field_name} must be one line")
    return prepared


def _reviewed_at(value: object) -> str:
    prepared = _required_string(value, "reviewed_at")
    parse_value = prepared[:-1] + "+00:00" if prepared.endswith("Z") else prepared
    try:
        parsed = datetime.fromisoformat(parse_value)
    except ValueError as error:
        raise ValueError("mapping promotion reviewed_at must be ISO-8601") from error
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("mapping promotion reviewed_at must include a timezone offset")
    return prepared


def _without_generated_at(payload: Mapping[str, Any]) -> dict[str, Any]:
    prepared = deepcopy(dict(payload))
    prepared.pop("generated_at", None)
    return prepared


def _validate_validation_packet(
    submitted: Mapping[str, Any],
    recomputed: Mapping[str, Any],
) -> dict[str, dict[str, Any]]:
    if submitted.get("schema_version") != 1:
        raise ValueError("unsupported report slice candidate validation schema version")
    if submitted.get("validation_kind") != _VALIDATION_KIND:
        raise ValueError("unexpected report slice candidate validation kind")
    if _without_generated_at(submitted) != _without_generated_at(recomputed):
        raise ValueError("submitted candidate validation does not match exact recomputed validation")

    summary = _required_object(submitted.get("summary"), "validation.summary")
    expected_summary = {
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
    }
    for field_name, expected in expected_summary.items():
        if summary.get(field_name) != expected:
            raise ValueError(f"candidate validation summary mismatch: {field_name}")

    boundary = _required_object(submitted.get("decision_boundary"), "validation.decision_boundary")
    expected_boundary = {
        "status": "candidate",
        "automatic_promotion": False,
        "can_promote": False,
        "ready_for_manual_promotion": True,
        "manual_promotion_required": True,
        "semantic_verification_required": True,
        "normalization_allowed": False,
    }
    for field_name, expected in expected_boundary.items():
        if boundary.get(field_name) != expected:
            raise ValueError(f"candidate validation boundary mismatch: {field_name}")

    cross_checks = _required_object(submitted.get("cross_payload_checks"), "cross_payload_checks")
    if not cross_checks or any(value is not True for value in cross_checks.values()):
        raise ValueError("candidate validation cross-payload checks are incomplete")

    rows: dict[str, dict[str, Any]] = {}
    for raw_row in _required_list(submitted.get("mappings"), "validation.mappings"):
        row = _required_object(raw_row, "validation.mappings[]")
        mapping_id = _required_string(row.get("mapping_id"), "mapping_id")
        if mapping_id not in _EXPECTED_MAPPING_FILES or mapping_id in rows:
            raise ValueError(f"unsupported or duplicated validated mapping: {mapping_id}")
        if row.get("mapping_file") != _EXPECTED_MAPPING_FILES[mapping_id]:
            raise ValueError(f"validated mapping file mismatch for {mapping_id}")
        if row.get("status") != "candidate":
            raise ValueError(f"validated mapping {mapping_id} must remain candidate")
        for field_name in (
            "candidate_file_matches_selection",
            "raw_archive_verified",
            "dry_run_counts_match",
        ):
            if row.get(field_name) is not True:
                raise ValueError(f"validated mapping gate failed for {mapping_id}: {field_name}")
        rows[mapping_id] = row

    if set(rows) != set(_EXPECTED_MAPPING_FILES):
        raise ValueError("validated mapping set mismatch")
    return rows


def _load_candidate_mappings(
    selection_path: Path,
    *,
    mapping_dir: Path,
) -> list[dict[str, Any]]:
    selection = _load_object(selection_path, "report slice field selection")
    if selection.get("schema_version") != 1:
        raise ValueError("unsupported report slice field selection schema version")
    if selection.get("selection_kind") != _SELECTION_KIND:
        raise ValueError("unexpected report slice field selection kind")

    rows: dict[str, dict[str, Any]] = {}
    for raw_row in _required_list(selection.get("mappings"), "selection.mappings"):
        row = _required_object(raw_row, "selection.mappings[]")
        mapping = _required_object(row.get("mapping"), "selection.mappings[].mapping")
        mapping_id = _required_string(mapping.get("mapping_id"), "mapping_id")
        if mapping_id not in _EXPECTED_MAPPING_FILES or mapping_id in rows:
            raise ValueError(f"unsupported or duplicated selected mapping: {mapping_id}")
        mapping_file = _required_string(row.get("mapping_file"), "mapping_file")
        if mapping_file != _EXPECTED_MAPPING_FILES[mapping_id]:
            raise ValueError(f"selected mapping file mismatch for {mapping_id}")
        if mapping.get("status") != "candidate":
            raise ValueError(f"selected mapping {mapping_id} must remain candidate")
        candidate_path = mapping_dir / mapping_file
        candidate = _load_object(candidate_path, f"candidate mapping {mapping_id}")
        if candidate != mapping:
            raise ValueError(f"candidate mapping file changed after selection: {mapping_id}")
        rows[mapping_id] = {
            "mapping_id": mapping_id,
            "mapping_file": mapping_file,
            "mapping": mapping,
        }

    if set(rows) != set(_EXPECTED_MAPPING_FILES):
        raise ValueError("selected mapping set mismatch")
    return [rows[mapping_id] for mapping_id in sorted(rows)]


def _promoted_mapping(
    candidate: Mapping[str, Any],
    *,
    reviewed_by: str,
    reviewed_at: str,
    validation_name: str,
) -> dict[str, Any]:
    promoted = deepcopy(dict(candidate))
    promoted["status"] = "verified"
    promoted["reviewed_by"] = reviewed_by
    promoted["reviewed_at"] = reviewed_at
    promoted["promotion_validation_kind"] = _VALIDATION_KIND
    promoted["promotion_validation_name"] = validation_name
    promoted["verification_scope"] = (
        "parser_schema_raw_archive_dry_run_and_cross_payload_linkage_only"
    )
    promoted["mechanic_semantics_verified"] = False

    contracts = _required_list(promoted.get("field_contracts"), "field_contracts")
    for raw_contract in contracts:
        contract = _required_object(raw_contract, "field_contracts[]")
        if contract.get("semantic_status") != "reviewed_candidate":
            raise ValueError("candidate field contract has an unexpected semantic status")
        contract["semantic_status"] = "verified_parser_field"

    notes = _required_list(promoted.get("review_notes"), "review_notes")
    if any(not isinstance(note, str) or not note for note in notes):
        raise ValueError("mapping review_notes must contain non-empty strings")
    notes.extend(
        [
            "Manual promotion verifies selectors, JSON types, nullability, exact raw archive identity, dry-run counts and cross-payload linkage.",
            "Promotion does not verify gameplay mechanics, class/spec codebooks, combatants-info enrichment or aura semantics.",
        ]
    )
    return promoted


def promote_observed_report_slice_candidate_mappings(
    selection_path: Path,
    validation_path: Path,
    *,
    mapping_dir: Path,
    capture_path: Path,
    route_inventory_path: Path,
    raw_root: Path,
    reviewed_by: str,
    reviewed_at: str,
) -> dict[str, Any]:
    """Build verified mappings only after exact recomputation and explicit manual review metadata."""
    prepared_reviewer = _required_string(reviewed_by, "reviewed_by")
    prepared_reviewed_at = _reviewed_at(reviewed_at)

    recomputed = validate_observed_report_slice_candidate_mappings(
        selection_path,
        mapping_dir=mapping_dir,
        capture_path=capture_path,
        route_inventory_path=route_inventory_path,
        raw_root=raw_root,
    )
    submitted = _load_object(validation_path, "candidate mapping validation")
    validation_rows = _validate_validation_packet(submitted, recomputed)
    candidate_rows = _load_candidate_mappings(selection_path, mapping_dir=mapping_dir)

    verified_rows: list[dict[str, Any]] = []
    field_contract_count = 0
    for candidate_row in candidate_rows:
        mapping_id = candidate_row["mapping_id"]
        validation_row = validation_rows[mapping_id]
        promoted = _promoted_mapping(
            candidate_row["mapping"],
            reviewed_by=prepared_reviewer,
            reviewed_at=prepared_reviewed_at,
            validation_name=validation_path.name,
        )
        contracts = _required_list(promoted.get("field_contracts"), "field_contracts")
        field_contract_count += len(contracts)
        verified_rows.append(
            {
                "mapping_id": mapping_id,
                "mapping_file": candidate_row["mapping_file"],
                "mapping": promoted,
                "field_contract_count": len(contracts),
                "raw_archive_verified": validation_row["raw_archive_verified"],
                "dry_run_counts": validation_row["dry_run_counts"],
                "cross_payload_consistent": submitted["summary"]["cross_payload_consistent"],
            }
        )

    if field_contract_count != 54:
        raise ValueError("promoted field contract total mismatch")

    selection = _load_object(selection_path, "report slice field selection")
    deferred_scopes = deepcopy(
        _required_list(selection.get("deferred_scopes"), "deferred_scopes")
    )
    return {
        "schema_version": _PROMOTION_SCHEMA_VERSION,
        "promotion_kind": "observed_report_slice_manual_mapping_promotion",
        "generated_at": _generated_at(),
        "source_selection_name": selection_path.name,
        "source_validation_name": validation_path.name,
        "reviewed_by": prepared_reviewer,
        "reviewed_at": prepared_reviewed_at,
        "verified_mappings": verified_rows,
        "deferred_scopes": deferred_scopes,
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
            "mapping_count": len(verified_rows),
            "field_contract_count": field_contract_count,
            "exact_raw_archive_count": submitted["summary"]["exact_raw_archive_count"],
            "deferred_scope_count": len(deferred_scopes),
            "all_candidate_files_match_selection": True,
            "all_raw_archives_verified": True,
            "all_dry_run_counts_match": True,
            "cross_payload_consistent": True,
            "contains_source_scalar_values": False,
            "ready_to_publish_verified_mappings": True,
            "normalization_allowed": False,
        },
    }
