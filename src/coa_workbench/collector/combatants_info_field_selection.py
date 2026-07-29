from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

_SELECTION_SCHEMA_VERSION = 1
_DEEP_REVIEW_KIND = "observed_combatants_info_deep_scope_review"
_SCOPE_REVIEW_KIND = "observed_report_slice_scope_review"
_ENDPOINT_KIND = "combatants_info"
_ROUTE_TEMPLATE = "/api/reports/{template}/encounters/{template}/combatants-info"
_PAYLOAD_HASH = "45672e0f0ff9eb461c575bdd38385795daa6326378bc3f8ad51474276140dc14"
_SCHEMA_FINGERPRINT = "41d6d15422c668f83d2ccae1ec0ff2969671861f9e43b21cb371578961c5f8ff"
_OUTER_ACTOR_SCOPE = "/combatants/*"
_OUTER_ACTOR_PATH = "/combatants/*/character_id"

_EXPECTED_PRESENT_SCOPES = {
    "/combatants/*/ci_resolved/player",
    "/combatants/*/ci_resolved/guild",
    "/combatants/*/ci_resolved/instance",
    "/combatants/*/ci_resolved/specialization",
    "/combatants/*/ci_resolved/specialization/talents",
    "/combatants/*/ci_resolved/specialization/resolved_ca_talent_ranks/*",
    "/combatants/*/ci_resolved/specialization/hero_build/*",
    "/combatants/*/ci_resolved/specialization/unlocked_specs/*",
    "/combatants/*/ci_resolved/specialization/vanilla_talents",
    "/combatants/*/ci_resolved/gear/*",
}
_EXPECTED_MISSING_SCOPES = {
    "/combatants/*/ci_resolved/specialization/talents/trees/*",
    "/combatants/*/ci_resolved/mystic_enchants/*",
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
        raise ValueError(f"{field_name} must be an object")
    return value


def _required_list(value: object, field_name: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be an array")
    return value


def _required_string(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field_name} must be a non-empty string")
    return value


def _scope_index(review: Mapping[str, Any], label: str) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for raw_scope in _required_list(review.get("scopes"), f"{label}.scopes"):
        scope = _required_object(raw_scope, f"{label}.scopes[]")
        scope_path = _required_string(scope.get("scope"), "scope")
        if scope_path in result:
            raise ValueError(f"duplicate {label} scope: {scope_path}")
        result[scope_path] = scope
    return result


def _field_index(scope: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for raw_field in _required_list(scope.get("direct_fields"), "scope.direct_fields"):
        field = _required_object(raw_field, "scope.direct_fields[]")
        path = _required_string(field.get("path"), "direct field path")
        if path in result:
            raise ValueError(f"duplicate direct field path: {path}")
        result[path] = field
    return result


def _validate_deep_review(review: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    if review.get("schema_version") != 1 or review.get("review_kind") != _DEEP_REVIEW_KIND:
        raise ValueError("unsupported combatants-info deep scope review")

    endpoint = _required_object(review.get("endpoint"), "deep review.endpoint")
    expected_endpoint = {
        "endpoint_kind": _ENDPOINT_KIND,
        "route_template": _ROUTE_TEMPLATE,
        "payload_hash": _PAYLOAD_HASH,
        "schema_fingerprint": _SCHEMA_FINGERPRINT,
        "review_status": "candidate",
        "transport_provenance_type": "upstream_derived",
        "content_provenance_status": "candidate_companion_addon_enrichment",
    }
    for field_name, expected in expected_endpoint.items():
        if endpoint.get(field_name) != expected:
            raise ValueError(f"combatants-info deep review endpoint mismatch: {field_name}")

    summary = _required_object(review.get("summary"), "deep review.summary")
    expected_summary = {
        "endpoint_count": 1,
        "scope_candidate_count": 12,
        "present_scope_count": 10,
        "required_scope_count": 4,
        "required_scope_present_count": 4,
        "optional_scope_candidate_count": 8,
        "optional_scope_present_count": 6,
        "optional_scope_missing_count": 2,
        "direct_field_count": 56,
        "persisted_report_count": 1,
        "persisted_encounter_count": 14,
        "persisted_actor_count": 31,
        "persisted_participant_count": 31,
        "all_archives_consistent": True,
        "selected_parser_persistence_verified": True,
        "contains_source_scalar_values": False,
        "semantic_verification_required": True,
        "ready_for_manual_combatants_field_selection": True,
        "companion_addon_provenance_verified": False,
        "combatants_info_enrichment_available": False,
        "normalization_allowed": False,
        "mechanic_semantics_verified": False,
        "planner_scoring_allowed": False,
    }
    for field_name, expected in expected_summary.items():
        if summary.get(field_name) != expected:
            raise ValueError(f"combatants-info deep review summary mismatch: {field_name}")

    boundary = _required_object(review.get("decision_boundary"), "deep review.decision_boundary")
    expected_boundary = {
        "status": "candidate",
        "automatic_scope_selection": False,
        "automatic_field_selection": False,
        "automatic_mapping_creation": False,
        "can_promote": False,
        "semantic_verification_required": True,
        "companion_addon_provenance_verified": False,
        "combatants_info_enrichment_available": False,
        "normalization_allowed": False,
        "mechanic_semantics_verified": False,
        "planner_scoring_allowed": False,
    }
    for field_name, expected in expected_boundary.items():
        if boundary.get(field_name) != expected:
            raise ValueError(f"combatants-info deep review boundary mismatch: {field_name}")

    scopes = _scope_index(review, "deep review")
    if set(scopes) != _EXPECTED_PRESENT_SCOPES:
        raise ValueError("combatants-info deep review present scope set mismatch")
    for scope_path, scope in scopes.items():
        if scope.get("endpoint_kind") != _ENDPOINT_KIND:
            raise ValueError(f"combatants-info scope endpoint mismatch: {scope_path}")
        if scope.get("route_template") != _ROUTE_TEMPLATE:
            raise ValueError(f"combatants-info scope route mismatch: {scope_path}")
        if scope.get("payload_hash") != _PAYLOAD_HASH:
            raise ValueError(f"combatants-info scope payload mismatch: {scope_path}")
        if scope.get("schema_fingerprint") != _SCHEMA_FINGERPRINT:
            raise ValueError(f"combatants-info scope fingerprint mismatch: {scope_path}")
        if scope.get("review_status") != "candidate":
            raise ValueError(f"combatants-info scope is not candidate: {scope_path}")
        if scope.get("semantic_status") != "unverified_candidate":
            raise ValueError(f"combatants-info scope semantic status mismatch: {scope_path}")
        if scope.get("manual_decision_required") is not True:
            raise ValueError(f"combatants-info scope manual boundary missing: {scope_path}")

    missing_scopes = {
        _required_string(row.get("scope"), "missing optional scope")
        for row in (
            _required_object(raw, "deep review.missing_optional_scopes[]")
            for raw in _required_list(
                review.get("missing_optional_scopes"),
                "deep review.missing_optional_scopes",
            )
        )
    }
    if missing_scopes != _EXPECTED_MISSING_SCOPES:
        raise ValueError("combatants-info missing optional scope set mismatch")
    return scopes


def _validate_outer_actor_linkage(review: Mapping[str, Any]) -> dict[str, Any]:
    if review.get("schema_version") != 1 or review.get("review_kind") != _SCOPE_REVIEW_KIND:
        raise ValueError("unsupported observed report slice scope review")
    summary = _required_object(review.get("summary"), "scope review.summary")
    expected_summary = {
        "endpoint_count": 3,
        "scope_candidate_count": 7,
        "direct_field_count": 120,
        "all_archives_consistent": True,
        "contains_source_scalar_values": False,
        "semantic_verification_required": True,
        "normalization_allowed": False,
        "ready_for_manual_field_selection": True,
    }
    for field_name, expected in expected_summary.items():
        if summary.get(field_name) != expected:
            raise ValueError(f"scope review summary mismatch: {field_name}")

    matches = []
    for raw_scope in _required_list(review.get("scopes"), "scope review.scopes"):
        scope = _required_object(raw_scope, "scope review.scopes[]")
        if scope.get("endpoint_kind") == _ENDPOINT_KIND and scope.get("scope") == _OUTER_ACTOR_SCOPE:
            matches.append(scope)
    if len(matches) != 1:
        raise ValueError("scope review must contain one combatants outer scope")
    scope = matches[0]
    for field_name, expected in {
        "route_template": _ROUTE_TEMPLATE,
        "payload_hash": _PAYLOAD_HASH,
        "schema_fingerprint": _SCHEMA_FINGERPRINT,
        "review_status": "candidate",
        "semantic_status": "unverified_candidate",
        "manual_decision_required": True,
    }.items():
        if scope.get(field_name) != expected:
            raise ValueError(f"combatants outer scope mismatch: {field_name}")

    field = _field_index(scope).get(_OUTER_ACTOR_PATH)
    if field is None:
        raise ValueError("combatants outer actor linkage field is missing")
    if set(field.get("types", [])) != {"integer"}:
        raise ValueError("combatants outer actor linkage type mismatch")
    if field.get("nullable") is not False:
        raise ValueError("combatants outer actor linkage cannot be nullable")
    if field.get("observed_on_all_scope_occurrences") is not True:
        raise ValueError("combatants outer actor linkage must be observed everywhere")
    return field


def _selected_field(
    source_name: str,
    output_field: str,
    types: tuple[str, ...],
    *,
    required: bool = True,
) -> dict[str, Any]:
    return {
        "source_name": source_name,
        "output_field": output_field,
        "types": list(types),
        "required": required,
    }


_SELECTION_GROUP_BLUEPRINTS: tuple[dict[str, Any], ...] = (
    {
        "group_id": "actor_identity",
        "scope": "/combatants/*/ci_resolved/player",
        "source_actor_expression": "@ancestor[1]/character_id",
        "mapping_strategy": "actor_enrichment_candidate",
        "fields": (
            _selected_field("class", "class", ("string",)),
            _selected_field("gender", "gender", ("integer",)),
            _selected_field("guid", "guid", ("string",)),
            _selected_field("level", "level", ("integer",)),
            _selected_field("name", "name", ("string",)),
            _selected_field("race", "race", ("string",)),
            _selected_field("realm", "realm", ("string",)),
        ),
    },
    {
        "group_id": "guild_membership",
        "scope": "/combatants/*/ci_resolved/guild",
        "source_actor_expression": "@ancestor[1]/character_id",
        "mapping_strategy": "actor_enrichment_candidate",
        "fields": (
            _selected_field("name", "guild_name", ("string",)),
            _selected_field("rank_index", "guild_rank_index", ("integer",)),
            _selected_field("rank_name", "guild_rank_name", ("string",)),
        ),
    },
    {
        "group_id": "instance_context",
        "scope": "/combatants/*/ci_resolved/instance",
        "source_actor_expression": "@ancestor[1]/character_id",
        "mapping_strategy": "deduplicated_context_observation_candidate",
        "fields": (
            _selected_field("difficulty_index", "difficulty_index", ("integer",)),
            _selected_field("difficulty_name", "difficulty_name", ("string",)),
            _selected_field("instance_type", "instance_type", ("string",)),
            _selected_field("is_dynamic", "is_dynamic", ("boolean",)),
            _selected_field("map_id", "map_id", ("integer",)),
            _selected_field("max_players", "max_players", ("integer",)),
            _selected_field("name", "instance_name", ("string",)),
            _selected_field("player_difficulty", "player_difficulty", ("integer",)),
        ),
    },
    {
        "group_id": "specialization_summary",
        "scope": "/combatants/*/ci_resolved/specialization",
        "source_actor_expression": "@ancestor[1]/character_id",
        "mapping_strategy": "actor_enrichment_candidate",
        "fields": (
            _selected_field("active_spec_idx", "active_spec_idx", ("integer",)),
            _selected_field(
                "active_spec_name",
                "active_spec_name",
                ("string",),
                required=False,
            ),
            _selected_field(
                "active_spec_role",
                "active_spec_role",
                ("string",),
                required=False,
            ),
            _selected_field(
                "active_spec_slot",
                "active_spec_slot",
                ("integer",),
                required=False,
            ),
        ),
    },
    {
        "group_id": "talent_container_summary",
        "scope": "/combatants/*/ci_resolved/specialization/talents",
        "source_actor_expression": "@ancestor[2]/character_id",
        "mapping_strategy": "nested_observation_candidate",
        "fields": (
            _selected_field("class_label", "class_label", ("string",)),
            _selected_field("class_slug", "class_slug", ("string",)),
            _selected_field("tree_order", "tree_order", ("array",)),
        ),
    },
    {
        "group_id": "classless_talent_rank",
        "scope": "/combatants/*/ci_resolved/specialization/resolved_ca_talent_ranks/*",
        "source_actor_expression": "@ancestor[3]/character_id",
        "mapping_strategy": "nested_observation_candidate",
        "fields": (
            _selected_field("bisbeard_tree", "bisbeard_tree", ("string",)),
            _selected_field("cao_id", "cao_id", ("integer",)),
            _selected_field("icon", "icon", ("string",)),
            _selected_field("name", "name", ("string",)),
            _selected_field("rank", "rank", ("integer",)),
        ),
    },
    {
        "group_id": "hero_build_entry",
        "scope": "/combatants/*/ci_resolved/specialization/hero_build/*",
        "source_actor_expression": "@ancestor[3]/character_id",
        "mapping_strategy": "nested_observation_candidate",
        "fields": (
            _selected_field("entry_id", "entry_id", ("integer",)),
            _selected_field("rank", "rank", ("integer",)),
        ),
    },
    {
        "group_id": "gear_slot_summary",
        "scope": "/combatants/*/ci_resolved/gear/*",
        "source_actor_expression": "@ancestor[2]/character_id",
        "mapping_strategy": "nested_observation_candidate",
        "fields": (
            _selected_field("enchant", "enchant", ("integer",)),
            _selected_field("item_id", "item_id", ("integer",)),
            _selected_field("slot", "slot", ("integer",)),
            _selected_field("suffix", "suffix", ("integer",)),
            _selected_field("unique", "unique", ("integer",)),
        ),
    },
)


def _build_group(
    blueprint: Mapping[str, Any],
    scopes: Mapping[str, Mapping[str, Any]],
) -> tuple[dict[str, Any], set[str]]:
    scope_path = _required_string(blueprint.get("scope"), "selection group scope")
    scope = scopes.get(scope_path)
    if scope is None:
        raise ValueError(f"selected combatants scope is missing: {scope_path}")
    fields = _field_index(scope)
    selected_paths: set[str] = set()
    contracts: list[dict[str, Any]] = []
    for raw_blueprint in blueprint["fields"]:
        field_blueprint = _required_object(raw_blueprint, "selection field blueprint")
        source_name = _required_string(field_blueprint.get("source_name"), "source field name")
        source_path = scope_path.rstrip("/") + "/" + source_name
        source_field = fields.get(source_path)
        if source_field is None:
            raise ValueError(f"selected combatants field is missing: {source_path}")
        expected_types = set(_required_list(field_blueprint.get("types"), "field types"))
        if set(source_field.get("types", [])) != expected_types:
            raise ValueError(f"selected combatants field type mismatch: {source_path}")
        required = field_blueprint.get("required") is True
        if source_field.get("nullable") is not False:
            raise ValueError(f"selected combatants field is nullable: {source_path}")
        if required and source_field.get("observed_on_all_scope_occurrences") is not True:
            raise ValueError(f"required combatants field is not observed everywhere: {source_path}")
        if not required and source_field.get("observed_on_all_scope_occurrences") is not False:
            raise ValueError(f"optional combatants field unexpectedly appears everywhere: {source_path}")
        selected_paths.add(source_path)
        contracts.append(
            {
                "source_name": source_name,
                "source_path": source_path,
                "output_field": field_blueprint["output_field"],
                "types": sorted(expected_types),
                "nullable": False,
                "required": required,
                "occurrence_count": source_field.get("occurrence_count"),
                "observed_on_all_scope_occurrences": source_field.get(
                    "observed_on_all_scope_occurrences"
                ),
                "semantic_status": "reviewed_parser_candidate",
            }
        )
    return (
        {
            "group_id": blueprint["group_id"],
            "scope": scope_path,
            "source_actor_linkage": {
                "review_scope": _OUTER_ACTOR_SCOPE,
                "review_path": _OUTER_ACTOR_PATH,
                "expression": blueprint["source_actor_expression"],
                "stable_actor_strategy": "reuse_existing_source_actor_id",
                "status": "exact_path_confirmed_candidate_merge",
            },
            "mapping_strategy": blueprint["mapping_strategy"],
            "field_contracts": contracts,
            "selected_field_count": len(contracts),
            "mapping_status": "not_created",
        },
        selected_paths,
    )


def select_observed_combatants_info_fields(
    deep_review_path: Path,
    scope_review_path: Path,
) -> dict[str, Any]:
    """Select bounded combatants-info fields without creating a normalization mapping."""
    deep_review = _load_object(deep_review_path, "combatants-info deep review")
    scope_review = _load_object(scope_review_path, "report slice scope review")
    scopes = _validate_deep_review(deep_review)
    linkage_field = _validate_outer_actor_linkage(scope_review)

    groups: list[dict[str, Any]] = []
    selected_paths: set[str] = set()
    for blueprint in _SELECTION_GROUP_BLUEPRINTS:
        group, group_paths = _build_group(blueprint, scopes)
        groups.append(group)
        selected_paths.update(group_paths)

    all_direct_paths = {
        path
        for scope in scopes.values()
        for path in _field_index(scope)
    }
    deferred_paths = sorted(all_direct_paths - selected_paths)
    if len(selected_paths) != 37:
        raise ValueError("combatants-info selected field count mismatch")
    if len(deferred_paths) != 19:
        raise ValueError("combatants-info deferred field count mismatch")

    deferred_fields = [
        {
            "path": path,
            "decision": "deferred",
            "reason": (
                "duplicate source field, nested structure without a reviewed item contract, optional one-off "
                "shape, raw encoded value, resolved catalog object, or unresolved numeric-map semantics"
            ),
        }
        for path in deferred_paths
    ]
    missing_scopes = [
        {
            "scope": scope,
            "decision": "deferred",
            "reason": "scope_not_observed_in_exact_mapping_review",
        }
        for scope in sorted(_EXPECTED_MISSING_SCOPES)
    ]

    return {
        "schema_version": _SELECTION_SCHEMA_VERSION,
        "selection_kind": "observed_combatants_info_field_selection",
        "generated_at": _generated_at(),
        "source_deep_review_name": deep_review_path.name,
        "source_scope_review_name": scope_review_path.name,
        "source_persistence_run_id": deep_review.get("source_persistence_run_id"),
        "endpoint": {
            "endpoint_kind": _ENDPOINT_KIND,
            "route_template": _ROUTE_TEMPLATE,
            "payload_hash": _PAYLOAD_HASH,
            "schema_fingerprint": _SCHEMA_FINGERPRINT,
            "transport_provenance_type": "upstream_derived",
            "content_provenance_status": "candidate_companion_addon_enrichment",
        },
        "outer_actor_linkage": {
            "review_scope": _OUTER_ACTOR_SCOPE,
            "review_path": _OUTER_ACTOR_PATH,
            "types": list(linkage_field["types"]),
            "nullable": linkage_field["nullable"],
            "observed_on_all_scope_occurrences": linkage_field[
                "observed_on_all_scope_occurrences"
            ],
            "occurrence_count": linkage_field.get("occurrence_count"),
            "status": "exact_path_confirmed_candidate_merge",
        },
        "selection_groups": groups,
        "deferred_fields": deferred_fields,
        "missing_optional_scopes": missing_scopes,
        "decision_boundary": {
            "status": "candidate",
            "automatic_mapping_creation": False,
            "automatic_promotion": False,
            "can_promote": False,
            "actor_merge_verified": False,
            "companion_addon_provenance_verified": False,
            "nested_collection_semantics_verified": False,
            "combatants_info_enrichment_available": False,
            "normalization_allowed": False,
            "mechanic_semantics_verified": False,
            "planner_scoring_allowed": False,
            "ready_for_manual_mapping_design": True,
        },
        "summary": {
            "selection_group_count": len(groups),
            "selected_scope_count": len({group["scope"] for group in groups}),
            "selected_field_contract_count": len(selected_paths),
            "linkage_contract_count": len(groups),
            "unique_linkage_field_count": 1,
            "deferred_field_count": len(deferred_fields),
            "missing_optional_scope_count": len(missing_scopes),
            "generic_actor_enrichment_group_count": sum(
                group["mapping_strategy"] == "actor_enrichment_candidate" for group in groups
            ),
            "specialized_observation_group_count": sum(
                group["mapping_strategy"] != "actor_enrichment_candidate" for group in groups
            ),
            "contains_source_scalar_values": False,
            "all_source_reviews_consistent": True,
            "candidate_mapping_files_ready": False,
            "ready_for_manual_mapping_design": True,
            "combatants_info_enrichment_available": False,
            "normalization_allowed": False,
            "planner_scoring_allowed": False,
        },
    }
