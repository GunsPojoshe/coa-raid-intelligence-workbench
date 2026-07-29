from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from coa_workbench.collector.combatants_candidate_promotion_compat import (
    promote_observed_combatants_info_candidates,
)

from .migrations import apply_migrations

_PERSISTENCE_SCHEMA_VERSION = 1
_PERSISTENCE_VERSION = "combatants-observation-persistence-v1"
_PROMOTION_KIND = "observed_combatants_info_manual_candidate_promotion"
_PROMOTION_VERSION = "combatants-candidate-promotion-v1"
_PRIVATE_EXTRACTION_KIND = "observed_combatants_info_candidate_extraction_batch"
_EXTRACTION_VERSION = "combatants-candidate-extractor-v1"
_SOURCE_CODE = "coa_ascension_logs"
_PAYLOAD_HASH = "45672e0f0ff9eb461c575bdd38385795daa6326378bc3f8ad51474276140dc14"
_SCHEMA_FINGERPRINT = "41d6d15422c668f83d2ccae1ec0ff2969671861f9e43b21cb371578961c5f8ff"

_EXPECTED_ENTITY_COUNTS = {
    "actor_enrichment_observation": 11,
    "combatants_classless_talent_rank_observation": 564,
    "combatants_gear_slot_observation": 189,
    "combatants_hero_build_entry_observation": 564,
    "combatants_instance_context_observation": 4,
    "combatants_talent_container_observation": 11,
}
_EXPECTED_TOTAL_OBSERVATIONS = 1343
_EXPECTED_ACTOR_BUILD_OBSERVATIONS = 1339
_EXPECTED_LINKED_ACTORS = 11


def _generated_at() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _load_object(path: Path, label: str) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{label} must contain a JSON object")
    return payload


def _required_object(value: object, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"combatants persistence field {field_name} must be an object")
    return value


def _required_list(value: object, field_name: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"combatants persistence field {field_name} must be an array")
    return value


def _required_string(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"combatants persistence field {field_name} must be a non-empty string")
    return value


def _required_sha256(value: object, field_name: str) -> str:
    prepared = _required_string(value, field_name).casefold()
    if len(prepared) != 64 or any(character not in "0123456789abcdef" for character in prepared):
        raise ValueError(f"combatants persistence field {field_name} must be a SHA-256 digest")
    return prepared


def _canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_json(value: object) -> str:
    return _sha256_bytes(_canonical_json(value).encode("utf-8"))


def _stable_id(entity: str, *parts: object) -> str:
    material = "\0".join([entity, *(str(part) for part in parts)])
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def _timestamp(value: object, field_name: str) -> datetime:
    prepared = _required_string(value, field_name)
    parse_value = prepared[:-1] + "+00:00" if prepared.endswith("Z") else prepared
    try:
        parsed = datetime.fromisoformat(parse_value)
    except ValueError as error:
        raise ValueError(f"combatants persistence field {field_name} must be ISO-8601") from error
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"combatants persistence field {field_name} must include timezone")
    return parsed.astimezone(timezone.utc).replace(tzinfo=None)


def _without_generated_at(payload: Mapping[str, Any]) -> dict[str, Any]:
    prepared = deepcopy(dict(payload))
    prepared.pop("generated_at", None)
    return prepared


def _validate_promotion(
    promotion_path: Path,
    *,
    extraction_receipt_path: Path,
    private_extraction_path: Path,
) -> tuple[dict[str, Any], str]:
    promotion_body = promotion_path.read_bytes()
    submitted = json.loads(promotion_body)
    if not isinstance(submitted, dict):
        raise ValueError("combatants promotion receipt must contain a JSON object")
    if submitted.get("schema_version") != 1:
        raise ValueError("unsupported combatants promotion schema version")
    if submitted.get("promotion_kind") != _PROMOTION_KIND:
        raise ValueError("unexpected combatants promotion kind")
    if submitted.get("promotion_version") != _PROMOTION_VERSION:
        raise ValueError("unexpected combatants promotion version")

    reviewed_by = _required_string(submitted.get("reviewed_by"), "reviewed_by")
    reviewed_at = _required_string(submitted.get("reviewed_at"), "reviewed_at")
    recomputed = promote_observed_combatants_info_candidates(
        extraction_receipt_path,
        private_extraction_path,
        reviewed_by=reviewed_by,
        reviewed_at=reviewed_at,
    )
    if _without_generated_at(submitted) != _without_generated_at(recomputed):
        raise ValueError("submitted combatants promotion does not match exact recomputed promotion")

    summary = _required_object(submitted.get("summary"), "promotion.summary")
    expected_summary = {
        "design_count": 6,
        "selected_field_contract_count": 37,
        "source_match_count": 1350,
        "output_observation_count": _EXPECTED_TOTAL_OBSERVATIONS,
        "deduplicated_source_match_count": 7,
        "linked_actor_count": _EXPECTED_LINKED_ACTORS,
        "integrity_check_count": 15,
        "all_integrity_checks_passed": True,
        "contains_source_scalar_values": False,
        "private_extraction_contains_source_scalar_values": True,
        "manual_promotion_completed": True,
        "automatic_persistence": False,
        "ready_for_immutable_observation_persistence": True,
        "core_entity_mutation_allowed": False,
        "companion_addon_provenance_verified": False,
        "nested_collection_semantics_verified": False,
        "mechanic_semantics_verified": False,
        "combatants_info_enrichment_available": False,
        "planner_scoring_allowed": False,
    }
    for field_name, expected in expected_summary.items():
        if summary.get(field_name) != expected:
            raise ValueError(f"combatants promotion summary mismatch: {field_name}")
    return submitted, _sha256_bytes(promotion_body)


