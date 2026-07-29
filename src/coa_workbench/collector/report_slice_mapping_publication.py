from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

from coa_workbench.normalizer.canonical import NormalizationMapping

_PUBLICATION_SCHEMA_VERSION = 1
_PROMOTION_KIND = "observed_report_slice_manual_mapping_promotion"
_EXPECTED_MAPPINGS = {
    "coa-encounter-detail-v1": {
        "mapping_file": "coa_encounter_detail_v1.json",
        "field_contract_count": 35,
        "dry_run_counts": {
            "reports": 1,
            "encounters": 1,
            "actors": 31,
            "participants": 31,
            "aura_events": 0,
            "rejects": 0,
        },
    },
    "coa-report-detail-v1": {
        "mapping_file": "coa_report_detail_v1.json",
        "field_contract_count": 19,
        "dry_run_counts": {
            "reports": 1,
            "encounters": 14,
            "actors": 0,
            "participants": 0,
            "aura_events": 0,
            "rejects": 0,
        },
    },
}


def _load_object(path: Path, description: str) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{description} must contain a JSON object")
    return payload


def _required_object(value: object, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"mapping publication field {field_name} must be an object")
    return value


def _required_list(value: object, field_name: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"mapping publication field {field_name} must be an array")
    return value


def _required_string(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"mapping publication field {field_name} must be a non-empty string")
    prepared = value.strip()
    if "\n" in prepared or "\r" in prepared:
        raise ValueError(f"mapping publication field {field_name} must be one line")
    return prepared


def _reviewed_at(value: object) -> str:
    prepared = _required_string(value, "reviewed_at")
    parse_value = prepared[:-1] + "+00:00" if prepared.endswith("Z") else prepared
    try:
        parsed = datetime.fromisoformat(parse_value)
    except ValueError as error:
        raise ValueError("mapping publication reviewed_at must be ISO-8601") from error
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("mapping publication reviewed_at must include a timezone offset")
    return prepared


def _serialized(mapping: Mapping[str, Any]) -> bytes:
    return (json.dumps(dict(mapping), indent=2, sort_keys=True) + "\n").encode()


