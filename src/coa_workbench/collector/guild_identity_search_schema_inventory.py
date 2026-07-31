from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from coa_workbench.collector.guild_identity_search_capture_review import (
    _load_object,
    _read_bound_payload,
    _required_list,
    _required_object,
    _sha256_bytes,
    _validate_sources,
    _write_json,
)

_INVENTORY_VERSION = "guild-identity-search-schema-inventory-v1"
_PUBLIC_REVIEW_KIND = "guild_identity_search_capture_review"
_PUBLIC_REVIEW_VERSION = "guild-identity-search-capture-review-v1"
_SELECTED_PROFILE = "spa_fetch_context"
_MAX_INVENTORY_NODES = 250
_MAX_INVENTORY_DEPTH = 12


def _value_kind(value: object) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, dict):
        return "object"
    if isinstance(value, list):
        return "array"
    raise ValueError(f"unsupported JSON value type: {type(value).__name__}")


def _normalized_name(value: str) -> str:
    return "".join(char for char in value.casefold() if char.isalnum())


def _field_roles(field_name: str) -> list[str]:
    normalized = _normalized_name(field_name)
    roles: list[str] = []
    if normalized in {
        "displayname",
        "guild",
        "guildlabel",
        "guildname",
        "label",
        "name",
        "title",
    } or normalized.endswith(("guildname", "displayname")):
        roles.append("label_candidate")
    if normalized in {
        "guildid",
        "guildidentifier",
        "id",
        "identifier",
        "key",
        "uuid",
    } or normalized.endswith(("guildid", "identifier", "uuid")):
        roles.append("id_candidate")
    if normalized in {"realm", "region", "server", "shard"}:
        roles.append("location_candidate")
    if normalized in {"faction", "side"}:
        roles.append("faction_candidate")
    return roles


def _inventory_fields(
    guild_object: Mapping[str, Any],
    *,
    expected_guild_label: str,
    source_guild_id: int | str,
) -> list[dict[str, Any]]:
    expected_casefold = expected_guild_label.casefold()
    source_text = str(source_guild_id)
    aggregated: dict[str, dict[str, Any]] = {}
    visited_nodes = 0

    def visit(value: object, path: str, field_name: str, depth: int) -> None:
        nonlocal visited_nodes
        visited_nodes += 1
        if visited_nodes > _MAX_INVENTORY_NODES:
            raise ValueError("guild search schema inventory node limit exceeded")
        if depth > _MAX_INVENTORY_DEPTH:
            raise ValueError("guild search schema inventory depth limit exceeded")

        kind = _value_kind(value)
        roles = _field_roles(field_name)
        exact_label = isinstance(value, str) and value == expected_guild_label
        casefold_label = isinstance(value, str) and value.casefold() == expected_casefold
        contains_label = (
            isinstance(value, str)
            and bool(expected_casefold)
            and expected_casefold in value.casefold()
        )
        source_id_match = (
            not isinstance(value, bool)
            and isinstance(value, (int, str))
            and str(value) == source_text
        )
        row: dict[str, Any] = {
            "path": path,
            "field_name": field_name,
            "value_kind": kind,
            "depth": depth,
            "field_roles": roles,
            "exact_label_match": exact_label,
            "casefold_label_match": casefold_label,
            "contains_label_casefold": contains_label,
            "source_id_match": source_id_match,
            "contains_scalar_value": False,
        }
        if isinstance(value, dict):
            row["object_field_names"] = sorted(str(key) for key in value)
        elif isinstance(value, list):
            row["array_length"] = len(value)
            row["array_element_kinds"] = sorted({_value_kind(child) for child in value})

        signature = json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        if signature not in aggregated:
            aggregated[signature] = {**row, "occurrence_count": 0}
        aggregated[signature]["occurrence_count"] += 1

        if isinstance(value, dict):
            for key in sorted(value):
                visit(value[key], f"{path}.{key}", str(key), depth + 1)
        elif isinstance(value, list):
            for child in value:
                visit(child, f"{path}[]", f"{field_name}[]", depth + 1)

    visit(dict(guild_object), "$.guilds[]", "guilds[]", 0)
    return sorted(
        aggregated.values(),
        key=lambda row: (
            str(row["path"]),
            str(row["value_kind"]),
            str(row["field_name"]),
        ),
    )


