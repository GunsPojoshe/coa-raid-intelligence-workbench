from __future__ import annotations

import hashlib
import json

import pytest

from coa_workbench.collector.guild_identity_search_mapping_review import (
    _review_guild_object,
    _validate_public_field_inventory,
    review_guild_identity_search_mapping,
)


def _field_rows() -> list[dict[str, object]]:
    return [
        {
            "path": "$.guilds[]",
            "field_name": "guilds[]",
            "value_kind": "object",
            "field_roles": [],
            "object_field_names": ["id", "name", "realm", "report_count"],
            "contains_scalar_value": False,
        },
        {
            "path": "$.guilds[].id",
            "field_name": "id",
            "value_kind": "integer",
            "field_roles": ["id_candidate"],
            "source_id_match": True,
            "contains_scalar_value": False,
        },
        {
            "path": "$.guilds[].name",
            "field_name": "name",
            "value_kind": "string",
            "field_roles": ["label_candidate"],
            "casefold_label_match": True,
            "contains_label_casefold": True,
            "contains_scalar_value": False,
        },
        {
            "path": "$.guilds[].realm",
            "field_name": "realm",
            "value_kind": "string",
            "field_roles": ["location_candidate"],
            "contains_scalar_value": False,
        },
        {
            "path": "$.guilds[].report_count",
            "field_name": "report_count",
            "value_kind": "string",
            "field_roles": [],
            "contains_scalar_value": False,
        },
    ]


def _write_json(path, payload: dict[str, object]) -> bytes:
    body = (json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()
    path.write_bytes(body)
    return body


def test_public_field_inventory_accepts_observed_mapping() -> None:
    _validate_public_field_inventory(_field_rows())


def test_public_field_inventory_rejects_schema_drift() -> None:
    rows = _field_rows()
    rows[0]["object_field_names"] = ["id", "name", "realm"]

    with pytest.raises(ValueError, match="field set mismatch"):
        _validate_public_field_inventory(rows)


def test_review_guild_object_accepts_casefold_name_and_source_id() -> None:
    reviewed = _review_guild_object(
        {
            "id": 987654321,
            "name": "ARGENTUM",
            "realm": "Area 52",
            "report_count": "2468",
        },
        source_guild_id=987654321,
        expected_guild_label="Argentum",
    )

    assert reviewed["guild_id"] == 987654321
    assert reviewed["guild_name"] == "ARGENTUM"
    assert reviewed["report_count_nonnegative_integer_parseable"] is True


def test_review_guild_object_rejects_source_id_mismatch() -> None:
    with pytest.raises(ValueError, match="does not match source candidate"):
        _review_guild_object(
            {
                "id": 123,
                "name": "Argentum",
                "realm": "Area 52",
                "report_count": "17",
            },
            source_guild_id=456,
            expected_guild_label="Argentum",
        )


def test_mapping_review_is_scalar_free_and_ready_for_decision(tmp_path) -> None:
    rows = _field_rows()
    capture = {
        "bytes_uncompressed": 93,
        "observation_id": "a" * 64,
        "payload_hash": "b" * 64,
        "raw_id": "c" * 64,
        "schema_fingerprint": "d" * 64,
    }
    private_inventory = {
        "schema_version": 1,
        "inventory_kind": "guild_identity_search_schema_inventory_private",
        "inventory_version": "guild-identity-search-schema-inventory-v1",
        "target_guild_label": "Argentum",
        "candidate_source_guild_id": 987654321,
        "capture_binding": capture,
        "guild_object": {
            "id": 987654321,
            "name": "ARGENTUM",
            "realm": "Area 52",
            "report_count": "2468",
        },
        "field_inventory": rows,
    }
    private_inventory_path = tmp_path / "inventory.private.json"
    private_body = _write_json(private_inventory_path, private_inventory)

    public_inventory = {
        "schema_version": 1,
        "inventory_kind": "guild_identity_search_schema_inventory",
        "inventory_version": "guild-identity-search-schema-inventory-v1",
        "source_private_inventory_sha256": hashlib.sha256(private_body).hexdigest(),
        "target": {
            "guild_label": "Argentum",
            "raw_payload_published": False,
            "source_guild_id_published": False,
        },
        "capture_binding": capture,
        "schema_inventory": {"field_entries": rows},
        "summary": {
            "all_integrity_checks_passed": True,
            "guild_object_count": 1,
            "casefold_label_match_count": 1,
            "source_id_match_count": 1,
            "contains_raw_payload": False,
            "contains_source_scalar_values": False,
        },
    }
    public_inventory_path = tmp_path / "inventory.json"
    _write_json(public_inventory_path, public_inventory)

    private_output_path = tmp_path / "mapping.private.json"
    receipt_output_path = tmp_path / "mapping.json"
    receipt = review_guild_identity_search_mapping(
        public_inventory_path=public_inventory_path,
        private_inventory_path=private_inventory_path,
        private_output_path=private_output_path,
        receipt_output_path=receipt_output_path,
    )

    assert receipt["summary"]["all_integrity_checks_passed"] is True
    assert receipt["decision_boundary"]["independent_source_identity_candidate_observed"] is True
    assert receipt["decision_boundary"]["ready_for_guild_identity_decision_review"] is True
    assert receipt["decision_boundary"]["guild_identity_verified"] is False

    public_text = receipt_output_path.read_text(encoding="utf-8")
    assert "987654321" not in public_text
    assert "ARGENTUM" not in public_text
    assert "Area 52" not in public_text
    assert "reviewed_guild_object" not in public_text

    private_text = private_output_path.read_text(encoding="utf-8")
    assert "987654321" in private_text
    assert "ARGENTUM" in private_text
    assert "Area 52" in private_text