def _load_private_batch(path: Path, expected_sha256: str) -> dict[str, Any]:
    body = path.read_bytes()
    if _sha256_bytes(body) != expected_sha256:
        raise ValueError("combatants private extraction content hash changed after promotion")
    payload = json.loads(body)
    if not isinstance(payload, dict):
        raise ValueError("combatants private extraction must contain a JSON object")
    expected_fields = {
        "schema_version": 1,
        "extraction_kind": _PRIVATE_EXTRACTION_KIND,
        "extraction_version": _EXTRACTION_VERSION,
        "source_code": _SOURCE_CODE,
        "source_payload_hash": _PAYLOAD_HASH,
        "schema_fingerprint": _SCHEMA_FINGERPRINT,
    }
    for field_name, expected in expected_fields.items():
        if payload.get(field_name) != expected:
            raise ValueError(f"combatants private extraction mismatch: {field_name}")
    return payload


def _core_snapshot(connection: Any) -> dict[str, list[tuple[Any, ...]]]:
    return {
        table: connection.execute(f"SELECT * FROM {table} ORDER BY ALL").fetchall()
        for table in ("report", "encounter", "actor", "participant")
    }


def _validate_core_references(connection: Any, private_payload: Mapping[str, Any]) -> None:
    report_id = _required_sha256(private_payload.get("report_id"), "report_id")
    encounter_id = _required_sha256(private_payload.get("encounter_id"), "encounter_id")
    report_rows = connection.execute(
        "SELECT report_id FROM report WHERE report_id = ?", [report_id]
    ).fetchall()
    if len(report_rows) != 1:
        raise ValueError("combatants persistence report reference is missing")
    encounter_rows = connection.execute(
        "SELECT encounter_id, report_id FROM encounter WHERE encounter_id = ?", [encounter_id]
    ).fetchall()
    if encounter_rows != [(encounter_id, report_id)]:
        raise ValueError("combatants persistence encounter reference is missing or inconsistent")

    observations = _required_object(private_payload.get("observations"), "observations")
    actor_rows = _required_list(
        observations.get("coa-combatants-actor-enrichment-v1"),
        "coa-combatants-actor-enrichment-v1",
    )
    expected_actor_rows = sorted(
        (
            _required_sha256(_required_object(row, "actor observation").get("actor_id"), "actor_id"),
            _required_string(_required_object(row, "actor observation").get("source_actor_id"), "source_actor_id"),
        )
        for row in actor_rows
    )
    persisted_actor_rows = connection.execute(
        "SELECT actor_id, source_actor_id FROM actor WHERE actor_id IN (SELECT UNNEST(?)) ORDER BY actor_id",
        [[row[0] for row in expected_actor_rows]],
    ).fetchall()
    if persisted_actor_rows != expected_actor_rows:
        raise ValueError("combatants persistence actor references are incomplete or inconsistent")


def _observation_rows(private_payload: Mapping[str, Any], persistence_run_id: str) -> list[list[Any]]:
    observations = _required_object(private_payload.get("observations"), "observations")
    rows: list[list[Any]] = []
    entity_counts: dict[str, int] = {}
    for design_id in sorted(observations):
        for raw_row in _required_list(observations.get(design_id), design_id):
            row = _required_object(raw_row, f"{design_id}[]")
            observation_id = _required_sha256(row.get("observation_id"), "observation_id")
            entity_type = _required_string(row.get("entity_type"), "entity_type")
            entity_hash = _required_sha256(row.get("selected_record_sha256"), "selected_record_sha256")
            actor_id = row.get("actor_id")
            entity_key = _required_sha256(actor_id, "actor_id") if actor_id is not None else observation_id
            if _sha256_json(_required_object(row.get("selected_fields"), "selected_fields")) != entity_hash:
                raise ValueError(f"combatants selected field hash changed before persistence: {design_id}")
            entity_counts[entity_type] = entity_counts.get(entity_type, 0) + 1
            rows.append(
                [
                    observation_id,
                    persistence_run_id,
                    entity_type,
                    entity_key,
                    entity_hash,
                    _canonical_json([private_payload.get("observation_id")]),
                    "exact_private_combatants_candidate_extraction",
                    "verified_parser_observation",
                    _canonical_json(row),
                ]
            )
    if entity_counts != _EXPECTED_ENTITY_COUNTS:
        raise ValueError("combatants persistence entity counts mismatch")
    if len(rows) != _EXPECTED_TOTAL_OBSERVATIONS:
        raise ValueError("combatants persistence observation count mismatch")
    return rows


