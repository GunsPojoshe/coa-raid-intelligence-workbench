from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from coa_workbench.collector.combatants_candidate_promotion import (
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


def _strict_insert_or_match(
    connection: Any,
    *,
    table: str,
    key_fields: tuple[str, ...],
    values: Mapping[str, Any],
) -> str:
    columns = list(values)
    where = " AND ".join(f"{field} = ?" for field in key_fields)
    existing = connection.execute(
        f"SELECT {', '.join(columns)} FROM {table} WHERE {where}",
        [values[field] for field in key_fields],
    ).fetchone()
    if existing is None:
        placeholders = ", ".join("?" for _ in columns)
        connection.execute(
            f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})",
            [values[field] for field in columns],
        )
        return "inserted"
    existing_values = dict(zip(columns, existing, strict=True))
    if existing_values != dict(values):
        raise ValueError(f"existing {table} row conflicts with verified combatants persistence")
    return "matched"


def _record_change(changes: dict[str, dict[str, int]], category: str, result: str) -> None:
    changes.setdefault(category, {"inserted": 0, "matched": 0})[result] += 1


def _core_snapshot(connection: Any, report_id: str, encounter_id: str, actor_ids: list[str]) -> dict[str, Any]:
    placeholders = ", ".join("?" for _ in actor_ids)
    return {
        "report": connection.execute("SELECT * FROM report WHERE report_id = ?", [report_id]).fetchall(),
        "encounter": connection.execute(
            "SELECT * FROM encounter WHERE encounter_id = ? AND report_id = ?",
            [encounter_id, report_id],
        ).fetchall(),
        "actors": connection.execute(
            f"SELECT * FROM actor WHERE actor_id IN ({placeholders}) ORDER BY actor_id",
            actor_ids,
        ).fetchall(),
        "participants": connection.execute(
            "SELECT * FROM participant WHERE encounter_id = ? ORDER BY actor_id",
            [encounter_id],
        ).fetchall(),
    }


