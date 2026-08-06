from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from coa_workbench.collector.combatants_candidate_promotion import (
    promote_observed_combatants_info_candidates,
)
from coa_workbench.normalizer.canonical import stable_id

_PAYLOAD_HASH = "45672e0f0ff9eb461c575bdd38385795daa6326378bc3f8ad51474276140dc14"
_FINGERPRINT = "41d6d15422c668f83d2ccae1ec0ff2969671861f9e43b21cb371578961c5f8ff"
_DESIGNS = {
    "coa-combatants-actor-enrichment-v1": ("actor_enrichment_observation", 14, 11, 11, 0),
    "coa-combatants-instance-context-v1": (
        "combatants_instance_context_observation",
        8,
        11,
        4,
        7,
    ),
    "coa-combatants-talent-container-v1": (
        "combatants_talent_container_observation",
        3,
        11,
        11,
        0,
    ),
    "coa-combatants-classless-talent-rank-v1": (
        "combatants_classless_talent_rank_observation",
        5,
        564,
        564,
        0,
    ),
    "coa-combatants-hero-build-entry-v1": (
        "combatants_hero_build_entry_observation",
        2,
        564,
        564,
        0,
    ),
    "coa-combatants-gear-slot-v1": (
        "combatants_gear_slot_observation",
        5,
        189,
        189,
        0,
    ),
}


def _canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256_json(value: object) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _write(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True), encoding="utf-8")


def _selected_fields(count: int, marker: str) -> dict[str, Any]:
    return {f"field_{index}": f"PRIVATE-{marker}-{index}" for index in range(count)}


def _observation(
    *,
    design_id: str,
    entity_type: str,
    selected_fields: dict[str, Any],
    report_id: str,
    encounter_id: str,
    actor_id: str | None,
    source_actor_id: str | None,
    raw_path: str | None,
) -> dict[str, Any]:
    record_hash = _sha256_json(selected_fields)
    observation_id = stable_id(
        "combatants_candidate_observation",
        design_id,
        _PAYLOAD_HASH,
        raw_path or "<no-raw-path>",
        record_hash,
        actor_id or "",
    )
    return {
        "observation_id": observation_id,
        "design_id": design_id,
        "entity_type": entity_type,
        "report_id": report_id,
        "encounter_id": encounter_id,
        "actor_id": actor_id,
        "source_actor_id": source_actor_id,
        "raw_match_path": raw_path,
        "selected_record_sha256": record_hash,
        "selected_fields": selected_fields,
        "trust_status": "observed_candidate",
    }