def _validate_public_review(
    review: Mapping[str, Any],
    *,
    private_review_body: bytes,
    public_diagnostic_body: bytes,
    expected_guild_label: str,
) -> dict[str, Any]:
    if review.get("schema_version") != 1:
        raise ValueError("public capture review schema mismatch")
    if review.get("review_kind") != _PUBLIC_REVIEW_KIND:
        raise ValueError("public capture review kind mismatch")
    if review.get("review_version") != _PUBLIC_REVIEW_VERSION:
        raise ValueError("public capture review version mismatch")

    target = _required_object(review.get("target"), "review.target")
    if target.get("guild_label") != expected_guild_label:
        raise ValueError("public capture review guild label mismatch")
    if target.get("raw_payload_published") is not False:
        raise ValueError("public capture review publishes raw payload")
    if target.get("source_guild_id_published") is not False:
        raise ValueError("public capture review publishes source guild ID")

    summary = _required_object(review.get("summary"), "review.summary")
    if summary.get("all_integrity_checks_passed") is not True:
        raise ValueError("public capture review integrity checks failed")
    if summary.get("contains_raw_payload") is not False:
        raise ValueError("public capture review contains raw payload")
    if summary.get("contains_source_scalar_values") is not False:
        raise ValueError("public capture review contains source scalar values")
    if summary.get("route_shape_candidate") is not True:
        raise ValueError("public capture review is not a route-shape candidate")
    if summary.get("exact_label_object_count") != 0:
        raise ValueError("schema inventory expects zero exact label objects")
    if summary.get("source_id_match_object_count") != 0:
        raise ValueError("schema inventory expects zero source ID matches")
    if summary.get("one_to_one_identity_candidate") is not False:
        raise ValueError("schema inventory input already claims one-to-one identity")

    expected_private_hash = review.get("source_private_review_sha256")
    if not isinstance(expected_private_hash, str) or len(expected_private_hash) != 64:
        raise ValueError("public capture review private SHA-256 is missing")
    if _sha256_bytes(private_review_body) != expected_private_hash:
        raise ValueError("private capture review SHA-256 mismatch")

    expected_diagnostic_hash = review.get("source_public_diagnostic_sha256")
    if not isinstance(expected_diagnostic_hash, str) or len(expected_diagnostic_hash) != 64:
        raise ValueError("public capture review diagnostic SHA-256 is missing")
    if _sha256_bytes(public_diagnostic_body) != expected_diagnostic_hash:
        raise ValueError("public access diagnostic SHA-256 mismatch")

    capture = _required_object(review.get("capture_binding"), "review.capture_binding")
    if capture.get("selected_access_profile") != _SELECTED_PROFILE:
        raise ValueError("public capture review selected profile mismatch")
    return capture