def persist_observed_combatants_info_observations(
    promotion_path: Path,
    *,
    extraction_receipt_path: Path,
    private_extraction_path: Path,
    database_path: Path,
    migrations_path: Path,
) -> dict[str, Any]:
    """Persist the exact manually promoted combatants batch atomically and idempotently."""
    promotion, promotion_sha256 = _validate_promotion(
        promotion_path,
        extraction_receipt_path=extraction_receipt_path,
        private_extraction_path=private_extraction_path,
    )
    private_sha256 = _required_sha256(
        promotion.get("source_private_extraction_sha256"),
        "source_private_extraction_sha256",
    )
    payload = _load_private_batch(private_extraction_path, private_sha256)
    observations = _required_object(payload.get("observations"), "observations")
    report_id = _required_sha256(payload.get("report_id"), "report_id")
    encounter_id = _required_sha256(payload.get("encounter_id"), "encounter_id")

    promoted_designs = {
        _required_string(row.get("design_id"), "promoted_designs[].design_id"): row
        for raw_row in _required_list(promotion.get("promoted_designs"), "promoted_designs")
        for row in [_required_object(raw_row, "promoted_designs[]")]
    }
    if len(promoted_designs) != 6:
        raise ValueError("combatants promoted design set is incomplete")

    flattened: list[dict[str, Any]] = []
    entity_counts: dict[str, int] = {}
    actor_map: dict[str, str] = {}
    linked_actor_ids: set[str] = set()
    for design_id in sorted(observations):
        design = promoted_designs.get(design_id)
        if design is None:
            raise ValueError(f"combatants private batch has an unpromoted design: {design_id}")
        entity_type = _required_string(design.get("target_entity_type"), "target_entity_type")
        rows = _required_list(observations[design_id], f"observations.{design_id}")
        for raw_row in rows:
            row = _required_object(raw_row, f"observations.{design_id}[]")
            if row.get("design_id") != design_id or row.get("entity_type") != entity_type:
                raise ValueError(f"combatants persisted observation design mismatch: {design_id}")
            source_observation_id = _required_sha256(row.get("observation_id"), "observation_id")
            if row.get("trust_status") != "observed_candidate":
                raise ValueError(f"combatants source observation trust status changed: {design_id}")
            actor_id = row.get("actor_id")
            source_actor_id = row.get("source_actor_id")
            if actor_id is not None:
                prepared_actor_id = _required_sha256(actor_id, "actor_id")
                prepared_source_actor_id = _required_string(source_actor_id, "source_actor_id")
                linked_actor_ids.add(prepared_actor_id)
                if entity_type == "actor_enrichment_observation":
                    existing = actor_map.setdefault(prepared_source_actor_id, prepared_actor_id)
                    if existing != prepared_actor_id:
                        raise ValueError("combatants actor enrichment mapping conflicts")
            else:
                for linked_actor_id in _required_list(row.get("linked_actor_ids"), "linked_actor_ids"):
                    linked_actor_ids.add(_required_sha256(linked_actor_id, "linked_actor_id"))
            stored = deepcopy(row)
            stored["trust_status"] = "verified_parser_observation"
            flattened.append(
                {
                    "source_observation_id": source_observation_id,
                    "entity_type": entity_type,
                    "stored": stored,
                }
            )
            entity_counts[entity_type] = entity_counts.get(entity_type, 0) + 1

    if entity_counts != _EXPECTED_ENTITY_COUNTS:
        raise ValueError("combatants persistence entity counts do not match promoted batch")
    if len(flattened) != _EXPECTED_TOTAL_OBSERVATIONS:
        raise ValueError("combatants persistence observation count mismatch")
    if len(actor_map) != _EXPECTED_LINKED_ACTORS or len(linked_actor_ids) != _EXPECTED_LINKED_ACTORS:
        raise ValueError("combatants persistence linked actor set mismatch")

    persistence_run_id = _stable_id(
        "combatants_observation_persistence_run",
        private_sha256,
        _PERSISTENCE_VERSION,
    )
    source_batch_id = _stable_id("combatants_observation_batch", private_sha256, _PAYLOAD_HASH)
    reviewed_at = _timestamp(promotion.get("reviewed_at"), "reviewed_at")
    reviewed_by = _required_string(promotion.get("reviewed_by"), "reviewed_by")
    applied_migrations = apply_migrations(database_path, migrations_path)

    try:
        import duckdb
    except ImportError as error:  # pragma: no cover - runtime dependency guard
        raise RuntimeError("DuckDB is required for combatants observation persistence") from error

    changes: dict[str, dict[str, int]] = {}
    checks = {
        "exact_promotion_recomputed": True,
        "promotion_receipt_sha256_verified": True,
        "private_extraction_sha256_verified": True,
        "exact_payload_binding_verified": True,
        "all_promoted_designs_verified": True,
        "all_observation_counts_verified": True,
        "all_actor_links_verified": False,
        "persisted_report_reference_verified": False,
        "persisted_encounter_reference_verified": False,
        "transaction_committed": False,
        "canonical_observation_counts_match": False,
        "parser_read_model_counts_match": False,
        "actor_build_read_model_counts_match": False,
        "core_entity_rows_unchanged": False,
    }

    with duckdb.connect(str(database_path)) as connection:
        connection.execute("BEGIN TRANSACTION")
        try:
            actor_ids = sorted(linked_actor_ids)
            core_before = _core_snapshot(connection, report_id, encounter_id, actor_ids)
            if len(core_before["report"]) != 1:
                raise ValueError("combatants persistence report reference is missing")
            checks["persisted_report_reference_verified"] = True
            if len(core_before["encounter"]) != 1:
                raise ValueError("combatants persistence encounter reference is missing")
            checks["persisted_encounter_reference_verified"] = True
            if len(core_before["actors"]) != _EXPECTED_LINKED_ACTORS:
                raise ValueError("combatants persistence actor references are incomplete")
            persisted_actor_map = {str(row[1]): str(row[0]) for row in core_before["actors"]}
            if persisted_actor_map != actor_map:
                raise ValueError("combatants persistence actor source linkage mismatch")
            checks["all_actor_links_verified"] = True

            run_values = {
                "persistence_run_id": persistence_run_id,
                "promotion_receipt_sha256": promotion_sha256,
                "promotion_version": _PROMOTION_VERSION,
                "private_extraction_sha256": private_sha256,
                "source_payload_hash": _PAYLOAD_HASH,
                "schema_fingerprint": _SCHEMA_FINGERPRINT,
                "source_code": _SOURCE_CODE,
                "status": "completed",
                "design_counts_json": _canonical_json(_EXPECTED_ENTITY_COUNTS),
                "observation_count": _EXPECTED_TOTAL_OBSERVATIONS,
                "reviewed_by": reviewed_by,
                "reviewed_at": reviewed_at,
                "metadata_json": _canonical_json(
                    {
                        "persistence_version": _PERSISTENCE_VERSION,
                        "promotion_receipt": promotion_path.name,
                        "extraction_receipt": extraction_receipt_path.name,
                        "private_extraction": private_extraction_path.name,
                        "core_entity_mutation_allowed": False,
                        "planner_scoring_allowed": False,
                    }
                ),
            }
            result = _strict_insert_or_match(
                connection,
                table="combatants_observation_persistence_run",
                key_fields=("persistence_run_id",),
                values=run_values,
            )
            _record_change(changes, "persistence_runs", result)

            for item in flattened:
                entity_json = _canonical_json(item["stored"])
                entity_type = item["entity_type"]
                entity_key = item["source_observation_id"]
                values = {
                    "observation_id": _stable_id(
                        "canonical_entity_observation",
                        persistence_run_id,
                        entity_type,
                        entity_key,
                    ),
                    "persistence_run_id": persistence_run_id,
                    "entity_type": entity_type,
                    "entity_key": entity_key,
                    "entity_hash": _sha256_bytes(entity_json.encode("utf-8")),
                    "source_batch_ids_json": _canonical_json([source_batch_id]),
                    "provenance_type": "upstream_derived",
                    "trust_status": "verified_parser_observation",
                    "entity_json": entity_json,
                }
                result = _strict_insert_or_match(
                    connection,
                    table="canonical_entity_observation",
                    key_fields=("observation_id",),
                    values=values,
                )
                _record_change(changes, "canonical_entity_observations", result)

            persisted_count = connection.execute(
                """
                SELECT COUNT(*) FROM canonical_entity_observation
                WHERE persistence_run_id = ? AND trust_status = 'verified_parser_observation'
                """,
                [persistence_run_id],
            ).fetchone()[0]
            persisted_by_entity = {
                row[0]: row[1]
                for row in connection.execute(
                    """
                    SELECT entity_type, COUNT(*)
                    FROM canonical_entity_observation
                    WHERE persistence_run_id = ?
                    GROUP BY entity_type
                    ORDER BY entity_type
                    """,
                    [persistence_run_id],
                ).fetchall()
            }
            if persisted_count != _EXPECTED_TOTAL_OBSERVATIONS or persisted_by_entity != _EXPECTED_ENTITY_COUNTS:
                raise ValueError("persisted combatants canonical observation counts mismatch")
            checks["canonical_observation_counts_match"] = True

            parser_view_count = connection.execute(
                "SELECT COUNT(*) FROM combatants_parser_observation_v1 WHERE persistence_run_id = ?",
                [persistence_run_id],
            ).fetchone()[0]
            if parser_view_count != _EXPECTED_TOTAL_OBSERVATIONS:
                raise ValueError("combatants parser observation read model count mismatch")
            checks["parser_read_model_counts_match"] = True

            actor_build_count, distinct_actor_count = connection.execute(
                """
                SELECT COUNT(*), COUNT(DISTINCT actor_id)
                FROM combatants_actor_build_observation_v1
                WHERE persistence_run_id = ?
                """,
                [persistence_run_id],
            ).fetchone()
            if (
                actor_build_count != _EXPECTED_ACTOR_BUILD_OBSERVATIONS
                or distinct_actor_count != _EXPECTED_LINKED_ACTORS
            ):
                raise ValueError("combatants actor/build read model count mismatch")
            checks["actor_build_read_model_counts_match"] = True

            core_after = _core_snapshot(connection, report_id, encounter_id, actor_ids)
            if core_after != core_before:
                raise ValueError("combatants persistence modified core entity rows")
            checks["core_entity_rows_unchanged"] = True
            connection.execute("COMMIT")
            checks["transaction_committed"] = True
        except Exception:
            connection.execute("ROLLBACK")
            raise

    if any(value is not True for value in checks.values()):
        raise ValueError("combatants persistence integrity checks are incomplete")

    return {
        "schema_version": _PERSISTENCE_SCHEMA_VERSION,
        "persistence_kind": "observed_combatants_info_immutable_observation_persistence",
        "persistence_version": _PERSISTENCE_VERSION,
        "generated_at": _generated_at(),
        "source_promotion_name": promotion_path.name,
        "source_promotion_sha256": promotion_sha256,
        "source_extraction_receipt_name": extraction_receipt_path.name,
        "source_private_extraction_name": private_extraction_path.name,
        "source_private_extraction_sha256": private_sha256,
        "source_payload_hash": _PAYLOAD_HASH,
        "schema_fingerprint": _SCHEMA_FINGERPRINT,
        "persistence_run_id": persistence_run_id,
        "source_batch_id": source_batch_id,
        "database_file": database_path.name,
        "applied_migrations": applied_migrations,
        "persisted_entity_counts": dict(_EXPECTED_ENTITY_COUNTS),
        "database_changes": changes,
        "read_model_counts": {
            "parser_observations": _EXPECTED_TOTAL_OBSERVATIONS,
            "actor_build_observations": _EXPECTED_ACTOR_BUILD_OBSERVATIONS,
            "distinct_linked_actors": _EXPECTED_LINKED_ACTORS,
        },
        "integrity_checks": checks,
        "decision_boundary": {
            "status": "persisted_verified_parser_observations",
            "immutable_observation_persistence_completed": True,
            "automatic_persistence": False,
            "core_entity_mutation_performed": False,
            "ready_for_parser_observation_queries": True,
            "ready_for_actor_build_observation_queries": True,
            "database_contains_source_scalar_values": True,
            "companion_addon_provenance_verified": False,
            "nested_collection_semantics_verified": False,
            "semantic_uniqueness_verified": False,
            "mechanic_semantics_verified": False,
            "combatants_info_enrichment_available": False,
            "planner_scoring_allowed": False,
        },
        "summary": {
            "design_count": 6,
            "persisted_observation_count": _EXPECTED_TOTAL_OBSERVATIONS,
            "actor_build_observation_count": _EXPECTED_ACTOR_BUILD_OBSERVATIONS,
            "linked_actor_count": _EXPECTED_LINKED_ACTORS,
            "persistence_run_count": 1,
            "all_integrity_checks_passed": True,
            "transaction_committed": True,
            "contains_source_scalar_values": False,
            "database_contains_source_scalar_values": True,
            "core_entity_mutation_performed": False,
            "ready_for_parser_observation_queries": True,
            "ready_for_actor_build_observation_queries": True,
            "combatants_info_enrichment_available": False,
            "mechanic_semantics_verified": False,
            "planner_scoring_allowed": False,
        },
    }
