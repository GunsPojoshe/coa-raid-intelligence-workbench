from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from coa_workbench.normalizer.canonical import stable_id

_PROMOTION_SCHEMA_VERSION = 1
_PROMOTION_VERSION = "combatants-candidate-promotion-v1"
_EXTRACTION_KIND = "observed_combatants_info_candidate_extraction"
_EXTRACTION_VERSION = "combatants-candidate-extractor-v1"
_PRIVATE_EXTRACTION_KIND = "observed_combatants_info_candidate_extraction_batch"
_SOURCE_CODE = "coa_ascension_logs"
_PAYLOAD_HASH = "45672e0f0ff9eb461c575bdd38385795daa6326378bc3f8ad51474276140dc14"
_SCHEMA_FINGERPRINT = "41d6d15422c668f83d2ccae1ec0ff2969671861f9e43b21cb371578961c5f8ff"

_EXPECTED_DESIGNS: dict[str, dict[str, Any]] = {
    "coa-combatants-actor-enrichment-v1": {
        "design_type": "actor_enrichment_observation",
        "entity_type": "actor_enrichment_observation",
        "selected_field_count": 14,
        "source_match_count": 11,
        "output_observation_count": 11,
        "deduplicated_source_match_count": 0,
        "mode": "actor",
    },
    "coa-combatants-instance-context-v1": {
        "design_type": "deduplicated_context_observation",
        "entity_type": "combatants_instance_context_observation",
        "selected_field_count": 8,
        "source_match_count": 11,
        "output_observation_count": 4,
        "deduplicated_source_match_count": 7,
        "mode": "context",
    },
    "coa-combatants-talent-container-v1": {
        "design_type": "nested_parser_observation",
        "entity_type": "combatants_talent_container_observation",
        "selected_field_count": 3,
        "source_match_count": 11,
        "output_observation_count": 11,
        "deduplicated_source_match_count": 0,
        "mode": "nested",
    },
    "coa-combatants-classless-talent-rank-v1": {
        "design_type": "nested_parser_observation",
        "entity_type": "combatants_classless_talent_rank_observation",
        "selected_field_count": 5,
        "source_match_count": 564,
        "output_observation_count": 564,
        "deduplicated_source_match_count": 0,
        "mode": "nested",
    },
    "coa-combatants-hero-build-entry-v1": {
        "design_type": "nested_parser_observation",
        "entity_type": "combatants_hero_build_entry_observation",
        "selected_field_count": 2,
        "source_match_count": 564,
        "output_observation_count": 564,
        "deduplicated_source_match_count": 0,
        "mode": "nested",
    },
    "coa-combatants-gear-slot-v1": {
        "design_type": "nested_parser_observation",
        "entity_type": "combatants_gear_slot_observation",
        "selected_field_count": 5,
        "source_match_count": 189,
        "output_observation_count": 189,
        "deduplicated_source_match_count": 0,
        "mode": "nested",
    },
}

_BASE_OBSERVATION_FIELDS = {
    "observation_id",
    "design_id",
    "entity_type",
    "report_id",
    "encounter_id",
    "actor_id",
    "source_actor_id",
    "raw_match_path",
    "selected_record_sha256",
    "selected_fields",
    "trust_status",
}
_CONTEXT_FIELDS = {
    "linked_actor_ids",
    "linked_source_actor_ids",
    "source_raw_match_paths",
}
_EXPECTED_INTEGRITY_CHECKS = {
    "all_actor_names_exact_match",
    "all_actor_stable_ids_verified",
    "all_record_hashes_created",
    "all_selected_field_types_verified",
    "all_source_match_counts_verified",
    "core_entity_mutation_not_performed",
    "exact_mapping_design_verified",
    "exact_observation_manifest_verified",
    "exact_raw_archive_verified",
    "persisted_encounter_reference_verified",
    "persisted_report_reference_verified",
    "route_context_verified",
}


def _generated_at() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _load_object(path: Path, label: str) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{label} must contain a JSON object")
    return payload


def _required_object(value: object, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"combatants promotion field {field_name} must be an object")
    return value


