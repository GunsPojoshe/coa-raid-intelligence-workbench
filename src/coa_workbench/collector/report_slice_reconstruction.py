from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

_RECONSTRUCTION_SCHEMA_VERSION = 1
_RECONSTRUCTION_VERSION = "report-slice-reconstruction-v1"
_NORMALIZATION_KIND = "observed_report_slice_selected_parser_normalization"
_EXPECTED_BATCHES = {
    "coa-encounter-detail-v1": {
        "normalized_batch_file": "coa_encounter_detail_v1.normalized.json",
        "counts": {
            "reports": 1,
            "encounters": 1,
            "actors": 31,
            "participants": 31,
            "aura_events": 0,
            "rejects": 0,
        },
    },
    "coa-report-detail-v1": {
        "normalized_batch_file": "coa_report_detail_v1.normalized.json",
        "counts": {
            "reports": 1,
            "encounters": 14,
            "actors": 0,
            "participants": 0,
            "aura_events": 0,
            "rejects": 0,
        },
    },
}
_EXPECTED_INPUT_COUNTS = {
    "reports": 2,
    "encounters": 15,
    "actors": 31,
    "participants": 31,
    "aura_events": 0,
    "rejects": 0,
}
_EXPECTED_OUTPUT_COUNTS = {
    "reports": 1,
    "encounters": 14,
    "actors": 31,
    "participants": 31,
    "aura_events": 0,
    "rejects": 0,
}
_EXPECTED_CROSS_PAYLOAD_CHECKS = {
    "exact_encounter_present_in_report_batch",
    "participant_actor_references_resolved",
    "participant_encounter_references_resolved",
    "participant_pairs_unique",
    "report_id_consistent",
    "single_report_id_in_each_batch",
}
_MISSING = object()


def _generated_at() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _load_object(path: Path, description: str) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{description} must contain a JSON object")
    return payload


def _required_object(value: object, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"report slice reconstruction field {field_name} must be an object")
    return value


def _required_list(value: object, field_name: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"report slice reconstruction field {field_name} must be an array")
    return value