def _upsert_exact(
    connection: Any,
    *,
    table: str,
    key_column: str,
    key_value: str,
    columns: list[str],
    values: list[Any],
) -> str:
    existing = connection.execute(
        f"SELECT {', '.join(columns)} FROM {table} WHERE {key_column} = ?",
        [key_value],
    ).fetchall()
    if existing:
        if existing != [tuple(values)]:
            raise ValueError(f"combatants persistence existing {table} row conflicts with exact batch")
        return "matched"
    placeholders = ", ".join("?" for _ in values)
    connection.execute(
        f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})",
        values,
    )
    return "inserted"


def persist_observed_combatants_info_observations(
    promotion_path: Path,
    *,
    extraction_receipt_path: Path,
    private_extraction_path: Path,
    database_path: Path,
    migrations_path: Path,
) -> dict[str, Any]:
    """Persist an exact promoted combatants parser-observation batch atomically and idempotently."""
    promotion, promotion_sha256 = _validate_promotion(
        promotion_path,
        extraction_receipt_path=extraction_receipt_path,
        private_extraction_path=private_extraction_path,
    )
    private_sha256 = _required_sha256(
        promotion.get("source_private_extraction_sha256"),
        "source_private_extraction_sha256",
    )
    private_payload = _load_private_batch(private_extraction_path, private_sha256)
    report_id = _required_sha256(private_payload.get("report_id"), "report_id")
    encounter_id = _required_sha256(private_payload.get("encounter_id"), "encounter_id")
    reviewed_at = _timestamp(promotion.get("reviewed_at"), "reviewed_at")
    persistence_run_id = _stable_id(
        "combatants_observation_persistence_run",
        promotion_sha256,
        private_sha256,
        report_id,
        encounter_id,
    )
    observation_rows = _observation_rows(private_payload, persistence_run_id)

    apply_migrations(database_path, migrations_path)
    try:
        import duckdb
    except ImportError as error:  # pragma: no cover - runtime packaging
        raise RuntimeError("DuckDB is required for combatants observation persistence") from error

    changes = {
        "persistence_runs": {"inserted": 0, "matched": 0},
        "canonical_entity_observations": {"inserted": 0, "matched": 0},
    }
    with duckdb.connect(str(database_path)) as connection:
        before_core = _core_snapshot(connection)
        connection.execute("BEGIN TRANSACTION")
        try:
            _validate_core_references(connection, private_payload)
            run_values = [
                persistence_run_id,
                promotion_sha256,
                private_sha256,
                _required_sha256(promotion.get("source_payload_hash"), "source_payload_hash"),
                _required_sha256(promotion.get("schema_fingerprint"), "schema_fingerprint"),
                _required_string(promotion.get("promotion_version"), "promotion_version"),
                _required_string(promotion.get("reviewed_by"), "reviewed_by"),
                reviewed_at,
                report_id,
                encounter_id,
                _EXPECTED_TOTAL_OBSERVATIONS,
                _EXPECTED_LINKED_ACTORS,
                _canonical_json(_EXPECTED_ENTITY_COUNTS),
                "persisted_verified_parser_observations",
            ]
            run_columns = [
                "persistence_run_id",
                "promotion_sha256",
                "private_extraction_sha256",
                "source_payload_hash",
                "schema_fingerprint",
                "promotion_version",
                "reviewed_by",
                "reviewed_at",
                "report_id",
                "encounter_id",
                "observation_count",
                "linked_actor_count",
                "entity_counts_json",
                "status",
            ]
            run_status = _upsert_exact(
                connection,
                table="combatants_observation_persistence_run",
                key_column="persistence_run_id",
                key_value=persistence_run_id,
                columns=run_columns,
                values=run_values,
            )
            changes["persistence_runs"][run_status] += 1

            observation_columns = [
                "observation_id",
                "persistence_run_id",
                "entity_type",
                "entity_key",
                "entity_hash",
                "source_batch_ids_json",
                "provenance_type",
                "trust_status",
                "entity_json",
            ]
            for values in observation_rows:
                status = _upsert_exact(
                    connection,
                    table="canonical_entity_observation",
                    key_column="observation_id",
                    key_value=values[0],
                    columns=observation_columns,
                    values=values,
                )
                changes["canonical_entity_observations"][status] += 1

            after_core = _core_snapshot(connection)
            if after_core != before_core:
                raise ValueError("combatants persistence attempted to mutate core entities")
            connection.execute("COMMIT")
        except Exception:
            connection.execute("ROLLBACK")
            raise

        parser_count = connection.execute(
            "SELECT COUNT(*) FROM combatants_parser_observation_v1 WHERE persistence_run_id = ?",
            [persistence_run_id],
        ).fetchone()[0]
        actor_build_count = connection.execute(
            "SELECT COUNT(*) FROM combatants_actor_build_observation_v1 WHERE persistence_run_id = ?",
            [persistence_run_id],
        ).fetchone()[0]
        distinct_actor_count = connection.execute(
            "SELECT COUNT(DISTINCT actor_id) FROM combatants_actor_build_observation_v1 "
            "WHERE persistence_run_id = ?",
            [persistence_run_id],
        ).fetchone()[0]
    if parser_count != _EXPECTED_TOTAL_OBSERVATIONS:
        raise ValueError("combatants parser observation read model count mismatch")
    if actor_build_count != _EXPECTED_ACTOR_BUILD_OBSERVATIONS:
        raise ValueError("combatants actor/build observation read model count mismatch")
    if distinct_actor_count != _EXPECTED_LINKED_ACTORS:
        raise ValueError("combatants actor/build linked actor count mismatch")

    checks = {
        "submitted_promotion_recomputed_exactly": True,
        "promotion_receipt_sha256_verified": True,
        "private_extraction_sha256_verified": True,
        "promotion_integrity_checks_verified": True,
        "report_reference_verified": True,
        "encounter_reference_verified": True,
        "all_actor_references_verified": True,
        "all_entity_counts_verified": True,
        "all_observation_hashes_verified": True,
        "all_existing_rows_exact_or_absent": True,
        "transaction_committed": True,
        "core_entity_snapshots_unchanged": True,
        "parser_read_model_verified": True,
        "actor_build_read_model_verified": True,
        "planner_scoring_not_enabled": True,
    }
    return {
        "schema_version": _PERSISTENCE_SCHEMA_VERSION,
        "persistence_kind": "observed_combatants_info_immutable_observation_persistence",
        "persistence_version": _PERSISTENCE_VERSION,
        "generated_at": _generated_at(),
        "source_promotion_name": promotion_path.name,
        "source_promotion_sha256": promotion_sha256,
        "source_private_extraction_name": private_extraction_path.name,
        "source_private_extraction_sha256": private_sha256,
        "source_payload_hash": _PAYLOAD_HASH,
        "schema_fingerprint": _SCHEMA_FINGERPRINT,
        "persistence_run_id": persistence_run_id,
        "persisted_entity_counts": dict(_EXPECTED_ENTITY_COUNTS),
        "database_changes": changes,
        "read_model_counts": {
            "parser_observations": parser_count,
            "actor_build_observations": actor_build_count,
            "distinct_linked_actors": distinct_actor_count,
        },
        "integrity_checks": checks,
        "decision_boundary": {
            "status": "persisted_verified_parser_observations",
            "immutable_observation_persistence_completed": True,
            "automatic_persistence": False,
            "core_entity_mutation_performed": False,
            "ready_for_parser_observation_queries": True,
            "ready_for_actor_build_observation_queries": True,
            "companion_addon_provenance_verified": False,
            "nested_collection_semantics_verified": False,
            "semantic_uniqueness_verified": False,
            "combatants_info_enrichment_available": False,
            "mechanic_semantics_verified": False,
            "planner_scoring_allowed": False,
            "database_contains_source_scalar_values": True,
        },
        "summary": {
            "design_count": 6,
            "persisted_observation_count": parser_count,
            "actor_build_observation_count": actor_build_count,
            "linked_actor_count": distinct_actor_count,
            "persistence_run_count": 1,
            "integrity_check_count": len(checks),
            "all_integrity_checks_passed": True,
            "transaction_committed": True,
            "core_entity_mutation_performed": False,
            "contains_source_scalar_values": False,
            "database_contains_source_scalar_values": True,
            "ready_for_parser_observation_queries": True,
            "ready_for_actor_build_observation_queries": True,
            "combatants_info_enrichment_available": False,
            "mechanic_semantics_verified": False,
            "planner_scoring_allowed": False,
        },
    }