def _required_list(value: object, field_name: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"combatants promotion field {field_name} must be an array")
    return value


def _required_string(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"combatants promotion field {field_name} must be a non-empty string")
    prepared = value.strip()
    if "\n" in prepared or "\r" in prepared:
        raise ValueError(f"combatants promotion field {field_name} must be one line")
    return prepared


def _required_sha256(value: object, field_name: str) -> str:
    prepared = _required_string(value, field_name).casefold()
    if len(prepared) != 64 or any(character not in "0123456789abcdef" for character in prepared):
        raise ValueError(f"combatants promotion field {field_name} must be a SHA-256 digest")
    return prepared


def _reviewed_at(value: object) -> str:
    prepared = _required_string(value, "reviewed_at")
    parse_value = prepared[:-1] + "+00:00" if prepared.endswith("Z") else prepared
    try:
        parsed = datetime.fromisoformat(parse_value)
    except ValueError as error:
        raise ValueError("combatants promotion reviewed_at must be ISO-8601") from error
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("combatants promotion reviewed_at must include a timezone offset")
    return prepared


def _canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256_json(value: object) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _hash_multiset(values: list[str]) -> str:
    return _sha256_json(sorted(values))


def _validate_extraction_receipt(
    receipt: Mapping[str, Any],
    *,
    private_path: Path,
    private_sha256: str,
) -> dict[str, dict[str, Any]]:
    if receipt.get("schema_version") != 1:
        raise ValueError("unsupported combatants candidate extraction schema version")
    if receipt.get("extraction_kind") != _EXTRACTION_KIND:
        raise ValueError("unexpected combatants candidate extraction kind")
    if receipt.get("extraction_version") != _EXTRACTION_VERSION:
        raise ValueError("unexpected combatants candidate extraction version")
    if receipt.get("source_payload_hash") != _PAYLOAD_HASH:
        raise ValueError("combatants candidate extraction payload hash mismatch")
    if receipt.get("schema_fingerprint") != _SCHEMA_FINGERPRINT:
        raise ValueError("combatants candidate extraction schema fingerprint mismatch")
    if receipt.get("private_extraction_file") != private_path.name:
        raise ValueError("combatants private extraction filename mismatch")
    if _required_sha256(receipt.get("private_extraction_sha256"), "private_extraction_sha256") != private_sha256:
        raise ValueError("combatants private extraction content hash mismatch")

    checks = _required_object(receipt.get("integrity_checks"), "integrity_checks")
    if set(checks) != _EXPECTED_INTEGRITY_CHECKS or any(value is not True for value in checks.values()):
        raise ValueError("combatants candidate extraction integrity checks are incomplete")

    summary = _required_object(receipt.get("summary"), "summary")
    expected_summary = {
        "design_count": 6,
        "selected_field_contract_count": 37,
        "source_match_count": 1350,
        "output_observation_count": 1343,
        "linked_actor_count": 11,
        "actor_name_exact_match_count": 11,
        "deduplicated_source_match_count": 7,
        "exact_raw_archive_count": 1,
        "integrity_check_count": 12,
        "all_integrity_checks_passed": True,
        "contains_source_scalar_values": False,
        "private_extraction_contains_source_scalar_values": True,
        "candidate_mapping_files_ready": False,
        "automatic_persistence": False,
        "ready_for_manual_candidate_extraction_validation": True,
        "combatants_info_enrichment_available": False,
        "normalization_allowed": False,
        "planner_scoring_allowed": False,
    }
    for field_name, expected in expected_summary.items():
        if summary.get(field_name) != expected:
            raise ValueError(f"combatants candidate extraction summary mismatch: {field_name}")

    boundary = _required_object(receipt.get("decision_boundary"), "decision_boundary")
    expected_boundary = {
        "status": "candidate_extracted",
        "automatic_persistence": False,
        "candidate_mapping_files_ready": False,
        "actor_merge_verified_for_exact_payload": True,
        "route_context_verified_for_exact_payload": True,
        "companion_addon_provenance_verified": False,
        "nested_collection_semantics_verified": False,
        "can_promote": False,
        "combatants_info_enrichment_available": False,
        "normalization_allowed": False,
        "mechanic_semantics_verified": False,
        "planner_scoring_allowed": False,
        "ready_for_manual_candidate_extraction_validation": True,
        "private_extraction_contains_source_scalar_values": True,
    }
    for field_name, expected in expected_boundary.items():
        if boundary.get(field_name) != expected:
            raise ValueError(f"combatants candidate extraction boundary mismatch: {field_name}")

    rows: dict[str, dict[str, Any]] = {}
    for raw_row in _required_list(receipt.get("design_results"), "design_results"):
        row = _required_object(raw_row, "design_results[]")
        design_id = _required_string(row.get("design_id"), "design_id")
        expected = _EXPECTED_DESIGNS.get(design_id)
        if expected is None or design_id in rows:
            raise ValueError(f"unsupported or duplicated combatants extraction design: {design_id}")
        expected_fields = {
            "design_type": expected["design_type"],
            "target_entity_type": expected["entity_type"],
            "selected_field_count": expected["selected_field_count"],
            "source_match_count": expected["source_match_count"],
            "output_observation_count": expected["output_observation_count"],
            "deduplicated_source_match_count": expected["deduplicated_source_match_count"],
            "all_selected_field_types_verified": True,
            "all_actor_links_verified": True,
            "all_record_hashes_created": True,
            "core_entity_mutation_performed": False,
        }
        for field_name, expected_value in expected_fields.items():
            if row.get(field_name) != expected_value:
                raise ValueError(f"combatants extraction design mismatch: {design_id} {field_name}")
        rows[design_id] = row
    if set(rows) != set(_EXPECTED_DESIGNS):
        raise ValueError("combatants candidate extraction design set mismatch")
    return rows