def _required_string(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(
            f"report slice reconstruction field {field_name} must be a non-empty string"
        )
    return value


def _required_boolean(value: object, field_name: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"report slice reconstruction field {field_name} must be a boolean")
    return value


def _required_integer(value: object, field_name: str, *, minimum: int = 0) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < minimum:
        raise ValueError(
            f"report slice reconstruction field {field_name} must be an integer greater than or "
            f"equal to {minimum}"
        )
    return value


def _required_sha256(value: object, field_name: str) -> str:
    prepared = _required_string(value, field_name).casefold()
    if len(prepared) != 64 or any(char not in "0123456789abcdef" for char in prepared):
        raise ValueError(f"report slice reconstruction field {field_name} must be a SHA-256 digest")
    return prepared


def _serialized(payload: Mapping[str, Any]) -> bytes:
    return (json.dumps(dict(payload), indent=2, sort_keys=True) + "\n").encode()


def _write_atomic(path: Path, body: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(body)
    temporary.replace(path)


def _validate_normalization_receipt(
    receipt: Mapping[str, Any],
) -> dict[str, dict[str, Any]]:
    if receipt.get("schema_version") != 1:
        raise ValueError("unsupported report slice normalization schema version")
    if receipt.get("normalization_kind") != _NORMALIZATION_KIND:
        raise ValueError("unexpected report slice normalization kind")

    summary = _required_object(receipt.get("summary"), "summary")
    expected_summary = {
        "mapping_count": 2,
        "field_contract_count": 54,
        "exact_raw_archive_count": 2,
        "all_mapping_hashes_verified": True,
        "all_raw_archives_verified": True,
        "all_normalization_counts_match": True,
        "cross_payload_consistent": True,
        "contains_source_scalar_values": False,
        "normalized_batch_files_contain_source_scalar_values": True,
        "ready_for_deterministic_reconstruction": True,
        "mechanic_semantics_verified": False,
        "full_report_slice_complete": False,
    }
    for field_name, expected in expected_summary.items():
        if summary.get(field_name) != expected:
            raise ValueError(f"report slice normalization summary mismatch: {field_name}")
    if summary.get("aggregate_counts") != _EXPECTED_INPUT_COUNTS:
        raise ValueError("report slice normalization aggregate counts mismatch")

    boundary = _required_object(receipt.get("decision_boundary"), "decision_boundary")
    expected_boundary = {
        "status": "normalized_parser_slice",
        "selected_parser_normalization_completed": True,
        "ready_for_deterministic_reconstruction": True,
        "automatic_commit": False,
        "mechanic_semantics_verified": False,
        "combatants_info_enrichment_available": False,
        "aura_normalization_available": False,
        "full_report_slice_complete": False,
        "normalized_batch_files_contain_source_scalar_values": True,
    }
    for field_name, expected in expected_boundary.items():
        if boundary.get(field_name) != expected:
            raise ValueError(f"report slice normalization boundary mismatch: {field_name}")

    cross_checks = _required_object(receipt.get("cross_payload_checks"), "cross_payload_checks")
    if set(cross_checks) != _EXPECTED_CROSS_PAYLOAD_CHECKS:
        raise ValueError("report slice normalization cross-payload check set mismatch")
    if any(value is not True for value in cross_checks.values()):
        raise ValueError("report slice normalization cross-payload checks are incomplete")

    rows: dict[str, dict[str, Any]] = {}
    for raw_row in _required_list(receipt.get("normalized_batches"), "normalized_batches"):
        row = _required_object(raw_row, "normalized_batches[]")
        mapping_id = _required_string(row.get("mapping_id"), "mapping_id")
        if mapping_id not in _EXPECTED_BATCHES or mapping_id in rows:
            raise ValueError(f"unsupported or duplicated normalized mapping: {mapping_id}")
        expected = _EXPECTED_BATCHES[mapping_id]
        if row.get("normalized_batch_file") != expected["normalized_batch_file"]:
            raise ValueError(f"normalized batch filename mismatch for {mapping_id}")
        if row.get("counts") != expected["counts"]:
            raise ValueError(f"normalized batch count mismatch for {mapping_id}")
        if _required_boolean(row.get("mapping_hash_verified"), "mapping_hash_verified") is not True:
            raise ValueError(f"normalized mapping hash gate failed for {mapping_id}")
        if _required_boolean(row.get("raw_archive_verified"), "raw_archive_verified") is not True:
            raise ValueError(f"normalized raw archive gate failed for {mapping_id}")
        _required_sha256(row.get("mapping_content_sha256"), "mapping_content_sha256")
        _required_sha256(row.get("normalized_batch_sha256"), "normalized_batch_sha256")
        _required_sha256(row.get("source_payload_hash"), "source_payload_hash")
        _required_sha256(row.get("schema_fingerprint"), "schema_fingerprint")
        rows[mapping_id] = row

    if set(rows) != set(_EXPECTED_BATCHES):
        raise ValueError("normalized mapping set mismatch")
    return rows


def _load_normalized_batch(
    row: Mapping[str, Any],
    *,
    normalized_output_dir: Path,
) -> dict[str, Any]:
    root = normalized_output_dir.resolve()
    filename = _required_string(row.get("normalized_batch_file"), "normalized_batch_file")
    path = (root / filename).resolve()
    if not path.is_relative_to(root) or not path.is_file() or path.name != filename:
        raise ValueError("normalized batch must be a JSON file below normalized-output-dir")
    body = path.read_bytes()
    expected_hash = _required_sha256(row.get("normalized_batch_sha256"), "normalized_batch_sha256")
    if hashlib.sha256(body).hexdigest() != expected_hash:
        raise ValueError(f"normalized batch content hash mismatch for {row.get('mapping_id')}")

    payload = json.loads(body)
    if not isinstance(payload, dict):
        raise ValueError("normalized batch payload must be an object")
    if payload.get("schema_version") != 1 or payload.get("normalization_kind") != "canonical_batch":
        raise ValueError("normalized batch envelope mismatch")
    if payload.get("source_payload_hash") != row.get("source_payload_hash"):
        raise ValueError("normalized batch source payload hash mismatch")
    if payload.get("schema_fingerprint") != row.get("schema_fingerprint"):
        raise ValueError("normalized batch schema fingerprint mismatch")

    batch = _required_object(payload.get("batch"), "batch")
    mapping_id = _required_string(batch.get("mapping_id"), "batch.mapping_id")
    if mapping_id != row.get("mapping_id"):
        raise ValueError("normalized batch mapping id mismatch")
    if batch.get("source_code") != "coa_ascension_logs":
        raise ValueError("normalized batch source code mismatch")
    if batch.get("mapping_version") != "1":
        raise ValueError("normalized batch mapping version mismatch")
    if batch.get("normalizer_version") != "canonical-normalizer-v1":
        raise ValueError("normalized batch normalizer version mismatch")

    expected_counts = _required_object(row.get("counts"), "counts")
    actual_counts = {
        name: len(_required_list(batch.get(name), f"batch.{name}"))
        for name in (
            "reports",
            "encounters",
            "actors",
            "participants",
            "aura_events",
            "rejects",
        )
    }
    if batch.get("counts") != expected_counts or actual_counts != expected_counts:
        raise ValueError(f"normalized batch embedded counts mismatch for {mapping_id}")
    if actual_counts["aura_events"] != 0 or actual_counts["rejects"] != 0:
        raise ValueError("selected parser reconstruction requires empty aura events and rejects")
    return batch


def _record_key(record: Mapping[str, Any], fields: Sequence[str], entity: str) -> tuple[str, ...]:
    values = []
    for field_name in fields:
        value = record.get(field_name)
        if value in (None, ""):
            raise ValueError(f"reconstruction {entity} record is missing key field {field_name}")
        values.append(str(value))
    return tuple(values)


def _merge_record(
    existing: Mapping[str, Any],
    incoming: Mapping[str, Any],
    *,
    entity: str,
) -> tuple[dict[str, Any], int]:
    merged = deepcopy(dict(existing))
    filled_fields = 0
    for field_name in sorted(set(existing) | set(incoming)):
        current = existing.get(field_name, _MISSING)
        candidate = incoming.get(field_name, _MISSING)
        if candidate is _MISSING:
            continue
        if current is _MISSING or (current is None and candidate is not None):
            merged[field_name] = deepcopy(candidate)
            filled_fields += 1
            continue
        if candidate is None or current == candidate:
            continue
        raise ValueError(f"reconstruction field conflict for {entity}.{field_name}")
    return merged, filled_fields


def _merge_entity(
    batches: Sequence[Mapping[str, Any]],
    *,
    entity: str,
    key_fields: Sequence[str],
    allow_duplicate_merge: bool,
) -> tuple[list[dict[str, Any]], int, int]:
    records: dict[tuple[str, ...], dict[str, Any]] = {}
    duplicate_count = 0
    filled_field_count = 0
    for batch in batches:
        for raw_record in _required_list(batch.get(entity), f"batch.{entity}"):
            record = _required_object(raw_record, f"batch.{entity}[]")
            key = _record_key(record, key_fields, entity)
            if key not in records:
                records[key] = deepcopy(record)
                continue
            if not allow_duplicate_merge:
                raise ValueError(f"reconstruction duplicated {entity} key")
            duplicate_count += 1
            records[key], filled = _merge_record(records[key], record, entity=entity)
            filled_field_count += filled
    return [records[key] for key in sorted(records)], duplicate_count, filled_field_count


def reconstruct_observed_report_slice(
    normalization_path: Path,
    *,
    normalized_output_dir: Path,
    reconstructed_output_path: Path,
) -> dict[str, Any]:
    """Merge exact normalized parser batches into one deterministic local canonical slice."""
    normalization = _load_object(normalization_path, "report slice normalization receipt")
    rows = _validate_normalization_receipt(normalization)
    batches_by_id = {
        mapping_id: _load_normalized_batch(row, normalized_output_dir=normalized_output_dir)
        for mapping_id, row in sorted(rows.items())
    }
    batches = [batches_by_id[mapping_id] for mapping_id in sorted(batches_by_id)]

    reports, duplicate_reports, report_fields_filled = _merge_entity(
        batches,
        entity="reports",
        key_fields=("report_id",),
        allow_duplicate_merge=True,
    )
    encounters, duplicate_encounters, encounter_fields_filled = _merge_entity(
        batches,
        entity="encounters",
        key_fields=("encounter_id",),
        allow_duplicate_merge=True,
    )
    actors, duplicate_actors, actor_fields_filled = _merge_entity(
        batches,
        entity="actors",
        key_fields=("actor_id",),
        allow_duplicate_merge=False,
    )
    participants, duplicate_participants, participant_fields_filled = _merge_entity(
        batches,
        entity="participants",
        key_fields=("encounter_id", "actor_id"),
        allow_duplicate_merge=False,
    )

    if duplicate_reports != 1 or duplicate_encounters != 1:
        raise ValueError("reconstruction expected exactly one duplicated report and encounter")
    if duplicate_actors != 0 or duplicate_participants != 0:
        raise ValueError("reconstruction encountered unexpected actor or participant duplicates")

    output_counts = {
        "reports": len(reports),
        "encounters": len(encounters),
        "actors": len(actors),
        "participants": len(participants),
        "aura_events": 0,
        "rejects": 0,
    }
    if output_counts != _EXPECTED_OUTPUT_COUNTS:
        raise ValueError(
            f"reconstructed report slice count mismatch: expected={_EXPECTED_OUTPUT_COUNTS} "
            f"actual={output_counts}"
        )

    report_ids = {str(row["report_id"]) for row in reports}
    encounter_ids = {str(row["encounter_id"]) for row in encounters}
    actor_ids = {str(row["actor_id"]) for row in actors}
    participant_pairs = {
        (str(row["encounter_id"]), str(row["actor_id"])) for row in participants
    }
    participant_encounter_ids = {str(row["encounter_id"]) for row in participants}
    report_detail_batch = batches_by_id["coa-report-detail-v1"]
    encounter_detail_batch = batches_by_id["coa-encounter-detail-v1"]
    source_report_field_union = set(report_detail_batch["reports"][0]) | set(
        encounter_detail_batch["reports"][0]
    )
    source_encounter_field_union = set(report_detail_batch["encounters"][0]) | set(
        encounter_detail_batch["encounters"][0]
    )
    merged_report_fields = set(reports[0])
    exact_encounter_id = str(encounter_detail_batch["encounters"][0]["encounter_id"])
    exact_encounter = next(
        row for row in encounters if str(row["encounter_id"]) == exact_encounter_id
    )

    linkage_checks = {
        "single_report_reconstructed": len(report_ids) == 1,
        "all_encounters_reference_report": all(
            str(row.get("report_id")) in report_ids for row in encounters
        ),
        "participant_actor_references_resolved": all(
            str(row["actor_id"]) in actor_ids for row in participants
        ),
        "participant_encounter_references_resolved": all(
            str(row["encounter_id"]) in encounter_ids for row in participants
        ),
        "participant_pairs_unique": len(participant_pairs) == len(participants),
        "single_participant_encounter": len(participant_encounter_ids) == 1,
        "exact_encounter_reconstructed": participant_encounter_ids == {exact_encounter_id},
        "report_fields_preserved": source_report_field_union.issubset(merged_report_fields),
        "exact_encounter_fields_preserved": source_encounter_field_union.issubset(
            set(exact_encounter)
        ),
    }
    failed_checks = sorted(name for name, passed in linkage_checks.items() if not passed)
    if failed_checks:
        raise ValueError("reconstructed report slice checks failed: " + ", ".join(failed_checks))

    reconstructed_payload = {
        "schema_version": 1,
        "reconstruction_kind": "observed_report_slice_canonical_reconstruction",
        "reconstruction_version": _RECONSTRUCTION_VERSION,
        "source_normalization_name": normalization_path.name,
        "source_normalized_batch_sha256": {
            mapping_id: rows[mapping_id]["normalized_batch_sha256"]
            for mapping_id in sorted(rows)
        },
        "canonical_slice": {
            "source_code": "coa_ascension_logs",
            "reports": reports,
            "encounters": encounters,
            "actors": actors,
            "participants": participants,
            "aura_events": [],
            "rejects": [],
        },
    }
    reconstructed_body = _serialized(reconstructed_payload)
    _write_atomic(reconstructed_output_path, reconstructed_body)

    merge_statistics = {
        "input_counts": dict(_EXPECTED_INPUT_COUNTS),
        "output_counts": output_counts,
        "duplicate_records_merged": {
            "reports": duplicate_reports,
            "encounters": duplicate_encounters,
            "actors": duplicate_actors,
            "participants": duplicate_participants,
        },
        "complementary_fields_filled": {
            "reports": report_fields_filled,
            "encounters": encounter_fields_filled,
            "actors": actor_fields_filled,
            "participants": participant_fields_filled,
        },
        "field_conflict_count": 0,
    }
    source_batches = [
        {
            "mapping_id": mapping_id,
            "normalized_batch_file": rows[mapping_id]["normalized_batch_file"],
            "normalized_batch_sha256": rows[mapping_id]["normalized_batch_sha256"],
            "counts": rows[mapping_id]["counts"],
            "batch_hash_verified": True,
        }
        for mapping_id in sorted(rows)
    ]
    return {
        "schema_version": _RECONSTRUCTION_SCHEMA_VERSION,
        "reconstruction_kind": "observed_report_slice_deterministic_reconstruction",
        "reconstruction_version": _RECONSTRUCTION_VERSION,
        "generated_at": _generated_at(),
        "source_normalization_name": normalization_path.name,
        "source_normalized_batches": source_batches,
        "reconstructed_output_file": reconstructed_output_path.name,
        "reconstructed_output_sha256": hashlib.sha256(reconstructed_body).hexdigest(),
        "merge_statistics": merge_statistics,
        "linkage_checks": linkage_checks,
        "decision_boundary": {
            "status": "reconstructed_parser_slice",
            "deterministic_reconstruction_completed": True,
            "ready_for_selected_parser_persistence": True,
            "automatic_commit": False,
            "mechanic_semantics_verified": False,
            "combatants_info_enrichment_available": False,
            "aura_reconstruction_available": False,
            "full_report_slice_complete": False,
            "reconstructed_file_contains_source_scalar_values": True,
        },
        "summary": {
            "source_batch_count": len(source_batches),
            "input_counts": dict(_EXPECTED_INPUT_COUNTS),
            "output_counts": output_counts,
            "duplicate_report_count": duplicate_reports,
            "duplicate_encounter_count": duplicate_encounters,
            "field_conflict_count": 0,
            "all_input_batch_hashes_verified": True,
            "all_linkage_checks_passed": True,
            "contains_source_scalar_values": False,
            "reconstructed_file_contains_source_scalar_values": True,
            "ready_for_selected_parser_persistence": True,
            "mechanic_semantics_verified": False,
            "full_report_slice_complete": False,
        },
    }