def _write_atomic(path: Path, body: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(body)
    temporary.replace(path)


def _validate_promotion(payload: Mapping[str, Any]) -> tuple[str, str, list[dict[str, Any]]]:
    if payload.get("schema_version") != 1:
        raise ValueError("unsupported report slice mapping promotion schema version")
    if payload.get("promotion_kind") != _PROMOTION_KIND:
        raise ValueError("unexpected report slice mapping promotion kind")

    reviewed_by = _required_string(payload.get("reviewed_by"), "reviewed_by")
    reviewed_at = _reviewed_at(payload.get("reviewed_at"))

    summary = _required_object(payload.get("summary"), "summary")
    expected_summary = {
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
    for field_name, expected in expected_summary.items():
        if summary.get(field_name) != expected:
            raise ValueError(f"mapping promotion summary mismatch: {field_name}")

    boundary = _required_object(payload.get("decision_boundary"), "decision_boundary")
    expected_boundary = {
        "status": "verified",
        "automatic_promotion": False,
        "manual_promotion_completed": True,
        "automatic_publication": False,
        "manual_publication_required": True,
        "ready_to_publish_verified_mappings": True,
        "mechanic_semantics_verified": False,
        "normalization_allowed": False,
    }
    for field_name, expected in expected_boundary.items():
        if boundary.get(field_name) != expected:
            raise ValueError(f"mapping promotion boundary mismatch: {field_name}")

    deferred_scopes = _required_list(payload.get("deferred_scopes"), "deferred_scopes")
    expected_deferred = {
        ("combatants_info", "/combatants/*"),
        ("combatants_info", "/combatants/*/ci_resolved"),
        ("combatants_info", "/combatants/*/ci_resolved/specialization"),
    }
    actual_deferred: set[tuple[str, str]] = set()
    for raw_row in deferred_scopes:
        row = _required_object(raw_row, "deferred_scopes[]")
        if row.get("decision") != "deferred":
            raise ValueError("mapping promotion deferred scope has an unexpected decision")
        _required_string(row.get("reason"), "deferred_scopes[].reason")
        actual_deferred.add(
            (
                _required_string(row.get("endpoint_kind"), "deferred_scopes[].endpoint_kind"),
                _required_string(row.get("scope"), "deferred_scopes[].scope"),
            )
        )
    if actual_deferred != expected_deferred:
        raise ValueError("mapping promotion deferred scope set mismatch")

    rows: dict[str, dict[str, Any]] = {}
    for raw_row in _required_list(payload.get("verified_mappings"), "verified_mappings"):
        row = _required_object(raw_row, "verified_mappings[]")
        mapping = _required_object(row.get("mapping"), "verified_mappings[].mapping")
        mapping_id = _required_string(mapping.get("mapping_id"), "mapping_id")
        if mapping_id not in _EXPECTED_MAPPINGS or mapping_id in rows:
            raise ValueError(f"unsupported or duplicated promoted mapping: {mapping_id}")
        expected = _EXPECTED_MAPPINGS[mapping_id]
        if row.get("mapping_id") != mapping_id:
            raise ValueError(f"promoted mapping row id mismatch for {mapping_id}")
        if row.get("mapping_file") != expected["mapping_file"]:
            raise ValueError(f"promoted mapping file mismatch for {mapping_id}")
        if row.get("field_contract_count") != expected["field_contract_count"]:
            raise ValueError(f"promoted field contract count mismatch for {mapping_id}")
        if row.get("dry_run_counts") != expected["dry_run_counts"]:
            raise ValueError(f"promoted dry-run counts mismatch for {mapping_id}")
        if row.get("raw_archive_verified") is not True:
            raise ValueError(f"promoted raw archive gate failed for {mapping_id}")
        if row.get("cross_payload_consistent") is not True:
            raise ValueError(f"promoted cross-payload gate failed for {mapping_id}")
        if mapping.get("status") != "verified":
            raise ValueError(f"promoted mapping {mapping_id} must be verified")
        if mapping.get("reviewed_by") != reviewed_by:
            raise ValueError(f"promoted mapping reviewer mismatch for {mapping_id}")
        if mapping.get("reviewed_at") != reviewed_at:
            raise ValueError(f"promoted mapping review time mismatch for {mapping_id}")
        if mapping.get("mechanic_semantics_verified") is not False:
            raise ValueError(f"promoted mapping mechanics boundary changed for {mapping_id}")
        if mapping.get("verification_scope") != (
            "parser_schema_raw_archive_dry_run_and_cross_payload_linkage_only"
        ):
            raise ValueError(f"promoted mapping verification scope mismatch for {mapping_id}")
        if mapping.get("event_type_map") != {}:
            raise ValueError(f"promoted mapping {mapping_id} must not define aura semantics")
        contracts = _required_list(mapping.get("field_contracts"), "field_contracts")
        if len(contracts) != expected["field_contract_count"]:
            raise ValueError(f"promoted embedded contract count mismatch for {mapping_id}")
        for raw_contract in contracts:
            contract = _required_object(raw_contract, "field_contracts[]")
            if contract.get("semantic_status") != "verified_parser_field":
                raise ValueError(f"promoted parser field is not verified for {mapping_id}")
        if not NormalizationMapping.from_dict(mapping).production_ready:
            raise ValueError(f"promoted mapping is not production ready: {mapping_id}")
        rows[mapping_id] = row

    if set(rows) != set(_EXPECTED_MAPPINGS):
        raise ValueError("promoted mapping set mismatch")
    return reviewed_by, reviewed_at, [rows[mapping_id] for mapping_id in sorted(rows)]


def publish_observed_report_slice_mappings(
    promotion_path: Path,
    *,
    staged_mapping_dir: Path,
    target_mapping_dir: Path,
) -> dict[str, Any]:
    """Publish exactly reviewed parser mappings and return a scalar-free receipt."""
    promotion = _load_object(promotion_path, "report slice mapping promotion")
    reviewed_by, reviewed_at, rows = _validate_promotion(promotion)

    published_rows: list[dict[str, Any]] = []
    for row in rows:
        mapping = _required_object(row.get("mapping"), "verified_mappings[].mapping")
        mapping_id = _required_string(row.get("mapping_id"), "mapping_id")
        mapping_file = _required_string(row.get("mapping_file"), "mapping_file")
        staged_path = staged_mapping_dir / mapping_file
        staged = _load_object(staged_path, f"staged verified mapping {mapping_id}")
        if staged != mapping:
            raise ValueError(f"staged verified mapping does not match promotion: {mapping_id}")

        body = _serialized(mapping)
        target_path = target_mapping_dir / mapping_file
        already_current = target_path.is_file() and target_path.read_bytes() == body
        if target_path.exists() and not target_path.is_file():
            raise ValueError(f"mapping publication target is not a file: {target_path}")
        if target_path.is_file() and not already_current:
            raise ValueError(f"mapping publication target already differs: {target_path}")
        if not already_current:
            _write_atomic(target_path, body)

        published_rows.append(
            {
                "mapping_id": mapping_id,
                "mapping_file": mapping_file,
                "status": "verified",
                "field_contract_count": row["field_contract_count"],
                "content_sha256": hashlib.sha256(body).hexdigest(),
                "target_path": target_path.as_posix(),
                "already_current": already_current,
            }
        )

    return {
        "schema_version": _PUBLICATION_SCHEMA_VERSION,
        "publication_kind": "observed_report_slice_verified_mapping_publication",
        "source_promotion_name": promotion_path.name,
        "reviewed_by": reviewed_by,
        "reviewed_at": reviewed_at,
        "published_mappings": published_rows,
        "decision_boundary": {
            "status": "published",
            "automatic_publication": False,
            "manual_publication_completed": True,
            "selected_parser_normalization_allowed": True,
            "mechanic_semantics_verified": False,
            "combatants_info_enrichment_available": False,
            "aura_normalization_available": False,
            "full_report_slice_complete": False,
        },
        "summary": {
            "mapping_count": len(published_rows),
            "field_contract_count": sum(row["field_contract_count"] for row in published_rows),
            "all_staged_files_match_promotion": True,
            "all_targets_published": True,
            "contains_source_scalar_values": False,
            "selected_parser_normalization_allowed": True,
            "mechanic_semantics_verified": False,
            "full_report_slice_complete": False,
        },
    }