def _validate_common_observation(
    row: Mapping[str, Any],
    *,
    design_id: str,
    expected: Mapping[str, Any],
    report_id: str,
    encounter_id: str,
    allowed_fields: set[str],
) -> tuple[str, str, dict[str, Any]]:
    if set(row) != allowed_fields:
        raise ValueError(f"combatants observation field set mismatch: {design_id}")
    observation_id = _required_sha256(row.get("observation_id"), "observation_id")
    if row.get("design_id") != design_id:
        raise ValueError(f"combatants observation design mismatch: {design_id}")
    if row.get("entity_type") != expected["entity_type"]:
        raise ValueError(f"combatants observation entity type mismatch: {design_id}")
    if row.get("report_id") != report_id or row.get("encounter_id") != encounter_id:
        raise ValueError(f"combatants observation route context mismatch: {design_id}")
    if row.get("trust_status") != "observed_candidate":
        raise ValueError(f"combatants observation trust status mismatch: {design_id}")
    selected_fields = _required_object(row.get("selected_fields"), "selected_fields")
    if len(selected_fields) != expected["selected_field_count"]:
        raise ValueError(f"combatants selected field count mismatch: {design_id}")
    selected_hash = _required_sha256(row.get("selected_record_sha256"), "selected_record_sha256")
    if _sha256_json(selected_fields) != selected_hash:
        raise ValueError(f"combatants selected record hash mismatch: {design_id}")
    actor_id = row.get("actor_id")
    raw_path = row.get("raw_match_path")
    expected_id = stable_id(
        "combatants_candidate_observation",
        design_id,
        _PAYLOAD_HASH,
        raw_path or "<no-raw-path>",
        selected_hash,
        actor_id or "",
    )
    if observation_id != expected_id:
        raise ValueError(f"combatants observation stable id mismatch: {design_id}")
    return observation_id, selected_hash, selected_fields