def _packet(tmp_path: Path) -> tuple[Path, Path]:
    report_id = stable_id("report", "PRIVATE-REPORT")
    encounter_id = stable_id("encounter", "PRIVATE-ENCOUNTER")
    actor_map = {
        str(index): stable_id("actor", "coa_ascension_logs", str(index))
        for index in range(1, 12)
    }

    observations: dict[str, list[dict[str, Any]]] = {}
    actor_design = "coa-combatants-actor-enrichment-v1"
    actor_entity, actor_field_count, *_ = _DESIGNS[actor_design]
    observations[actor_design] = [
        _observation(
            design_id=actor_design,
            entity_type=actor_entity,
            selected_fields=_selected_fields(actor_field_count, f"actor-{source_actor_id}"),
            report_id=report_id,
            encounter_id=encounter_id,
            actor_id=actor_id,
            source_actor_id=source_actor_id,
            raw_path=f"/combatants/{source_actor_id}/ci_resolved/player",
        )
        for source_actor_id, actor_id in actor_map.items()
    ]

    context_design = "coa-combatants-instance-context-v1"
    context_entity, context_field_count, *_ = _DESIGNS[context_design]
    source_groups = [["1", "2", "3"], ["4", "5", "6"], ["7", "8", "9"], ["10", "11"]]
    context_rows: list[dict[str, Any]] = []
    for group_index, source_actor_ids in enumerate(source_groups):
        row = _observation(
            design_id=context_design,
            entity_type=context_entity,
            selected_fields=_selected_fields(context_field_count, f"context-{group_index}"),
            report_id=report_id,
            encounter_id=encounter_id,
            actor_id=None,
            source_actor_id=None,
            raw_path=None,
        )
        row["linked_actor_ids"] = [actor_map[source_actor_id] for source_actor_id in source_actor_ids]
        row["linked_source_actor_ids"] = source_actor_ids
        row["source_raw_match_paths"] = [
            f"/combatants/{source_actor_id}/ci_resolved/instance"
            for source_actor_id in source_actor_ids
        ]
        context_rows.append(row)
    observations[context_design] = context_rows

    for design_id, (entity_type, field_count, _source_count, output_count, _dedup) in _DESIGNS.items():
        if design_id in observations:
            continue
        rows: list[dict[str, Any]] = []
        for index in range(output_count):
            source_actor_id = str((index % 11) + 1)
            rows.append(
                _observation(
                    design_id=design_id,
                    entity_type=entity_type,
                    selected_fields=_selected_fields(field_count, f"{design_id}-{index}"),
                    report_id=report_id,
                    encounter_id=encounter_id,
                    actor_id=actor_map[source_actor_id],
                    source_actor_id=source_actor_id,
                    raw_path=f"/combatants/{source_actor_id}/{design_id}/{index}",
                )
            )
        observations[design_id] = rows

    private_payload = {
        "schema_version": 1,
        "extraction_kind": "observed_combatants_info_candidate_extraction_batch",
        "extraction_version": "combatants-candidate-extractor-v1",
        "source_code": "coa_ascension_logs",
        "source_payload_hash": _PAYLOAD_HASH,
        "schema_fingerprint": _FINGERPRINT,
        "raw_id": "PRIVATE-RAW-ID",
        "observation_id": "PRIVATE-SOURCE-OBSERVATION-ID",
        "source_report_id": "PRIVATE-SOURCE-REPORT-ID",
        "source_encounter_id": "PRIVATE-SOURCE-ENCOUNTER-ID",
        "report_id": report_id,
        "encounter_id": encounter_id,
        "observations": observations,
        "summary": {
            "design_count": 6,
            "selected_field_contract_count": 37,
            "source_match_count": 1350,
            "output_observation_count": 1343,
            "linked_actor_count": 11,
            "actor_name_exact_match_count": 11,
            "deduplicated_source_match_count": 7,
        },
    }
    private_path = tmp_path / "observed-combatants-info.candidate-extraction.json"
    _write(private_path, private_payload)
    private_hash = hashlib.sha256(private_path.read_bytes()).hexdigest()

    design_results = []
    for design_id, (entity_type, field_count, source_count, output_count, dedup_count) in sorted(
        _DESIGNS.items()
    ):
        design_results.append(
            {
                "design_id": design_id,
                "design_type": (
                    "actor_enrichment_observation"
                    if design_id == actor_design
                    else (
                        "deduplicated_context_observation"
                        if design_id == context_design
                        else "nested_parser_observation"
                    )
                ),
                "target_entity_type": entity_type,
                "selected_field_count": field_count,
                "source_match_count": source_count,
                "output_observation_count": output_count,
                "deduplicated_source_match_count": dedup_count,
                "all_selected_field_types_verified": True,
                "all_actor_links_verified": True,
                "all_record_hashes_created": True,
                "core_entity_mutation_performed": False,
            }
        )

    integrity_checks = {
        "all_actor_names_exact_match": True,
        "all_actor_stable_ids_verified": True,
        "all_record_hashes_created": True,
        "all_selected_field_types_verified": True,
        "all_source_match_counts_verified": True,
        "core_entity_mutation_not_performed": True,
        "exact_mapping_design_verified": True,
        "exact_observation_manifest_verified": True,
        "exact_raw_archive_verified": True,
        "persisted_encounter_reference_verified": True,
        "persisted_report_reference_verified": True,
        "route_context_verified": True,
    }
    receipt = {
        "schema_version": 1,
        "extraction_kind": "observed_combatants_info_candidate_extraction",
        "extraction_version": "combatants-candidate-extractor-v1",
        "generated_at": "2026-07-29T22:06:54Z",
        "source_design_name": "observed-combatants-info-mapping-design.json",
        "source_capture_name": "observed-report-slice-capture.json",
        "source_payload_hash": _PAYLOAD_HASH,
        "schema_fingerprint": _FINGERPRINT,
        "private_extraction_file": private_path.name,
        "private_extraction_sha256": private_hash,
        "design_results": design_results,
        "integrity_checks": integrity_checks,
        "decision_boundary": {
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
        },
        "summary": {
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
        },
    }
    receipt_path = tmp_path / "observed-combatants-info-candidate-extraction.json"
    _write(receipt_path, receipt)
    return receipt_path, private_path