def inventory_guild_identity_search_schema(
    *,
    public_capture_review_path: Path,
    private_capture_review_path: Path,
    public_access_diagnostic_path: Path,
    private_access_diagnostic_path: Path,
    private_search_probe_path: Path,
    raw_root: Path,
    private_output_path: Path,
    receipt_output_path: Path,
    expected_guild_label: str = "Argentum",
) -> dict[str, Any]:
    """Inventory the already bound guild-search object without publishing scalar values."""
    public_review, public_review_body = _load_object(
        public_capture_review_path,
        "public guild search capture review",
    )
    private_review, private_review_body = _load_object(
        private_capture_review_path,
        "private guild search capture review",
    )
    public_diagnostic, public_diagnostic_body = _load_object(
        public_access_diagnostic_path,
        "public guild search access diagnostic",
    )
    private_diagnostic, private_diagnostic_body = _load_object(
        private_access_diagnostic_path,
        "private guild search access diagnostic",
    )
    private_probe, private_probe_body = _load_object(
        private_search_probe_path,
        "private guild search probe",
    )

    review_capture = _validate_public_review(
        public_review,
        private_review_body=private_review_body,
        public_diagnostic_body=public_diagnostic_body,
        expected_guild_label=expected_guild_label,
    )
    source_capture, private_attempt, source_guild_id = _validate_sources(
        public_diagnostic,
        private_diagnostic,
        private_probe,
        private_diagnostic_body=private_diagnostic_body,
        private_probe_body=private_probe_body,
        expected_guild_label=expected_guild_label,
    )
    if review_capture != source_capture:
        raise ValueError("capture review and source diagnostic bindings differ")

    manifest, payload, raw_body = _read_bound_payload(raw_root, source_capture)
    if payload != private_attempt.get("body"):
        raise ValueError("raw payload does not match private access diagnostic")
    if payload.get("success") is not True:
        raise ValueError("guild search payload success flag is not true")
    guilds = _required_list(payload.get("guilds"), "payload.guilds")
    guild_objects = [value for value in guilds if isinstance(value, dict)]
    if len(guilds) != 1 or len(guild_objects) != 1:
        raise ValueError("schema inventory requires exactly one guild object")

    guild_object = guild_objects[0]
    fields = _inventory_fields(
        guild_object,
        expected_guild_label=expected_guild_label,
        source_guild_id=source_guild_id,
    )
    exact_label_matches = sum(
        int(row["occurrence_count"])
        for row in fields
        if row["exact_label_match"]
    )
    casefold_label_matches = sum(
        int(row["occurrence_count"])
        for row in fields
        if row["casefold_label_match"]
    )
    contains_label_matches = sum(
        int(row["occurrence_count"])
        for row in fields
        if row["contains_label_casefold"]
    )
    source_id_matches = sum(
        int(row["occurrence_count"])
        for row in fields
        if row["source_id_match"]
    )
    label_role_fields = sum(
        int(row["occurrence_count"])
        for row in fields
        if "label_candidate" in row["field_roles"]
    )
    id_role_fields = sum(
        int(row["occurrence_count"])
        for row in fields
        if "id_candidate" in row["field_roles"]
    )

    checks = {
        "public_capture_review_verified": True,
        "private_capture_review_sha256_verified": True,
        "public_access_diagnostic_sha256_verified": True,
        "private_access_diagnostic_sha256_verified": True,
        "private_search_probe_sha256_verified": True,
        "capture_binding_verified": True,
        "selected_access_profile_verified": True,
        "raw_content_manifest_binding_verified": True,
        "raw_payload_sha256_verified": _sha256_bytes(raw_body) == source_capture["payload_hash"],
        "raw_payload_matches_private_diagnostic": True,
        "single_guild_object_verified": True,
        "inventory_node_count_bounded": sum(int(row["occurrence_count"]) for row in fields)
        <= _MAX_INVENTORY_NODES,
        "public_inventory_contains_no_scalar_values": all(
            row["contains_scalar_value"] is False for row in fields
        ),
        "raw_payload_not_published": True,
        "source_guild_id_not_published": True,
    }

    private_payload = {
        "schema_version": 1,
        "inventory_kind": "guild_identity_search_schema_inventory_private",
        "inventory_version": _INVENTORY_VERSION,
        "source_public_capture_review_name": public_capture_review_path.name,
        "source_public_capture_review_sha256": _sha256_bytes(public_review_body),
        "source_private_capture_review_name": private_capture_review_path.name,
        "source_private_capture_review_sha256": _sha256_bytes(private_review_body),
        "target_guild_label": expected_guild_label,
        "candidate_source_guild_id": source_guild_id,
        "capture_binding": source_capture,
        "raw_content_manifest": manifest,
        "guild_object": guild_object,
        "field_inventory": fields,
    }
    private_body = _write_json(private_output_path, private_payload)

    receipt = {
        "schema_version": 1,
        "inventory_kind": "guild_identity_search_schema_inventory",
        "inventory_version": _INVENTORY_VERSION,
        "source_public_capture_review_name": public_capture_review_path.name,
        "source_public_capture_review_sha256": _sha256_bytes(public_review_body),
        "source_private_inventory_name": private_output_path.name,
        "source_private_inventory_sha256": _sha256_bytes(private_body),
        "target": {
            "guild_label": expected_guild_label,
            "raw_payload_published": False,
            "source_guild_id_published": False,
        },
        "capture_binding": source_capture,
        "schema_inventory": {
            "guild_object_count": 1,
            "field_entries": fields,
            "distinct_field_entry_count": len(fields),
            "total_node_count": sum(int(row["occurrence_count"]) for row in fields),
            "exact_label_match_count": exact_label_matches,
            "casefold_label_match_count": casefold_label_matches,
            "contains_label_casefold_count": contains_label_matches,
            "source_id_match_count": source_id_matches,
            "label_role_field_count": label_role_fields,
            "id_role_field_count": id_role_fields,
            "contains_scalar_values": False,
        },
        "integrity_checks": checks,
        "summary": {
            "all_integrity_checks_passed": all(checks.values()),
            "guild_object_count": 1,
            "distinct_field_entry_count": len(fields),
            "exact_label_match_count": exact_label_matches,
            "casefold_label_match_count": casefold_label_matches,
            "contains_label_casefold_count": contains_label_matches,
            "source_id_match_count": source_id_matches,
            "contains_raw_payload": False,
            "contains_source_scalar_values": False,
        },
        "decision_boundary": {
            "status": "guild_search_schema_inventory_complete",
            "guild_api_route_candidates_observed": True,
            "guild_search_route_response_captured": True,
            "guild_search_route_semantics_candidate_observed": True,
            "guild_search_schema_inventory_complete": True,
            "ready_for_guild_search_mapping_review": True,
            "guild_api_route_semantics_verified": False,
            "independent_source_identity_candidate_observed": False,
            "independent_source_identity_verified": False,
            "guild_identity_verified": False,
            "ready_for_guild_identity_decision_review": False,
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
