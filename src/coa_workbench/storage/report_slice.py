from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from .migrations import apply_migrations

_PERSISTENCE_SCHEMA_VERSION = 1
_PERSISTENCE_VERSION = "selected-parser-persistence-v1"
_RECONSTRUCTION_KIND = "observed_report_slice_deterministic_reconstruction"
_RECONSTRUCTED_PAYLOAD_KIND = "observed_report_slice_canonical_reconstruction"
_RECONSTRUCTION_VERSION = "report-slice-reconstruction-v1"
_NORMALIZATION_KIND = "observed_report_slice_selected_parser_normalization"
_NORMALIZER_VERSION = "canonical-normalizer-v1"
_SOURCE_CODE = "coa_ascension_logs"
_EXPECTED_COUNTS = {
    "reports": 1,
    "encounters": 14,
    "actors": 31,
    "participants": 31,
    "aura_events": 0,
    "rejects": 0,
}
_EXPECTED_INPUT_COUNTS = {
    "reports": 2,
    "encounters": 15,
    "actors": 31,
    "participants": 31,
    "aura_events": 0,
    "rejects": 0,
}
_EXPECTED_BATCHES = {
    "coa-encounter-detail-v1": {
        "mapping_file": "coa_encounter_detail_v1.json",
        "endpoint_code": "encounter_detail",
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
        "mapping_file": "coa_report_detail_v1.json",
        "endpoint_code": "report_detail",
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
_EXPECTED_RECONSTRUCTION_CHECKS = {
    "all_encounters_reference_report",
    "exact_encounter_fields_preserved",
    "exact_encounter_reconstructed",
    "participant_actor_references_resolved",
    "participant_encounter_references_resolved",
    "participant_pairs_unique",
    "report_fields_preserved",
    "single_participant_encounter",
    "single_report_reconstructed",
}
_EXPECTED_NORMALIZATION_CHECKS = {
    "exact_encounter_present_in_report_batch",
    "participant_actor_references_resolved",
    "participant_encounter_references_resolved",
    "participant_pairs_unique",
    "report_id_consistent",
    "single_report_id_in_each_batch",
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
        raise ValueError(f"report slice persistence field {field_name} must be an object")
    return value


def _required_list(value: object, field_name: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"report slice persistence field {field_name} must be an array")
    return value


def _required_string(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"report slice persistence field {field_name} must be a non-empty string")
    return value


def _required_boolean(value: object, field_name: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"report slice persistence field {field_name} must be a boolean")
    return value


def _required_sha256(value: object, field_name: str) -> str:
    prepared = _required_string(value, field_name).casefold()
    if len(prepared) != 64 or any(char not in "0123456789abcdef" for char in prepared):
        raise ValueError(f"report slice persistence field {field_name} must be a SHA-256 digest")
    return prepared


def _canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _stable_id(entity: str, *parts: object) -> str:
    material = "\0".join([entity, *(str(part) for part in parts)])
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def _timestamp(value: object, field_name: str) -> datetime:
    prepared = _required_string(value, field_name)
    parse_value = prepared[:-1] + "+00:00" if prepared.endswith("Z") else prepared
    try:
        parsed = datetime.fromisoformat(parse_value)
    except ValueError as error:
        raise ValueError(f"report slice persistence field {field_name} must be ISO-8601") from error
    if parsed.tzinfo is not None and parsed.utcoffset() is not None:
        parsed = parsed.astimezone(timezone.utc).replace(tzinfo=None)
    return parsed


def _validate_reconstruction_receipt(receipt: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    if receipt.get("schema_version") != 1:
        raise ValueError("unsupported report slice reconstruction schema version")
    if receipt.get("reconstruction_kind") != _RECONSTRUCTION_KIND:
        raise ValueError("unexpected report slice reconstruction kind")
    if receipt.get("reconstruction_version") != _RECONSTRUCTION_VERSION:
        raise ValueError("unexpected report slice reconstruction version")

    summary = _required_object(receipt.get("summary"), "summary")
    expected_summary = {
        "source_batch_count": 2,
        "duplicate_report_count": 1,
        "duplicate_encounter_count": 1,
        "field_conflict_count": 0,
        "all_input_batch_hashes_verified": True,
        "all_linkage_checks_passed": True,
        "contains_source_scalar_values": False,
        "reconstructed_file_contains_source_scalar_values": True,
        "ready_for_selected_parser_persistence": True,
        "mechanic_semantics_verified": False,
        "full_report_slice_complete": False,
    }
    for field_name, expected in expected_summary.items():
        if summary.get(field_name) != expected:
            raise ValueError(f"report slice reconstruction summary mismatch: {field_name}")
    if summary.get("input_counts") != _EXPECTED_INPUT_COUNTS:
        raise ValueError("report slice reconstruction input counts mismatch")
    if summary.get("output_counts") != _EXPECTED_COUNTS:
        raise ValueError("report slice reconstruction output counts mismatch")

    boundary = _required_object(receipt.get("decision_boundary"), "decision_boundary")
    expected_boundary = {
        "status": "reconstructed_parser_slice",
        "deterministic_reconstruction_completed": True,
        "ready_for_selected_parser_persistence": True,
        "automatic_commit": False,
        "mechanic_semantics_verified": False,
        "combatants_info_enrichment_available": False,
        "aura_reconstruction_available": False,
        "full_report_slice_complete": False,
        "reconstructed_file_contains_source_scalar_values": True,
    }
    for field_name, expected in expected_boundary.items():
        if boundary.get(field_name) != expected:
            raise ValueError(f"report slice reconstruction boundary mismatch: {field_name}")

    checks = _required_object(receipt.get("linkage_checks"), "linkage_checks")
    if set(checks) != _EXPECTED_RECONSTRUCTION_CHECKS:
        raise ValueError("report slice reconstruction linkage check set mismatch")
    if any(value is not True for value in checks.values()):
        raise ValueError("report slice reconstruction linkage checks are incomplete")

    rows: dict[str, dict[str, Any]] = {}
    for raw_row in _required_list(receipt.get("source_normalized_batches"), "source_normalized_batches"):
        row = _required_object(raw_row, "source_normalized_batches[]")
        mapping_id = _required_string(row.get("mapping_id"), "mapping_id")
        if mapping_id not in _EXPECTED_BATCHES or mapping_id in rows:
            raise ValueError(f"unsupported or duplicated reconstruction batch: {mapping_id}")
        expected = _EXPECTED_BATCHES[mapping_id]
        if row.get("normalized_batch_file") != expected["mapping_file"].replace(
            ".json", ".normalized.json"
        ):
            raise ValueError(f"reconstruction normalized batch filename mismatch for {mapping_id}")
        if row.get("counts") != expected["counts"]:
            raise ValueError(f"reconstruction normalized batch counts mismatch for {mapping_id}")
        if _required_boolean(row.get("batch_hash_verified"), "batch_hash_verified") is not True:
            raise ValueError(f"reconstruction batch hash gate failed for {mapping_id}")
        _required_sha256(row.get("normalized_batch_sha256"), "normalized_batch_sha256")
        rows[mapping_id] = row
    if set(rows) != set(_EXPECTED_BATCHES):
        raise ValueError("reconstruction source batch set mismatch")
    return rows


def _validate_normalization_receipt(receipt: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    if receipt.get("schema_version") != 1:
        raise ValueError("unsupported report slice normalization schema version")
    if receipt.get("normalization_kind") != _NORMALIZATION_KIND:
        raise ValueError("unexpected report slice normalization kind")

    summary = _required_object(receipt.get("summary"), "normalization.summary")
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

    boundary = _required_object(receipt.get("decision_boundary"), "normalization.decision_boundary")
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

    checks = _required_object(receipt.get("cross_payload_checks"), "cross_payload_checks")
    if set(checks) != _EXPECTED_NORMALIZATION_CHECKS:
        raise ValueError("report slice normalization cross-payload check set mismatch")
    if any(value is not True for value in checks.values()):
        raise ValueError("report slice normalization cross-payload checks are incomplete")

    rows: dict[str, dict[str, Any]] = {}
    for raw_row in _required_list(receipt.get("normalized_batches"), "normalized_batches"):
        row = _required_object(raw_row, "normalized_batches[]")
        mapping_id = _required_string(row.get("mapping_id"), "mapping_id")
        if mapping_id not in _EXPECTED_BATCHES or mapping_id in rows:
            raise ValueError(f"unsupported or duplicated normalized mapping: {mapping_id}")
        expected = _EXPECTED_BATCHES[mapping_id]
        if row.get("mapping_file") != expected["mapping_file"]:
            raise ValueError(f"normalization mapping filename mismatch for {mapping_id}")
        if row.get("counts") != expected["counts"]:
            raise ValueError(f"normalization counts mismatch for {mapping_id}")
        if _required_boolean(row.get("mapping_hash_verified"), "mapping_hash_verified") is not True:
            raise ValueError(f"normalization mapping hash gate failed for {mapping_id}")
        if _required_boolean(row.get("raw_archive_verified"), "raw_archive_verified") is not True:
            raise ValueError(f"normalization raw archive gate failed for {mapping_id}")
        for field_name in (
            "mapping_content_sha256",
            "source_payload_hash",
            "schema_fingerprint",
            "normalized_batch_sha256",
        ):
            _required_sha256(row.get(field_name), field_name)
        rows[mapping_id] = row
    if set(rows) != set(_EXPECTED_BATCHES):
        raise ValueError("normalization mapping set mismatch")
    return rows


def _load_reconstructed_slice(
    receipt: Mapping[str, Any],
    reconstructed_output_path: Path,
    source_rows: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    expected_name = _required_string(receipt.get("reconstructed_output_file"), "reconstructed_output_file")
    if reconstructed_output_path.name != expected_name or not reconstructed_output_path.is_file():
        raise ValueError("reconstructed output path does not match the reconstruction receipt")
    body = reconstructed_output_path.read_bytes()
    expected_hash = _required_sha256(
        receipt.get("reconstructed_output_sha256"), "reconstructed_output_sha256"
    )
    if hashlib.sha256(body).hexdigest() != expected_hash:
        raise ValueError("reconstructed output content hash mismatch")

    payload = json.loads(body)
    if not isinstance(payload, dict):
        raise ValueError("reconstructed output must contain a JSON object")
    if payload.get("schema_version") != 1:
        raise ValueError("unsupported reconstructed output schema version")
    if payload.get("reconstruction_kind") != _RECONSTRUCTED_PAYLOAD_KIND:
        raise ValueError("unexpected reconstructed output kind")
    if payload.get("reconstruction_version") != _RECONSTRUCTION_VERSION:
        raise ValueError("unexpected reconstructed output version")
    if payload.get("source_normalization_name") != receipt.get("source_normalization_name"):
        raise ValueError("reconstructed output normalization source mismatch")

    expected_batch_hashes = {
        mapping_id: row["normalized_batch_sha256"] for mapping_id, row in sorted(source_rows.items())
    }
    if payload.get("source_normalized_batch_sha256") != expected_batch_hashes:
        raise ValueError("reconstructed output source batch hashes mismatch")

    canonical = _required_object(payload.get("canonical_slice"), "canonical_slice")
    if canonical.get("source_code") != _SOURCE_CODE:
        raise ValueError("reconstructed output source code mismatch")
    for entity, expected_count in _EXPECTED_COUNTS.items():
        rows = _required_list(canonical.get(entity), f"canonical_slice.{entity}")
        if len(rows) != expected_count:
            raise ValueError(f"reconstructed output count mismatch for {entity}")
    if canonical["aura_events"] or canonical["rejects"]:
        raise ValueError("selected parser persistence requires empty aura events and rejects")

    reports = [_required_object(row, "canonical_slice.reports[]") for row in canonical["reports"]]
    encounters = [
        _required_object(row, "canonical_slice.encounters[]") for row in canonical["encounters"]
    ]
    actors = [_required_object(row, "canonical_slice.actors[]") for row in canonical["actors"]]
    participants = [
        _required_object(row, "canonical_slice.participants[]")
        for row in canonical["participants"]
    ]
    report_ids = {_required_string(row.get("report_id"), "report_id") for row in reports}
    encounter_ids = {_required_string(row.get("encounter_id"), "encounter_id") for row in encounters}
    actor_ids = {_required_string(row.get("actor_id"), "actor_id") for row in actors}
    participant_pairs = {
        (
            _required_string(row.get("encounter_id"), "participant.encounter_id"),
            _required_string(row.get("actor_id"), "participant.actor_id"),
        )
        for row in participants
    }
    if len(report_ids) != 1 or len(encounter_ids) != 14 or len(actor_ids) != 31:
        raise ValueError("reconstructed output stable entity IDs are not unique")
    if len(participant_pairs) != 31:
        raise ValueError("reconstructed output participant pairs are not unique")
    if any(str(row.get("report_id")) not in report_ids for row in encounters):
        raise ValueError("reconstructed output encounter report reference is unresolved")
    if any(str(row.get("encounter_id")) not in encounter_ids for row in participants):
        raise ValueError("reconstructed output participant encounter reference is unresolved")
    if any(str(row.get("actor_id")) not in actor_ids for row in participants):
        raise ValueError("reconstructed output participant actor reference is unresolved")
    return canonical


def _mapping_payloads(
    normalization_rows: Mapping[str, Mapping[str, Any]],
    *,
    mapping_dir: Path,
) -> dict[str, dict[str, Any]]:
    mappings: dict[str, dict[str, Any]] = {}
    for mapping_id, row in sorted(normalization_rows.items()):
        expected = _EXPECTED_BATCHES[mapping_id]
        path = mapping_dir / expected["mapping_file"]
        body = path.read_bytes()
        if hashlib.sha256(body).hexdigest() != row["mapping_content_sha256"]:
            raise ValueError(f"published mapping content hash mismatch for {mapping_id}")
        mapping = json.loads(body)
        if not isinstance(mapping, dict):
            raise ValueError(f"published mapping {mapping_id} must contain a JSON object")
        if mapping.get("mapping_id") != mapping_id or mapping.get("status") != "verified":
            raise ValueError(f"published mapping identity or status mismatch for {mapping_id}")
        if mapping.get("source_code") != _SOURCE_CODE:
            raise ValueError(f"published mapping source mismatch for {mapping_id}")
        if mapping.get("schema_fingerprint") != row.get("schema_fingerprint"):
            raise ValueError(f"published mapping schema fingerprint mismatch for {mapping_id}")
        if mapping.get("reviewed_payload_hash") != row.get("source_payload_hash"):
            raise ValueError(f"published mapping payload hash mismatch for {mapping_id}")
        if mapping.get("mechanic_semantics_verified") is not False:
            raise ValueError(f"published mapping mechanics boundary changed for {mapping_id}")
        mappings[mapping_id] = mapping
    return mappings


def _row_change() -> dict[str, int]:
    return {"inserted": 0, "updated": 0, "unchanged": 0}


def _record_change(changes: dict[str, dict[str, int]], category: str, result: str) -> None:
    changes.setdefault(category, _row_change())[result] += 1


def _strict_insert_or_match(
    connection: Any,
    *,
    table: str,
    key_fields: Sequence[str],
    values: Mapping[str, Any],
) -> str:
    columns = list(values)
    where = " AND ".join(f"{field} = ?" for field in key_fields)
    key_values = [values[field] for field in key_fields]
    existing = connection.execute(
        f"SELECT {', '.join(columns)} FROM {table} WHERE {where}", key_values
    ).fetchone()
    incoming = tuple(values[column] for column in columns)
    if existing is not None:
        if tuple(existing) != incoming:
            raise ValueError(f"existing {table} row conflicts with selected parser persistence")
        return "unchanged"
    placeholders = ", ".join("?" for _ in columns)
    connection.execute(
        f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})",
        list(incoming),
    )
    return "inserted"


def _merge_core_row(
    connection: Any,
    *,
    table: str,
    key_fields: Sequence[str],
    values: Mapping[str, Any],
    range_fields: Mapping[str, str] | None = None,
) -> str:
    columns = list(values)
    where = " AND ".join(f"{field} = ?" for field in key_fields)
    key_values = [values[field] for field in key_fields]
    existing = connection.execute(
        f"SELECT {', '.join(columns)} FROM {table} WHERE {where}", key_values
    ).fetchone()
    if existing is None:
        placeholders = ", ".join("?" for _ in columns)
        connection.execute(
            f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})",
            [values[column] for column in columns],
        )
        return "inserted"

    current = dict(zip(columns, existing, strict=True))
    updates: dict[str, Any] = {}
    ranges = dict(range_fields or {})
    for column, incoming in values.items():
        if column in key_fields or incoming is None:
            continue
        present = current[column]
        if column in ranges:
            if present is None:
                updates[column] = incoming
            elif ranges[column] == "min" and incoming < present:
                updates[column] = incoming
            elif ranges[column] == "max" and incoming > present:
                updates[column] = incoming
            continue
        if present is None:
            updates[column] = incoming
        elif present != incoming:
            raise ValueError(f"existing {table}.{column} conflicts with selected parser persistence")
    if not updates:
        return "unchanged"
    assignments = ", ".join(f"{column} = ?" for column in updates)
    connection.execute(
        f"UPDATE {table} SET {assignments} WHERE {where}",
        [*updates.values(), *key_values],
    )
    return "updated"


def _register_mapping(
    connection: Any,
    mapping_id: str,
    mapping: Mapping[str, Any],
    *,
    endpoint_code: str,
) -> str:
    mapping_json = _canonical_json(mapping)
    existing = connection.execute(
        """
        SELECT source_code, endpoint_code, schema_fingerprint, mapping_version, status, mapping_json
        FROM normalization_mapping WHERE mapping_id = ?
        """,
        [mapping_id],
    ).fetchone()
    incoming = (
        _SOURCE_CODE,
        endpoint_code,
        mapping["schema_fingerprint"],
        str(mapping["mapping_version"]),
        "verified",
        mapping_json,
    )
    if existing is None:
        connection.execute(
            """
            INSERT INTO normalization_mapping (
                mapping_id, source_code, endpoint_code, schema_fingerprint,
                mapping_version, status, mapping_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [mapping_id, *incoming],
        )
        return "inserted"
    if tuple(existing) == incoming:
        return "unchanged"
    existing_mapping = json.loads(existing[5])
    if existing[4] == "candidate" and existing_mapping.get("mapping_id") == mapping_id:
        connection.execute(
            """
            UPDATE normalization_mapping
            SET source_code = ?, endpoint_code = ?, schema_fingerprint = ?,
                mapping_version = ?, status = ?, mapping_json = ?, updated_at = CURRENT_TIMESTAMP
            WHERE mapping_id = ?
            """,
            [*incoming, mapping_id],
        )
        return "updated"
    raise ValueError(f"existing normalization mapping conflicts for {mapping_id}")


def _raw_id_for_payload(connection: Any, payload_hash: str) -> str:
    rows = connection.execute(
        "SELECT raw_id FROM raw_object WHERE payload_hash = ? ORDER BY raw_id", [payload_hash]
    ).fetchall()
    if len(rows) != 1:
        raise ValueError(
            f"selected parser persistence requires exactly one raw_object for payload {payload_hash}"
        )
    return str(rows[0][0])


def _duration_ms(record: Mapping[str, Any]) -> int:
    started_at = _timestamp(record.get("start_time"), "encounter.start_time")
    ended_at = _timestamp(record.get("end_time"), "encounter.end_time")
    duration = int(round((ended_at - started_at).total_seconds() * 1000))
    if duration < 0:
        raise ValueError("encounter end_time is before start_time")
    return duration


def persist_observed_report_slice(
    reconstruction_path: Path,
    reconstructed_output_path: Path,
    normalization_path: Path,
    *,
    mapping_dir: Path,
    database_path: Path,
    migrations_dir: Path,
) -> dict[str, Any]:
    """Persist the verified reconstructed parser slice atomically and emit a scalar-free receipt."""
    reconstruction = _load_object(reconstruction_path, "report slice reconstruction receipt")
    reconstruction_rows = _validate_reconstruction_receipt(reconstruction)
    normalization = _load_object(normalization_path, "report slice normalization receipt")
    normalization_rows = _validate_normalization_receipt(normalization)
    if reconstruction.get("source_normalization_name") != normalization_path.name:
        raise ValueError("reconstruction receipt does not reference the submitted normalization receipt")
    for mapping_id in sorted(_EXPECTED_BATCHES):
        if (
            reconstruction_rows[mapping_id]["normalized_batch_sha256"]
            != normalization_rows[mapping_id]["normalized_batch_sha256"]
        ):
            raise ValueError(f"normalization and reconstruction batch hash mismatch for {mapping_id}")

    canonical = _load_reconstructed_slice(
        reconstruction,
        reconstructed_output_path,
        reconstruction_rows,
    )
    mappings = _mapping_payloads(normalization_rows, mapping_dir=mapping_dir)
    applied_migrations = apply_migrations(database_path, migrations_dir)

    import duckdb

    reports = [_required_object(row, "canonical_slice.reports[]") for row in canonical["reports"]]
    encounters = [
        _required_object(row, "canonical_slice.encounters[]") for row in canonical["encounters"]
    ]
    actors = [_required_object(row, "canonical_slice.actors[]") for row in canonical["actors"]]
    participants = [
        _required_object(row, "canonical_slice.participants[]")
        for row in canonical["participants"]
    ]
    report = reports[0]
    report_id = _required_string(report.get("report_id"), "report.report_id")
    participant_encounter_ids = {
        _required_string(row.get("encounter_id"), "participant.encounter_id")
        for row in participants
    }
    if len(participant_encounter_ids) != 1:
        raise ValueError("selected parser persistence expected one participant encounter")
    exact_encounter_id = next(iter(participant_encounter_ids))
    exact_encounter = next(
        row for row in encounters if str(row.get("encounter_id")) == exact_encounter_id
    )
    actor_by_id = {
        _required_string(row.get("actor_id"), "actor.actor_id"): row for row in actors
    }
    exact_started_at = _timestamp(exact_encounter.get("start_time"), "encounter.start_time")
    exact_ended_at = _timestamp(exact_encounter.get("end_time"), "encounter.end_time")
    reconstructed_hash = _required_sha256(
        reconstruction.get("reconstructed_output_sha256"), "reconstructed_output_sha256"
    )
    persistence_run_id = _stable_id(
        "parser_slice_persistence_run", reconstructed_hash, _PERSISTENCE_VERSION
    )

    changes: dict[str, dict[str, int]] = {}
    source_batches: list[dict[str, Any]] = []
    integrity_checks: dict[str, bool] = {
        "reconstruction_hash_verified": True,
        "normalization_receipt_consistent": True,
        "mapping_hashes_verified": True,
        "raw_objects_verified": False,
        "source_batches_registered": False,
        "core_entity_counts_match": False,
        "canonical_observation_counts_match": False,
        "participant_references_resolved": False,
        "transaction_committed": False,
    }

    database_path.parent.mkdir(parents=True, exist_ok=True)
    with duckdb.connect(str(database_path)) as connection:
        connection.execute("BEGIN TRANSACTION")
        try:
            batch_ids: dict[str, str] = {}
            raw_ids: dict[str, str] = {}
            for mapping_id in sorted(_EXPECTED_BATCHES):
                row = normalization_rows[mapping_id]
                mapping = mappings[mapping_id]
                expected = _EXPECTED_BATCHES[mapping_id]
                result = _register_mapping(
                    connection,
                    mapping_id,
                    mapping,
                    endpoint_code=expected["endpoint_code"],
                )
                _record_change(changes, "normalization_mappings", result)

                raw_id = _raw_id_for_payload(connection, row["source_payload_hash"])
                raw_ids[mapping_id] = raw_id
                current_status = connection.execute(
                    "SELECT normalizer_status FROM raw_object WHERE raw_id = ?", [raw_id]
                ).fetchone()[0]
                if current_status == "pending":
                    connection.execute(
                        "UPDATE raw_object SET normalizer_status = 'normalized' WHERE raw_id = ?",
                        [raw_id],
                    )
                    _record_change(changes, "raw_objects", "updated")
                elif current_status == "normalized":
                    _record_change(changes, "raw_objects", "unchanged")
                else:
                    raise ValueError(f"raw object {raw_id} has unexpected normalizer status")

                parser_version = f"{mapping_id}@1|{_NORMALIZER_VERSION}"
                batch_id = _stable_id(
                    "observation_batch", mapping_id, row["source_payload_hash"], parser_version
                )
                batch_ids[mapping_id] = batch_id
                observed_at = (
                    _timestamp(report.get("created_at"), "report.created_at")
                    if mapping_id == "coa-report-detail-v1"
                    else exact_started_at
                )
                batch_values = {
                    "batch_id": batch_id,
                    "source_code": _SOURCE_CODE,
                    "raw_id": raw_id,
                    "report_id": report_id,
                    "encounter_id": (
                        exact_encounter_id if mapping_id == "coa-encounter-detail-v1" else None
                    ),
                    "game_version_id": None,
                    "observed_at": observed_at,
                    "parser_version": parser_version,
                    "payload_hash": row["source_payload_hash"],
                    "quality_status": "observed",
                    "metadata_json": _canonical_json(
                        {
                            "mapping_id": mapping_id,
                            "mapping_content_sha256": row["mapping_content_sha256"],
                            "normalized_batch_sha256": row["normalized_batch_sha256"],
                            "schema_fingerprint": row["schema_fingerprint"],
                            "reconstruction_sha256": reconstructed_hash,
                            "provenance_type": "upstream_derived",
                            "mechanic_semantics_verified": False,
                        }
                    ),
                }
                result = _strict_insert_or_match(
                    connection,
                    table="observation_batch",
                    key_fields=("batch_id",),
                    values=batch_values,
                )
                _record_change(changes, "observation_batches", result)

                normalization_run_id = _stable_id(
                    "normalization_run", mapping_id, row["normalized_batch_sha256"]
                )
                normalized_at = _timestamp(normalization.get("generated_at"), "normalization.generated_at")
                run_values = {
                    "run_id": normalization_run_id,
                    "raw_id": raw_id,
                    "mapping_id": mapping_id,
                    "normalizer_version": _NORMALIZER_VERSION,
                    "status": "completed",
                    "started_at": normalized_at,
                    "finished_at": normalized_at,
                    "counts_json": _canonical_json(row["counts"]),
                    "error_json": None,
                }
                result = _strict_insert_or_match(
                    connection,
                    table="normalization_run",
                    key_fields=("run_id",),
                    values=run_values,
                )
                _record_change(changes, "normalization_runs", result)
                source_batches.append(
                    {
                        "mapping_id": mapping_id,
                        "batch_id": batch_id,
                        "normalization_run_id": normalization_run_id,
                        "raw_id": raw_id,
                        "source_payload_hash": row["source_payload_hash"],
                        "normalized_batch_sha256": row["normalized_batch_sha256"],
                        "counts": row["counts"],
                        "mapping_hash_verified": True,
                        "raw_object_verified": True,
                    }
                )

            integrity_checks["raw_objects_verified"] = True
            integrity_checks["source_batches_registered"] = True

            report_values = {
                "report_id": report_id,
                "source_report_id": str(report["source_report_id"]),
                "raid_date": _timestamp(report["start_time"], "report.start_time").date(),
                "created_at": _timestamp(report["created_at"], "report.created_at"),
                "status": str(report["status"]),
                "payload_hash": normalization_rows["coa-report-detail-v1"]["source_payload_hash"],
                "raw_id": raw_ids["coa-report-detail-v1"],
            }
            result = _merge_core_row(
                connection,
                table="report",
                key_fields=("report_id",),
                values=report_values,
            )
            _record_change(changes, "reports", result)

            for encounter in encounters:
                encounter_values = {
                    "encounter_id": str(encounter["encounter_id"]),
                    "source_encounter_id": str(encounter["source_encounter_id"]),
                    "report_id": str(encounter["report_id"]),
                    "boss_id": (
                        str(encounter["boss_id"])
                        if encounter.get("boss_id") is not None
                        else None
                    ),
                    "boss_name": str(encounter["name"]),
                    "started_at": _timestamp(encounter["start_time"], "encounter.start_time"),
                    "duration_ms": _duration_ms(encounter),
                    "success": bool(encounter["success"]),
                    "raid_size": (
                        int(encounter["player_count"])
                        if encounter.get("player_count") is not None
                        else None
                    ),
                    "raid_format": None,
                    "format_bucket": None,
                    "canonical_physical_fight_id": None,
                    "data_quality_status": "observed_parser_verified",
                }
                result = _merge_core_row(
                    connection,
                    table="encounter",
                    key_fields=("encounter_id",),
                    values=encounter_values,
                )
                _record_change(changes, "encounters", result)

            for actor in actors:
                actor_values = {
                    "actor_id": str(actor["actor_id"]),
                    "source_actor_id": str(actor["source_actor_id"]),
                    "nickname": str(actor["name"]),
                    "actor_type": str(actor["actor_type"]),
                    "owner_actor_id": None,
                    "first_seen_at": exact_started_at,
                    "last_seen_at": exact_ended_at,
                }
                result = _merge_core_row(
                    connection,
                    table="actor",
                    key_fields=("actor_id",),
                    values=actor_values,
                    range_fields={"first_seen_at": "min", "last_seen_at": "max"},
                )
                _record_change(changes, "actors", result)

            for participant in participants:
                actor_id = str(participant["actor_id"])
                actor = actor_by_id[actor_id]
                participant_values = {
                    "encounter_id": str(participant["encounter_id"]),
                    "actor_id": actor_id,
                    "player_id": None,
                    "character_id": None,
                    "nickname": str(actor["name"]),
                    "class_code": (
                        str(actor["class"]) if actor.get("class") is not None else None
                    ),
                    "spec_code": str(actor["spec"]) if actor.get("spec") is not None else None,
                    "role_code": None,
                    "participation_status": "observed_parser_verified",
                }
                result = _merge_core_row(
                    connection,
                    table="participant",
                    key_fields=("encounter_id", "actor_id"),
                    values=participant_values,
                )
                _record_change(changes, "participants", result)

            report_batch_id = batch_ids["coa-report-detail-v1"]
            encounter_batch_id = batch_ids["coa-encounter-detail-v1"]
            observation_counts = {name: 0 for name in ("reports", "encounters", "actors", "participants")}
            entity_sets = {
                "reports": reports,
                "encounters": encounters,
                "actors": actors,
                "participants": participants,
            }
            for entity_type, rows in entity_sets.items():
                for record in rows:
                    if entity_type == "reports":
                        entity_key = str(record["report_id"])
                        source_batch_ids = [encounter_batch_id, report_batch_id]
                    elif entity_type == "encounters":
                        entity_key = str(record["encounter_id"])
                        source_batch_ids = (
                            [encounter_batch_id, report_batch_id]
                            if entity_key == exact_encounter_id
                            else [report_batch_id]
                        )
                    elif entity_type == "actors":
                        entity_key = str(record["actor_id"])
                        source_batch_ids = [encounter_batch_id]
                    else:
                        entity_key = f"{record['encounter_id']}:{record['actor_id']}"
                        source_batch_ids = [encounter_batch_id]
                    entity_json = _canonical_json(record)
                    entity_hash = hashlib.sha256(entity_json.encode("utf-8")).hexdigest()
                    observation_values = {
                        "observation_id": _stable_id(
                            "canonical_entity_observation",
                            persistence_run_id,
                            entity_type,
                            entity_key,
                        ),
                        "persistence_run_id": persistence_run_id,
                        "entity_type": entity_type,
                        "entity_key": entity_key,
                        "entity_hash": entity_hash,
                        "source_batch_ids_json": _canonical_json(sorted(source_batch_ids)),
                        "provenance_type": "upstream_derived",
                        "trust_status": "observed",
                        "entity_json": entity_json,
                    }
                    result = _strict_insert_or_match(
                        connection,
                        table="canonical_entity_observation",
                        key_fields=("observation_id",),
                        values=observation_values,
                    )
                    _record_change(changes, "canonical_entity_observations", result)
                    observation_counts[entity_type] += 1

            persisted_counts = {
                "reports": connection.execute(
                    "SELECT COUNT(*) FROM report WHERE report_id = ?", [report_id]
                ).fetchone()[0],
                "encounters": connection.execute(
                    "SELECT COUNT(*) FROM encounter WHERE report_id = ?", [report_id]
                ).fetchone()[0],
                "actors": connection.execute(
                    """
                    SELECT COUNT(DISTINCT actor_id) FROM participant
                    WHERE encounter_id = ?
                    """,
                    [exact_encounter_id],
                ).fetchone()[0],
                "participants": connection.execute(
                    "SELECT COUNT(*) FROM participant WHERE encounter_id = ?",
                    [exact_encounter_id],
                ).fetchone()[0],
                "aura_events": connection.execute(
                    "SELECT COUNT(*) FROM aura_event WHERE encounter_id = ?",
                    [exact_encounter_id],
                ).fetchone()[0],
                "rejects": 0,
            }
            if persisted_counts != _EXPECTED_COUNTS:
                raise ValueError(
                    f"persisted selected parser counts mismatch: expected={_EXPECTED_COUNTS} "
                    f"actual={persisted_counts}"
                )
            integrity_checks["core_entity_counts_match"] = True
            if observation_counts != {
                "reports": 1,
                "encounters": 14,
                "actors": 31,
                "participants": 31,
            }:
                raise ValueError("canonical entity observation counts mismatch")
            integrity_checks["canonical_observation_counts_match"] = True

            unresolved = connection.execute(
                """
                SELECT COUNT(*)
                FROM participant p
                LEFT JOIN encounter e ON e.encounter_id = p.encounter_id
                LEFT JOIN actor a ON a.actor_id = p.actor_id
                WHERE p.encounter_id = ? AND (e.encounter_id IS NULL OR a.actor_id IS NULL)
                """,
                [exact_encounter_id],
            ).fetchone()[0]
            if unresolved != 0:
                raise ValueError("persisted participant references are unresolved")
            integrity_checks["participant_references_resolved"] = True

            run_values = {
                "persistence_run_id": persistence_run_id,
                "reconstruction_sha256": reconstructed_hash,
                "reconstruction_version": _RECONSTRUCTION_VERSION,
                "source_code": _SOURCE_CODE,
                "source_normalization_name": normalization_path.name,
                "status": "completed",
                "input_counts_json": _canonical_json(_EXPECTED_COUNTS),
                "persisted_counts_json": _canonical_json(persisted_counts),
                "source_batch_hashes_json": _canonical_json(
                    {
                        mapping_id: normalization_rows[mapping_id]["normalized_batch_sha256"]
                        for mapping_id in sorted(normalization_rows)
                    }
                ),
                "metadata_json": _canonical_json(
                    {
                        "persistence_version": _PERSISTENCE_VERSION,
                        "reconstruction_receipt": reconstruction_path.name,
                        "reconstructed_output": reconstructed_output_path.name,
                        "normalization_receipt": normalization_path.name,
                        "mechanic_semantics_verified": False,
                        "full_report_slice_complete": False,
                    }
                ),
                "finished_at": datetime.now(timezone.utc).replace(tzinfo=None),
            }
            result = _strict_insert_or_match(
                connection,
                table="parser_slice_persistence_run",
                key_fields=("persistence_run_id",),
                values=run_values,
            )
            _record_change(changes, "persistence_runs", result)
            connection.execute("COMMIT")
            integrity_checks["transaction_committed"] = True
        except Exception:
            connection.execute("ROLLBACK")
            raise

    if any(value is not True for value in integrity_checks.values()):
        raise ValueError("selected parser persistence integrity checks are incomplete")

    return {
        "schema_version": _PERSISTENCE_SCHEMA_VERSION,
        "persistence_kind": "observed_report_slice_selected_parser_persistence",
        "persistence_version": _PERSISTENCE_VERSION,
        "generated_at": _generated_at(),
        "source_reconstruction_name": reconstruction_path.name,
        "source_normalization_name": normalization_path.name,
        "reconstructed_output_sha256": reconstructed_hash,
        "persistence_run_id": persistence_run_id,
        "database_file": database_path.name,
        "applied_migrations": applied_migrations,
        "source_batches": source_batches,
        "persisted_counts": dict(_EXPECTED_COUNTS),
        "database_changes": changes,
        "integrity_checks": integrity_checks,
        "decision_boundary": {
            "status": "persisted_parser_slice",
            "selected_parser_persistence_completed": True,
            "ready_for_parser_observation_queries": True,
            "ready_for_combatants_info_mapping_review": True,
            "automatic_commit": False,
            "database_contains_source_scalar_values": True,
            "mechanic_semantics_verified": False,
            "combatants_info_enrichment_available": False,
            "aura_reconstruction_available": False,
            "full_report_slice_complete": False,
            "planner_scoring_allowed": False,
        },
        "summary": {
            "source_batch_count": 2,
            "mapping_count": 2,
            "persistence_run_count": 1,
            "persisted_counts": dict(_EXPECTED_COUNTS),
            "canonical_entity_observation_count": 77,
            "all_mapping_hashes_verified": True,
            "all_raw_objects_verified": True,
            "all_integrity_checks_passed": True,
            "transaction_committed": True,
            "contains_source_scalar_values": False,
            "database_contains_source_scalar_values": True,
            "ready_for_parser_observation_queries": True,
            "ready_for_combatants_info_mapping_review": True,
            "mechanic_semantics_verified": False,
            "full_report_slice_complete": False,
            "planner_scoring_allowed": False,
        },
    }
