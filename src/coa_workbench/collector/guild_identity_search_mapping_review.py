from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from coa_workbench.collector.guild_identity_search_capture_review import (
    _load_object,
    _required_list,
    _required_object,
    _sha256_bytes,
    _write_json,
)

_MAPPING_VERSION = "guild-identity-search-mapping-review-v1"
_INVENTORY_KIND = "guild_identity_search_schema_inventory"
_INVENTORY_PRIVATE_KIND = "guild_identity_search_schema_inventory_private"
_INVENTORY_VERSION = "guild-identity-search-schema-inventory-v1"
_EXPECTED_OBJECT_FIELDS = {"id", "name", "realm", "report_count"}


def _required_string(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string")
    return value


def _row_by_path(rows: list[dict[str, Any]], path: str) -> dict[str, Any]:
    matches = [row for row in rows if row.get("path") == path]
    if len(matches) != 1:
        raise ValueError(f"expected exactly one inventory row for {path}")
    return matches[0]


def _validate_public_field_inventory(rows: list[dict[str, Any]]) -> None:
    if len(rows) != 5:
        raise ValueError("guild search mapping requires exactly five inventory rows")
    if any(row.get("contains_scalar_value") is not False for row in rows):
        raise ValueError("public field inventory contains scalar values")

    root = _row_by_path(rows, "$.guilds[]")
    if root.get("value_kind") != "object":
        raise ValueError("guild object inventory row type mismatch")
    if set(root.get("object_field_names", [])) != _EXPECTED_OBJECT_FIELDS:
        raise ValueError("guild object field set mismatch")

    guild_id = _row_by_path(rows, "$.guilds[].id")
    if guild_id.get("value_kind") != "integer":
        raise ValueError("guild ID inventory type mismatch")
    if guild_id.get("field_roles") != ["id_candidate"]:
        raise ValueError("guild ID inventory role mismatch")
    if guild_id.get("source_id_match") is not True:
        raise ValueError("guild ID inventory does not match source candidate")

    guild_name = _row_by_path(rows, "$.guilds[].name")
    if guild_name.get("value_kind") != "string":
        raise ValueError("guild name inventory type mismatch")
    if guild_name.get("field_roles") != ["label_candidate"]:
        raise ValueError("guild name inventory role mismatch")
    if guild_name.get("casefold_label_match") is not True:
        raise ValueError("guild name inventory lacks casefold label match")
    if guild_name.get("contains_label_casefold") is not True:
        raise ValueError("guild name inventory lacks contained label match")

    realm = _row_by_path(rows, "$.guilds[].realm")
    if realm.get("value_kind") != "string":
        raise ValueError("guild realm inventory type mismatch")
    if realm.get("field_roles") != ["location_candidate"]:
        raise ValueError("guild realm inventory role mismatch")

    report_count = _row_by_path(rows, "$.guilds[].report_count")
    if report_count.get("value_kind") != "string":
        raise ValueError("guild report count inventory type mismatch")


def _review_guild_object(
    guild_object: Mapping[str, Any],
    *,
    source_guild_id: int | str,
    expected_guild_label: str,
) -> dict[str, Any]:
    if set(guild_object) != _EXPECTED_OBJECT_FIELDS:
        raise ValueError("private guild object field set mismatch")

    guild_id = guild_object.get("id")
    if isinstance(guild_id, bool) or not isinstance(guild_id, int):
        raise ValueError("private guild ID must be an integer")
    if str(guild_id) != str(source_guild_id):
        raise ValueError("private guild ID does not match source candidate")

    guild_name = _required_string(guild_object.get("name"), "private guild name")
    if guild_name.casefold() != expected_guild_label.casefold():
        raise ValueError("private guild name does not casefold-match expected label")

    realm = _required_string(guild_object.get("realm"), "private guild realm")
    report_count = _required_string(
        guild_object.get("report_count"),
        "private guild report count",
    )
    normalized_report_count = report_count.strip()
    report_count_parseable = normalized_report_count.isascii() and normalized_report_count.isdigit()

    return {
        "guild_id": guild_id,
        "guild_name": guild_name,
        "realm": realm,
        "report_count": report_count,
        "report_count_nonnegative_integer_parseable": report_count_parseable,
    }


def review_guild_identity_search_mapping(
    *,
    public_inventory_path: Path,
    private_inventory_path: Path,
    private_output_path: Path,
    receipt_output_path: Path,
    expected_guild_label: str = "Argentum",
) -> dict[str, Any]:
    """Review the bound guild-search schema without publishing source scalar values."""
    public_inventory, public_inventory_body = _load_object(
        public_inventory_path,
        "public guild search schema inventory",
    )
    private_inventory, private_inventory_body = _load_object(
        private_inventory_path,
        "private guild search schema inventory",
    )

    if public_inventory.get("schema_version") != 1:
        raise ValueError("public schema inventory version mismatch")
    if public_inventory.get("inventory_kind") != _INVENTORY_KIND:
        raise ValueError("public schema inventory kind mismatch")
    if public_inventory.get("inventory_version") != _INVENTORY_VERSION:
        raise ValueError("public schema inventory implementation mismatch")

    target = _required_object(public_inventory.get("target"), "inventory.target")
    if target.get("guild_label") != expected_guild_label:
        raise ValueError("public schema inventory guild label mismatch")
    if target.get("raw_payload_published") is not False:
        raise ValueError("public schema inventory publishes raw payload")
    if target.get("source_guild_id_published") is not False:
        raise ValueError("public schema inventory publishes source guild ID")

    summary = _required_object(public_inventory.get("summary"), "inventory.summary")
    if summary.get("all_integrity_checks_passed") is not True:
        raise ValueError("public schema inventory integrity checks failed")
    if summary.get("guild_object_count") != 1:
        raise ValueError("mapping review requires exactly one guild object")
    if summary.get("casefold_label_match_count") != 1:
        raise ValueError("mapping review requires one casefold label match")
    if summary.get("source_id_match_count") != 1:
        raise ValueError("mapping review requires one source ID match")
    if summary.get("contains_raw_payload") is not False:
        raise ValueError("public schema inventory contains raw payload")
    if summary.get("contains_source_scalar_values") is not False:
        raise ValueError("public schema inventory contains source scalar values")

    expected_private_hash = public_inventory.get("source_private_inventory_sha256")
    if not isinstance(expected_private_hash, str) or len(expected_private_hash) != 64:
        raise ValueError("public schema inventory private SHA-256 is missing")
    if _sha256_bytes(private_inventory_body) != expected_private_hash:
        raise ValueError("private schema inventory SHA-256 mismatch")

    if private_inventory.get("schema_version") != 1:
        raise ValueError("private schema inventory version mismatch")
    if private_inventory.get("inventory_kind") != _INVENTORY_PRIVATE_KIND:
        raise ValueError("private schema inventory kind mismatch")
    if private_inventory.get("inventory_version") != _INVENTORY_VERSION:
        raise ValueError("private schema inventory implementation mismatch")
    if private_inventory.get("target_guild_label") != expected_guild_label:
        raise ValueError("private schema inventory guild label mismatch")

    public_capture = _required_object(
        public_inventory.get("capture_binding"),
        "inventory.capture_binding",
    )
    private_capture = _required_object(
        private_inventory.get("capture_binding"),
        "private_inventory.capture_binding",
    )
    if public_capture != private_capture:
        raise ValueError("public and private schema inventory capture bindings differ")

    schema_inventory = _required_object(
        public_inventory.get("schema_inventory"),
        "inventory.schema_inventory",
    )
    public_rows = [
        _required_object(row, "inventory field row")
        for row in _required_list(schema_inventory.get("field_entries"), "field_entries")
    ]
    private_rows = [
        _required_object(row, "private inventory field row")
        for row in _required_list(private_inventory.get("field_inventory"), "field_inventory")
    ]
    if public_rows != private_rows:
        raise ValueError("public and private field inventories differ")
    _validate_public_field_inventory(public_rows)

    source_guild_id = private_inventory.get("candidate_source_guild_id")
    if isinstance(source_guild_id, bool) or not isinstance(source_guild_id, (int, str)):
        raise ValueError("private source guild ID is missing")
    guild_object = _required_object(private_inventory.get("guild_object"), "guild_object")
    reviewed = _review_guild_object(
        guild_object,
        source_guild_id=source_guild_id,
        expected_guild_label=expected_guild_label,
    )

    mapped_fields = [
        {
            "semantic_name": "guild_id",
            "path": "$.guilds[].id",
            "source_type": "integer",
            "normalization": "identity",
            "source_candidate_match": True,
            "contains_scalar_value": False,
        },
        {
            "semantic_name": "guild_name",
            "path": "$.guilds[].name",
            "source_type": "string",
            "normalization": "unicode_casefold_for_comparison",
            "expected_label_match": True,
            "contains_scalar_value": False,
        },
        {
            "semantic_name": "realm",
            "path": "$.guilds[].realm",
            "source_type": "string",
            "normalization": "identity_candidate",
            "contains_scalar_value": False,
        },
        {
            "semantic_name": "report_count",
            "path": "$.guilds[].report_count",
            "source_type": "string",
            "normalization": "base10_nonnegative_integer_candidate",
            "parseable_in_observed_payload": reviewed[
                "report_count_nonnegative_integer_parseable"
            ],
            "contains_scalar_value": False,
        },
    ]

    checks = {
        "public_schema_inventory_verified": True,
        "private_schema_inventory_sha256_verified": True,
        "capture_binding_verified": True,
        "public_private_field_inventory_match_verified": True,
        "exact_object_field_set_verified": True,
        "guild_id_integer_verified": True,
        "guild_id_matches_source_candidate": True,
        "guild_name_casefold_match_verified": True,
        "realm_string_verified": True,
        "report_count_string_verified": True,
        "public_mapping_contains_no_scalar_values": all(
            row["contains_scalar_value"] is False for row in mapped_fields
        ),
        "raw_payload_not_published": True,
        "source_guild_id_not_published": True,
    }

    private_payload = {
        "schema_version": 1,
        "mapping_kind": "guild_identity_search_mapping_review_private",
        "mapping_version": _MAPPING_VERSION,
        "source_public_inventory_name": public_inventory_path.name,
        "source_public_inventory_sha256": _sha256_bytes(public_inventory_body),
        "source_private_inventory_name": private_inventory_path.name,
        "source_private_inventory_sha256": _sha256_bytes(private_inventory_body),
        "target_guild_label": expected_guild_label,
        "candidate_source_guild_id": source_guild_id,
        "capture_binding": public_capture,
        "reviewed_guild_object": reviewed,
        "mapped_fields": mapped_fields,
    }
    private_body = _write_json(private_output_path, private_payload)

    receipt = {
        "schema_version": 1,
        "mapping_kind": "guild_identity_search_mapping_review",
        "mapping_version": _MAPPING_VERSION,
        "source_public_inventory_name": public_inventory_path.name,
        "source_public_inventory_sha256": _sha256_bytes(public_inventory_body),
        "source_private_review_name": private_output_path.name,
        "source_private_review_sha256": _sha256_bytes(private_body),
        "target": {
            "guild_label": expected_guild_label,
            "raw_payload_published": False,
            "source_guild_id_published": False,
        },
        "capture_binding": public_capture,
        "field_mapping": {
            "mapped_fields": mapped_fields,
            "mapped_field_count": len(mapped_fields),
            "contains_scalar_values": False,
        },
        "evidence_summary": {
            "guild_search_result_count": 1,
            "guild_id_source_candidate_match_count": 1,
            "guild_name_casefold_match_count": 1,
            "guild_name_exact_match_count": 0,
            "realm_field_present": True,
            "report_count_field_present": True,
            "cross_endpoint_identity_candidate_observed": True,
            "contains_raw_payload": False,
            "contains_source_scalar_values": False,
        },
        "integrity_checks": checks,
        "summary": {
            "all_integrity_checks_passed": all(checks.values()),
            "mapped_field_count": len(mapped_fields),
            "cross_endpoint_identity_candidate_observed": True,
            "ready_for_guild_identity_decision_review": True,
            "contains_raw_payload": False,
            "contains_source_scalar_values": False,
        },
        "decision_boundary": {
            "status": "independent_source_identity_candidate_observed",
            "guild_api_route_candidates_observed": True,
            "guild_search_route_response_captured": True,
            "guild_search_route_semantics_candidate_observed": True,
            "guild_search_schema_inventory_complete": True,
            "guild_search_field_mapping_reviewed": True,
            "independent_source_identity_candidate_observed": True,
            "ready_for_guild_identity_decision_review": True,
            "guild_api_route_semantics_verified": False,
            "independent_source_identity_verified": False,
            "guild_identity_verified": False,
            "ready_for_guild_filtering": False,
            "ready_for_full_guild_crawl": False,
            "ready_for_multi_report_character_graph": False,
            "ready_for_performance_model": False,
            "ready_for_bis25_scoring": False,
            "planner_scoring_allowed": False,
        },
    }
    _write_json(receipt_output_path, receipt)
    return receipt
