from __future__ import annotations

from pathlib import Path

import pytest

from coa_workbench.normalizer.armory_mapping import ArmoryMappingContract


ROOT = Path(__file__).resolve().parents[2]
CHARACTER_MAPPING = ROOT / "config/mappings/coa_armory_character_v1.json"
TALENT_GRID_MAPPING = ROOT / "config/mappings/coa_armory_talent_grid_v1.json"


def _synthetic_review_packet(*contracts: ArmoryMappingContract) -> dict:
    endpoints = []
    total_paths = 0
    for contract in contracts:
        shapes: dict[str, dict] = {}

        def add_shape(path: str, types: tuple[str, ...], nullable: bool, occurrences: int) -> None:
            existing = shapes.get(path)
            shape = {
                "path": path,
                "occurrence_count": occurrences,
                "type_counts": {value: occurrences for value in types},
                "nullable": nullable,
            }
            if existing is None:
                shapes[path] = shape
            else:
                assert existing == shape

        for field in contract.singletons.values():
            add_shape(field.review_path, field.types, field.nullable, 1)
        for collection in contract.collections.values():
            shapes.setdefault(
                collection.path,
                {
                    "path": collection.path,
                    "occurrence_count": collection.observed_occurrences,
                    "type_counts": {"object": collection.observed_occurrences},
                    "nullable": False,
                },
            )
            for field in collection.fields.values():
                add_shape(
                    field.review_path,
                    field.types,
                    field.nullable,
                    collection.observed_occurrences,
                )
        total_paths += len(shapes)
        endpoints.append(
            {
                "endpoint_kind": contract.endpoint_kind,
                "payload_hash": contract.reviewed_payload_hash,
                "schema_fingerprint": contract.schema_fingerprint,
                "field_shapes": list(shapes.values()),
            }
        )
    return {
        "schema_version": 2,
        "review_kind": "armory_mapping_review",
        "endpoints": endpoints,
        "summary": {
            "endpoint_count": len(endpoints),
            "field_path_count": total_paths,
            "contains_source_scalar_values": False,
            "ready_for_manual_mapping_review": True,
        },
    }


def test_candidate_armory_mappings_load_and_match_review_contracts():
    character = ArmoryMappingContract.from_path(CHARACTER_MAPPING)
    talent_grid = ArmoryMappingContract.from_path(TALENT_GRID_MAPPING)
    packet = _synthetic_review_packet(character, talent_grid)

    character_result = character.validate_against_review_packet(packet)
    talent_grid_result = talent_grid.validate_against_review_packet(packet)

    assert character.mapping_id == "coa-armory-character-v1"
    assert character.reviewed_payload_hash == (
        "2a9d752d7af72d41cd9d41836d670069c78e408df7260f5d9caa83b07430985f"
    )
    assert character_result["field_count"] == 34
    assert character_result["collection_count"] == 5
    assert talent_grid.mapping_id == "coa-armory-talent-grid-v1"
    assert talent_grid.reviewed_payload_hash == (
        "11be25407ec00898547c1b7f342d4596268b3164df9fe0f120bb911559cc5206"
    )
    assert talent_grid_result["field_count"] == 16
    assert talent_grid_result["collection_count"] == 4
    assert character_result["production_ready"] is False
    assert talent_grid_result["production_ready"] is False


@pytest.mark.parametrize("mapping_path", [CHARACTER_MAPPING, TALENT_GRID_MAPPING])
def test_candidate_armory_mapping_is_blocked_from_production(mapping_path):
    contract = ArmoryMappingContract.from_path(mapping_path)

    with pytest.raises(ValueError, match="is not verified"):
        contract.require_verified()


def test_armory_mapping_rejects_review_type_drift():
    contract = ArmoryMappingContract.from_path(TALENT_GRID_MAPPING)
    packet = _synthetic_review_packet(contract)
    endpoint = packet["endpoints"][0]
    shape = next(
        item
        for item in endpoint["field_shapes"]
        if item["path"] == "/trees/*/talents/*/group_id"
    )
    shape["type_counts"] = {"integer": 158}
    shape["nullable"] = False

    with pytest.raises(ValueError, match="type mismatch"):
        contract.validate_against_review_packet(packet)


def test_armory_mapping_rejects_reviewed_payload_hash_mismatch():
    contract = ArmoryMappingContract.from_path(CHARACTER_MAPPING)
    packet = _synthetic_review_packet(contract)
    packet["endpoints"][0]["payload_hash"] = "0" * 64

    with pytest.raises(ValueError, match="reviewed payload hash mismatch"):
        contract.validate_against_review_packet(packet)