def _validate_private_batch(
    payload: Mapping[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if payload.get("schema_version") != 1:
        raise ValueError("unsupported private combatants extraction schema version")
    if payload.get("extraction_kind") != _PRIVATE_EXTRACTION_KIND:
        raise ValueError("unexpected private combatants extraction kind")
    if payload.get("extraction_version") != _EXTRACTION_VERSION:
        raise ValueError("unexpected private combatants extraction version")
    if payload.get("source_code") != _SOURCE_CODE:
        raise ValueError("private combatants extraction source code mismatch")
    if payload.get("source_payload_hash") != _PAYLOAD_HASH:
        raise ValueError("private combatants extraction payload hash mismatch")
    if payload.get("schema_fingerprint") != _SCHEMA_FINGERPRINT:
        raise ValueError("private combatants extraction schema fingerprint mismatch")

    for field_name in (
        "raw_id",
        "observation_id",
        "source_report_id",
        "source_encounter_id",
        "report_id",
        "encounter_id",
    ):
        _required_string(payload.get(field_name), field_name)
    report_id = str(payload["report_id"])
    encounter_id = str(payload["encounter_id"])

    private_summary = _required_object(payload.get("summary"), "private summary")
    expected_private_summary = {
        "design_count": 6,
        "selected_field_contract_count": 37,
        "source_match_count": 1350,
        "output_observation_count": 1343,
        "linked_actor_count": 11,
        "actor_name_exact_match_count": 11,
        "deduplicated_source_match_count": 7,
    }
    if private_summary != expected_private_summary:
        raise ValueError("private combatants extraction summary mismatch")

    observations = _required_object(payload.get("observations"), "observations")
    if set(observations) != set(_EXPECTED_DESIGNS):
        raise ValueError("private combatants extraction design set mismatch")

    all_observation_ids: set[str] = set()
    actor_map: dict[str, str] = {}
    promoted_rows: list[dict[str, Any]] = []

    actor_design_id = "coa-combatants-actor-enrichment-v1"
    actor_expected = _EXPECTED_DESIGNS[actor_design_id]
    actor_rows = _required_list(observations.get(actor_design_id), actor_design_id)
    if len(actor_rows) != actor_expected["output_observation_count"]:
        raise ValueError("combatants actor enrichment observation count mismatch")
    for raw_row in actor_rows:
        row = _required_object(raw_row, f"{actor_design_id}[]")
        observation_id, _record_hash, _selected_fields = _validate_common_observation(
            row,
            design_id=actor_design_id,
            expected=actor_expected,
            report_id=report_id,
            encounter_id=encounter_id,
            allowed_fields=_BASE_OBSERVATION_FIELDS,
        )
        actor_id = _required_sha256(row.get("actor_id"), "actor_id")
        source_actor_id = _required_string(row.get("source_actor_id"), "source_actor_id")
        _required_string(row.get("raw_match_path"), "raw_match_path")
        if source_actor_id in actor_map or actor_id in actor_map.values():
            raise ValueError("combatants actor enrichment linkage is duplicated")
        actor_map[source_actor_id] = actor_id
        if observation_id in all_observation_ids:
            raise ValueError("combatants observation id is duplicated")
        all_observation_ids.add(observation_id)

    if len(actor_map) != 11:
        raise ValueError("combatants actor enrichment linkage count mismatch")

    for design_id in sorted(_EXPECTED_DESIGNS):
        expected = _EXPECTED_DESIGNS[design_id]
        rows = _required_list(observations.get(design_id), design_id)
        if len(rows) != expected["output_observation_count"]:
            raise ValueError(f"combatants output observation count mismatch: {design_id}")

        observation_ids: list[str] = []
        record_hashes: list[str] = []
        raw_paths: set[str] = set()
        linked_source_actors: set[str] = set()

        for raw_row in rows:
            row = _required_object(raw_row, f"{design_id}[]")
            allowed = _BASE_OBSERVATION_FIELDS | (_CONTEXT_FIELDS if expected["mode"] == "context" else set())
            observation_id, record_hash, _selected_fields = _validate_common_observation(
                row,
                design_id=design_id,
                expected=expected,
                report_id=report_id,
                encounter_id=encounter_id,
                allowed_fields=allowed,
            )
            observation_ids.append(observation_id)
            record_hashes.append(record_hash)

            if design_id != actor_design_id:
                if observation_id in all_observation_ids:
                    raise ValueError("combatants observation id is duplicated")
                all_observation_ids.add(observation_id)

            if expected["mode"] == "context":
                if row.get("actor_id") is not None or row.get("source_actor_id") is not None:
                    raise ValueError("combatants context observation must not have a single actor")
                if row.get("raw_match_path") is not None:
                    raise ValueError("combatants context observation must use source raw path list")
                actor_ids = _required_list(row.get("linked_actor_ids"), "linked_actor_ids")
                source_actor_ids = _required_list(
                    row.get("linked_source_actor_ids"), "linked_source_actor_ids"
                )
                source_paths = _required_list(row.get("source_raw_match_paths"), "source_raw_match_paths")
                if not actor_ids or len(actor_ids) != len(source_actor_ids) or len(actor_ids) != len(source_paths):
                    raise ValueError("combatants context linkage arrays are inconsistent")
                if len(set(actor_ids)) != len(actor_ids) or len(set(source_actor_ids)) != len(source_actor_ids):
                    raise ValueError("combatants context linkage arrays contain duplicates")
                for actor_id, source_actor_id, source_path in zip(
                    actor_ids, source_actor_ids, source_paths, strict=True
                ):
                    prepared_actor_id = _required_sha256(actor_id, "linked_actor_id")
                    prepared_source_actor_id = _required_string(source_actor_id, "linked_source_actor_id")
                    _required_string(source_path, "source_raw_match_path")
                    if actor_map.get(prepared_source_actor_id) != prepared_actor_id:
                        raise ValueError("combatants context actor linkage mismatch")
                    if prepared_source_actor_id in linked_source_actors:
                        raise ValueError("combatants context source actor is linked more than once")
                    linked_source_actors.add(prepared_source_actor_id)
            else:
                actor_id = _required_sha256(row.get("actor_id"), "actor_id")
                source_actor_id = _required_string(row.get("source_actor_id"), "source_actor_id")
                raw_path = _required_string(row.get("raw_match_path"), "raw_match_path")
                if actor_map.get(source_actor_id) != actor_id:
                    raise ValueError(f"combatants observation actor linkage mismatch: {design_id}")
                if expected["mode"] == "nested" and raw_path in raw_paths:
                    raise ValueError(f"combatants nested raw path is duplicated: {design_id}")
                raw_paths.add(raw_path)
                linked_source_actors.add(source_actor_id)

        if expected["mode"] == "context" and linked_source_actors != set(actor_map):
            raise ValueError("combatants context observations do not cover the exact actor set")
        if expected["mode"] != "context" and linked_source_actors != set(actor_map):
            raise ValueError(f"combatants design does not cover the exact actor set: {design_id}")

        promoted_rows.append(
            {
                "design_id": design_id,
                "design_type": expected["design_type"],
                "target_entity_type": expected["entity_type"],
                "status": "verified_parser_observation",
                "selected_field_count": expected["selected_field_count"],
                "source_match_count": expected["source_match_count"],
                "output_observation_count": expected["output_observation_count"],
                "deduplicated_source_match_count": expected["deduplicated_source_match_count"],
                "observation_id_multiset_sha256": _hash_multiset(observation_ids),
                "selected_record_hash_multiset_sha256": _hash_multiset(record_hashes),
                "actor_linkage_verified": True,
                "route_context_verified": True,
                "selected_field_types_verified": True,
                "record_hashes_verified": True,
                "semantic_uniqueness_verified": False,
                "gameplay_semantics_verified": False,
                "core_entity_mutation_allowed": False,
            }
        )

    if len(all_observation_ids) != 1343:
        raise ValueError("combatants promoted observation id count mismatch")

    aggregate = {
        "design_count": len(promoted_rows),
        "selected_field_contract_count": 37,
        "source_match_count": sum(row["source_match_count"] for row in promoted_rows),
        "output_observation_count": sum(row["output_observation_count"] for row in promoted_rows),
        "deduplicated_source_match_count": sum(
            row["deduplicated_source_match_count"] for row in promoted_rows
        ),
        "linked_actor_count": len(actor_map),
        "observation_id_multiset_sha256": _hash_multiset(sorted(all_observation_ids)),
    }
    if aggregate["source_match_count"] != 1350 or aggregate["output_observation_count"] != 1343:
        raise ValueError("combatants promoted aggregate count mismatch")
    return promoted_rows, aggregate


def promote_observed_combatants_info_candidates(
    extraction_receipt_path: Path,
    private_extraction_path: Path,
    *,
    reviewed_by: str,
    reviewed_at: str,
) -> dict[str, Any]:
    """Validate the exact private candidate batch and return a scalar-free promotion receipt."""
    prepared_reviewer = _required_string(reviewed_by, "reviewed_by")
    prepared_reviewed_at = _reviewed_at(reviewed_at)

    private_body = private_extraction_path.read_bytes()
    private_sha256 = hashlib.sha256(private_body).hexdigest()
    receipt = _load_object(extraction_receipt_path, "combatants candidate extraction receipt")
    receipt_rows = _validate_extraction_receipt(
        receipt,
        private_path=private_extraction_path,
        private_sha256=private_sha256,
    )
    private_payload = json.loads(private_body)
    if not isinstance(private_payload, dict):
        raise ValueError("private combatants extraction must contain a JSON object")
    promoted_rows, aggregate = _validate_private_batch(private_payload)

    for row in promoted_rows:
        source = receipt_rows[row["design_id"]]
        if row["source_match_count"] != source["source_match_count"]:
            raise ValueError(f"combatants promoted source count mismatch: {row['design_id']}")
        if row["output_observation_count"] != source["output_observation_count"]:
            raise ValueError(f"combatants promoted output count mismatch: {row['design_id']}")

    checks = {
        "candidate_receipt_verified": True,
        "private_extraction_sha256_verified": True,
        "private_extraction_schema_verified": True,
        "exact_payload_binding_verified": True,
        "exact_route_context_consistent": True,
        "all_design_sets_verified": True,
        "all_output_counts_verified": True,
        "all_observation_ids_verified": True,
        "all_selected_record_hashes_verified": True,
        "all_selected_field_counts_verified": True,
        "all_actor_links_verified": True,
        "all_actor_sets_consistent": True,
        "all_nested_raw_paths_unique_per_design": True,
        "instance_context_deduplication_verified": True,
        "core_entity_mutation_not_allowed": True,
    }

    return {
        "schema_version": _PROMOTION_SCHEMA_VERSION,
        "promotion_kind": "observed_combatants_info_manual_candidate_promotion",
        "promotion_version": _PROMOTION_VERSION,
        "generated_at": _generated_at(),
        "source_extraction_receipt_name": extraction_receipt_path.name,
        "source_private_extraction_name": private_extraction_path.name,
        "source_private_extraction_sha256": private_sha256,
        "source_payload_hash": _PAYLOAD_HASH,
        "schema_fingerprint": _SCHEMA_FINGERPRINT,
        "reviewed_by": prepared_reviewer,
        "reviewed_at": prepared_reviewed_at,
        "verification_scope": (
            "exact_private_batch_schema_hash_counts_actor_linkage_route_context_and_record_hashes_only"
        ),
        "promoted_designs": promoted_rows,
        "integrity_checks": checks,
        "decision_boundary": {
            "status": "verified_parser_observation_batch",
            "automatic_promotion": False,
            "manual_promotion_completed": True,
            "automatic_persistence": False,
            "ready_for_immutable_observation_persistence": True,
            "core_entity_mutation_allowed": False,
            "actor_linkage_verified_for_exact_payload": True,
            "route_context_verified_for_exact_payload": True,
            "companion_addon_provenance_verified": False,
            "nested_collection_semantics_verified": False,
            "semantic_uniqueness_verified": False,
            "mechanic_semantics_verified": False,
            "combatants_info_enrichment_available": False,
            "planner_scoring_allowed": False,
            "private_extraction_contains_source_scalar_values": True,
        },
        "summary": {
            **aggregate,
            "integrity_check_count": len(checks),
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
        },
    }