def _promote(receipt_path: Path, private_path: Path) -> dict[str, Any]:
    return promote_observed_combatants_info_candidates(
        receipt_path,
        private_path,
        reviewed_by="GunsPojoshe (operator), OpenAI-assisted review",
        reviewed_at="2026-07-30T01:30:00+03:00",
    )


def test_promotes_exact_private_candidate_batch_without_source_scalars(tmp_path: Path) -> None:
    receipt_path, private_path = _packet(tmp_path)

    result = _promote(receipt_path, private_path)

    assert result["promotion_kind"] == "observed_combatants_info_manual_candidate_promotion"
    assert result["summary"]["design_count"] == 6
    assert result["summary"]["source_match_count"] == 1350
    assert result["summary"]["output_observation_count"] == 1343
    assert result["summary"]["linked_actor_count"] == 11
    assert result["summary"]["all_integrity_checks_passed"] is True
    assert result["decision_boundary"]["ready_for_immutable_observation_persistence"] is True
    assert result["decision_boundary"]["core_entity_mutation_allowed"] is False
    assert result["decision_boundary"]["planner_scoring_allowed"] is False
    assert len(result["promoted_designs"]) == 6
    assert "PRIVATE" not in json.dumps(result, ensure_ascii=False)


def test_rejects_private_batch_hash_mismatch(tmp_path: Path) -> None:
    receipt_path, private_path = _packet(tmp_path)
    private_path.write_text(private_path.read_text(encoding="utf-8") + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="content hash mismatch"):
        _promote(receipt_path, private_path)


def test_rejects_selected_record_hash_mismatch(tmp_path: Path) -> None:
    receipt_path, private_path = _packet(tmp_path)
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    private_payload = json.loads(private_path.read_text(encoding="utf-8"))
    private_payload["observations"]["coa-combatants-gear-slot-v1"][0][
        "selected_record_sha256"
    ] = "0" * 64
    _write(private_path, private_payload)
    receipt["private_extraction_sha256"] = hashlib.sha256(private_path.read_bytes()).hexdigest()
    _write(receipt_path, receipt)

    with pytest.raises(ValueError, match="selected record hash mismatch"):
        _promote(receipt_path, private_path)


def test_rejects_actor_linkage_mismatch(tmp_path: Path) -> None:
    receipt_path, private_path = _packet(tmp_path)
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    private_payload = json.loads(private_path.read_text(encoding="utf-8"))
    private_payload["observations"]["coa-combatants-hero-build-entry-v1"][0][
        "actor_id"
    ] = "0" * 64
    row = private_payload["observations"]["coa-combatants-hero-build-entry-v1"][0]
    row["observation_id"] = stable_id(
        "combatants_candidate_observation",
        row["design_id"],
        _PAYLOAD_HASH,
        row["raw_match_path"],
        row["selected_record_sha256"],
        row["actor_id"],
    )
    _write(private_path, private_payload)
    receipt["private_extraction_sha256"] = hashlib.sha256(private_path.read_bytes()).hexdigest()
    _write(receipt_path, receipt)

    with pytest.raises(ValueError, match="actor linkage mismatch"):
        _promote(receipt_path, private_path)


def test_rejects_candidate_receipt_boundary_change(tmp_path: Path) -> None:
    receipt_path, private_path = _packet(tmp_path)
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt["decision_boundary"]["automatic_persistence"] = True
    _write(receipt_path, receipt)

    with pytest.raises(ValueError, match="boundary mismatch"):
        _promote(receipt_path, private_path)
