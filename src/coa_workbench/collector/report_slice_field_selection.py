from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

_SELECTION_SCHEMA_VERSION = 1
_SCOPE_REVIEW_KIND = "observed_report_slice_scope_review"
_SOURCE_CODE = "coa_ascension_logs"

_ENDPOINTS: dict[str, dict[str, str]] = {
    "report_detail": {
        "route_template": "/api/reports/{template}",
        "payload_hash": "161739896f0b8321f884bcc24d1896efb894a9c6e05166269189f9871c64cba9",
        "schema_fingerprint": "3d533a4178b67957bbd31544ddf5484bd5959635ebd5edcdd0c7689a4bace216",
    },
    "encounter_detail": {
        "route_template": "/api/reports/{template}/encounters/{template}",
        "payload_hash": "955437d6c9c287cc7db280dd2388b88603af2785508061b95c7811dcd272fe22",
        "schema_fingerprint": "567f36824efb37a29b835df01ce9b1fcc79eae57d6230202d16a6265c6ca0e85",
    },
    "combatants_info": {
        "route_template": "/api/reports/{template}/encounters/{template}/combatants-info",
        "payload_hash": "45672e0f0ff9eb461c575bdd38385795daa6326378bc3f8ad51474276140dc14",
        "schema_fingerprint": "41d6d15422c668f83d2ccae1ec0ff2969671861f9e43b21cb371578961c5f8ff",
    },
}

_EXPECTED_SCOPES = {
    ("combatants_info", "/combatants/*"),
    ("combatants_info", "/combatants/*/ci_resolved"),
    ("combatants_info", "/combatants/*/ci_resolved/specialization"),
    ("encounter_detail", "/encounter"),
    ("encounter_detail", "/character_stats/*"),
    ("report_detail", "/report"),
    ("report_detail", "/encounters/*"),
}


def _generated_at() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _field(
    canonical_field: str,
    expression: str,
    review_scope: str,
    review_path: str,
    types: tuple[str, ...],
    *,
    nullable: bool = False,
    required: bool = True,
) -> dict[str, Any]:
    return {
        "canonical_field": canonical_field,
        "expression": expression,
        "review_scope": review_scope,
        "review_path": review_path,
        "types": list(types),
        "nullable": nullable,
        "required": required,
    }


_MAPPING_BLUEPRINTS: tuple[dict[str, Any], ...] = (
    {
        "mapping_id": "coa-report-detail-v1",
        "mapping_file": "coa_report_detail_v1.json",
        "endpoint_kind": "report_detail",
        "entities": {
            "reports": {
                "collection": "/report",
                "fields": (
                    _field("source_report_id", "@item/id", "/report", "/report/id", ("integer",)),
                    _field("title", "@item/title", "/report", "/report/title", ("string",)),
                    _field(
                        "created_at",
                        "@item/created_at",
                        "/report",
                        "/report/created_at",
                        ("string",),
                    ),
                    _field(
                        "start_time",
                        "@item/start_time",
                        "/report",
                        "/report/start_time",
                        ("string",),
                    ),
                    _field("end_time", "@item/end_time", "/report", "/report/end_time", ("string",)),
                    _field(
                        "visibility",
                        "@item/visibility",
                        "/report",
                        "/report/visibility",
                        ("string",),
                    ),
                    _field("timezone", "@item/timezone", "/report", "/report/timezone", ("string",)),
                    _field("realm", "@item/realm", "/report", "/report/realm", ("string",)),
                    _field("zone", "@item/zone", "/report", "/report/zone", ("string",)),
                    _field("status", "@item/status", "/report", "/report/status", ("string",)),
                    _field(
                        "has_telemetry",
                        "@item/has_telemetry",
                        "/report",
                        "/report/has_telemetry",
                        ("boolean",),
                    ),
                ),
                "required": (
                    "source_report_id",
                    "title",
                    "created_at",
                    "start_time",
                    "end_time",
                    "visibility",
                    "timezone",
                    "realm",
                    "zone",
                    "status",
                    "has_telemetry",
                ),
            },
            "encounters": {
                "collection": "/encounters/*",
                "fields": (
                    _field(
                        "source_encounter_id",
                        "@item/id",
                        "/encounters/*",
                        "/encounters/*/id",
                        ("integer",),
                    ),
                    _field(
                        "source_report_id",
                        "@root/report/id",
                        "/report",
                        "/report/id",
                        ("integer",),
                    ),
                    _field(
                        "name",
                        "@item/name",
                        "/encounters/*",
                        "/encounters/*/name",
                        ("string",),
                    ),
                    _field(
                        "start_time",
                        "@item/start_time",
                        "/encounters/*",
                        "/encounters/*/start_time",
                        ("string",),
                    ),
                    _field(
                        "end_time",
                        "@item/end_time",
                        "/encounters/*",
                        "/encounters/*/end_time",
                        ("string",),
                    ),
                    _field(
                        "success",
                        "@item/success",
                        "/encounters/*",
                        "/encounters/*/success",
                        ("boolean",),
                    ),
                    _field(
                        "kill_time",
                        "@item/kill_time",
                        "/encounters/*",
                        "/encounters/*/kill_time",
                        ("null", "object"),
                        nullable=True,
                        required=False,
                    ),
                    _field(
                        "wipe_percent",
                        "@item/wipe_percent",
                        "/encounters/*",
                        "/encounters/*/wipe_percent",
                        ("null", "string"),
                        nullable=True,
                        required=False,
                    ),
                ),
                "required": (
                    "source_encounter_id",
                    "source_report_id",
                    "name",
                    "start_time",
                    "end_time",
                    "success",
                ),
            },
        },
        "review_notes": (
            "Normalizes the exact report object and its fourteen observed encounter-list items.",
            "The encounter-to-report relation uses the exact reviewed /report/id root field.",
            "Speed-run, processing-warning, guild and uploader fields remain deferred from this minimal slice.",
        ),
    },
    {
        "mapping_id": "coa-encounter-detail-v1",
        "mapping_file": "coa_encounter_detail_v1.json",
        "endpoint_kind": "encounter_detail",
        "entities": {
            "reports": {
                "collection": "/encounter",
                "fields": (
                    _field(
                        "source_report_id",
                        "@item/report_id",
                        "/encounter",
                        "/encounter/report_id",
                        ("integer",),
                    ),
                    _field(
                        "realm",
                        "@item/report_realm",
                        "/encounter",
                        "/encounter/report_realm",
                        ("string",),
                    ),
                ),
                "required": ("source_report_id",),
            },
            "encounters": {
                "collection": "/encounter",
                "fields": (
                    _field(
                        "source_encounter_id",
                        "@item/id",
                        "/encounter",
                        "/encounter/id",
                        ("integer",),
                    ),
                    _field(
                        "source_report_id",
                        "@item/report_id",
                        "/encounter",
                        "/encounter/report_id",
                        ("integer",),
                    ),
                    _field("name", "@item/name", "/encounter", "/encounter/name", ("string",)),
                    _field(
                        "start_time",
                        "@item/start_time",
                        "/encounter",
                        "/encounter/start_time",
                        ("string",),
                    ),
                    _field(
                        "end_time",
                        "@item/end_time",
                        "/encounter",
                        "/encounter/end_time",
                        ("string",),
                    ),
                    _field(
                        "success",
                        "@item/success",
                        "/encounter",
                        "/encounter/success",
                        ("boolean",),
                    ),
                    _field(
                        "difficulty",
                        "@item/difficulty",
                        "/encounter",
                        "/encounter/difficulty",
                        ("string",),
                    ),
                    _field(
                        "duration_seconds",
                        "@item/duration_seconds",
                        "/encounter",
                        "/encounter/duration_seconds",
                        ("string",),
                    ),
                    _field(
                        "player_count",
                        "@item/player_count",
                        "/encounter",
                        "/encounter/player_count",
                        ("integer",),
                    ),
                    _field("zone", "@item/zone", "/encounter", "/encounter/zone", ("string",)),
                    _field(
                        "is_boss_encounter",
                        "@item/is_boss_encounter",
                        "/encounter",
                        "/encounter/is_boss_encounter",
                        ("boolean",),
                    ),
                    _field(
                        "boss_id",
                        "@item/boss_id",
                        "/encounter",
                        "/encounter/boss_id",
                        ("integer",),
                    ),
                    _field(
                        "creature_id",
                        "@item/creature_id",
                        "/encounter",
                        "/encounter/creature_id",
                        ("integer",),
                    ),
                    _field(
                        "trial_level",
                        "@item/trial_level",
                        "/encounter",
                        "/encounter/trial_level",
                        ("null",),
                        nullable=True,
                        required=False,
                    ),
                    _field(
                        "wipe_percent",
                        "@item/wipe_percent",
                        "/encounter",
                        "/encounter/wipe_percent",
                        ("null",),
                        nullable=True,
                        required=False,
                    ),
                ),
                "required": (
                    "source_encounter_id",
                    "source_report_id",
                    "name",
                    "start_time",
                    "end_time",
                    "success",
                    "difficulty",
                    "duration_seconds",
                    "player_count",
                    "zone",
                    "is_boss_encounter",
                    "boss_id",
                    "creature_id",
                ),
            },
            "actors": {
                "collection": "/character_stats/*",
                "fields": (
                    _field(
                        "source_actor_id",
                        "@item/character_id",
                        "/character_stats/*",
                        "/character_stats/*/character_id",
                        ("integer",),
                    ),
                    _field(
                        "name",
                        "@item/name",
                        "/character_stats/*",
                        "/character_stats/*/name",
                        ("string",),
                    ),
                    _field(
                        "actor_type",
                        "@item/character_type",
                        "/character_stats/*",
                        "/character_stats/*/character_type",
                        ("string",),
                    ),
                    _field(
                        "class",
                        "@item/class",
                        "/character_stats/*",
                        "/character_stats/*/class",
                        ("null", "string"),
                        nullable=True,
                        required=False,
                    ),
                    _field(
                        "spec",
                        "@item/spec",
                        "/character_stats/*",
                        "/character_stats/*/spec",
                        ("null", "string"),
                        nullable=True,
                        required=False,
                    ),
                    _field(
                        "level",
                        "@item/level",
                        "/character_stats/*",
                        "/character_stats/*/level",
                        ("null",),
                        nullable=True,
                        required=False,
                    ),
                ),
                "required": ("source_actor_id", "name", "actor_type"),
            },
            "participants": {
                "collection": "/character_stats/*",
                "fields": (
                    _field(
                        "source_encounter_id",
                        "@item/encounter_id",
                        "/character_stats/*",
                        "/character_stats/*/encounter_id",
                        ("integer",),
                    ),
                    _field(
                        "source_actor_id",
                        "@item/character_id",
                        "/character_stats/*",
                        "/character_stats/*/character_id",
                        ("integer",),
                    ),
                    _field(
                        "avg_dps",
                        "@item/avg_dps",
                        "/character_stats/*",
                        "/character_stats/*/avg_dps",
                        ("number",),
                    ),
                    _field(
                        "avg_hps",
                        "@item/avg_hps",
                        "/character_stats/*",
                        "/character_stats/*/avg_hps",
                        ("integer", "number"),
                    ),
                    _field(
                        "damage_taken",
                        "@item/damage_taken",
                        "/character_stats/*",
                        "/character_stats/*/damage_taken",
                        ("integer",),
                    ),
                    _field(
                        "deaths",
                        "@item/deaths",
                        "/character_stats/*",
                        "/character_stats/*/deaths",
                        ("integer",),
                    ),
                    _field(
                        "effective_healing",
                        "@item/effective_healing",
                        "/character_stats/*",
                        "/character_stats/*/effective_healing",
                        ("integer",),
                    ),
                    _field(
                        "encounter_duration",
                        "@item/encounter_duration",
                        "/character_stats/*",
                        "/character_stats/*/encounter_duration",
                        ("number",),
                    ),
                    _field(
                        "is_consolidated",
                        "@item/is_consolidated",
                        "/character_stats/*",
                        "/character_stats/*/is_consolidated",
                        ("boolean",),
                    ),
                    _field(
                        "total_absorbs",
                        "@item/total_absorbs",
                        "/character_stats/*",
                        "/character_stats/*/total_absorbs",
                        ("integer",),
                    ),
                    _field(
                        "total_damage",
                        "@item/total_damage",
                        "/character_stats/*",
                        "/character_stats/*/total_damage",
                        ("integer",),
                    ),
                    _field(
                        "total_healing",
                        "@item/total_healing",
                        "/character_stats/*",
                        "/character_stats/*/total_healing",
                        ("integer",),
                    ),
                ),
                "required": (
                    "source_encounter_id",
                    "source_actor_id",
                    "avg_dps",
                    "avg_hps",
                    "encounter_duration",
                    "is_consolidated",
                ),
            },
        },
        "review_notes": (
            "Creates a minimal report reference from /encounter/report_id so the generic normalizer can preserve exact report-to-encounter linkage inside this payload.",
            "Normalizes one exact encounter, thirty-one actor rows and thirty-one participant rows.",
            "Pet contributions, rankings, target damage and healing breakdowns remain deferred.",
        ),
    },
)


def _required_object(value: object, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be an object")
    return value


def _required_list(value: object, name: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"{name} must be an array")
    return value


def _load_review(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return _required_object(payload, "scope review")


def _scope_index(review: Mapping[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    result: dict[tuple[str, str], dict[str, Any]] = {}
    for raw_scope in _required_list(review.get("scopes"), "scope review.scopes"):
        scope = _required_object(raw_scope, "scope review.scopes[]")
        endpoint_kind = scope.get("endpoint_kind")
        scope_path = scope.get("scope")
        if not isinstance(endpoint_kind, str) or not isinstance(scope_path, str):
            raise ValueError("scope review contains an invalid endpoint/scope key")
        key = (endpoint_kind, scope_path)
        if key in result:
            raise ValueError(f"duplicate scope review key: {key}")
        result[key] = scope
    return result


def _field_index(scope: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for raw_field in _required_list(scope.get("direct_fields"), "scope.direct_fields"):
        field = _required_object(raw_field, "scope.direct_fields[]")
        path = field.get("path")
        if not isinstance(path, str) or not path:
            raise ValueError("scope direct field has no valid path")
        if path in result:
            raise ValueError(f"duplicate direct field path: {path}")
        result[path] = field
    return result


def _validate_review(review: Mapping[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    if review.get("schema_version") != 1 or review.get("review_kind") != _SCOPE_REVIEW_KIND:
        raise ValueError("unsupported observed report slice scope review")

    summary = _required_object(review.get("summary"), "scope review.summary")
    boundary = _required_object(review.get("decision_boundary"), "scope review.decision_boundary")
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
    for name, expected in expected_summary.items():
        if summary.get(name) != expected:
            raise ValueError(f"scope review summary mismatch for {name}")

    expected_boundary = {
        "status": "candidate",
        "automatic_scope_selection": False,
        "automatic_field_selection": False,
        "can_promote": False,
        "semantic_verification_required": True,
        "normalization_allowed": False,
    }
    for name, expected in expected_boundary.items():
        if boundary.get(name) != expected:
            raise ValueError(f"scope review decision boundary mismatch for {name}")

    scopes = _scope_index(review)
    if set(scopes) != _EXPECTED_SCOPES:
        raise ValueError("scope review does not contain the exact expected scope set")

    for key, scope in scopes.items():
        endpoint_kind, _scope_path = key
        endpoint = _ENDPOINTS[endpoint_kind]
        if scope.get("route_template") != endpoint["route_template"]:
            raise ValueError(f"route template mismatch for {endpoint_kind}")
        if scope.get("payload_hash") != endpoint["payload_hash"]:
            raise ValueError(f"payload hash mismatch for {endpoint_kind}")
        if scope.get("schema_fingerprint") != endpoint["schema_fingerprint"]:
            raise ValueError(f"schema fingerprint mismatch for {endpoint_kind}")
        if scope.get("review_status") != "candidate":
            raise ValueError(f"scope {key} is not a candidate")
        if scope.get("semantic_status") != "unverified_candidate":
            raise ValueError(f"scope {key} has an unexpected semantic status")
        if scope.get("manual_decision_required") is not True:
            raise ValueError(f"scope {key} does not require a manual decision")
    return scopes


def _validate_field_contract(
    scopes: Mapping[tuple[str, str], Mapping[str, Any]],
    *,
    endpoint_kind: str,
    contract: Mapping[str, Any],
) -> None:
    review_scope = str(contract["review_scope"])
    review_path = str(contract["review_path"])
    scope = scopes.get((endpoint_kind, review_scope))
    if scope is None:
        raise ValueError(f"selected review scope not found: {endpoint_kind} {review_scope}")
    field = _field_index(scope).get(review_path)
    if field is None:
        raise ValueError(f"selected review path not found: {endpoint_kind} {review_path}")

    expected_types = set(contract["types"])
    if set(field.get("types", [])) != expected_types:
        raise ValueError(f"selected field type mismatch: {endpoint_kind} {review_path}")
    if field.get("nullable") is not contract["nullable"]:
        raise ValueError(f"selected field nullable mismatch: {endpoint_kind} {review_path}")
    if contract["required"]:
        if field.get("observed_on_all_scope_occurrences") is not True:
            raise ValueError(f"required selected field is not observed everywhere: {review_path}")
        if field.get("nullable") is True:
            raise ValueError(f"required selected field is nullable: {review_path}")


def _mapping_from_blueprint(
    blueprint: Mapping[str, Any],
    scopes: Mapping[tuple[str, str], Mapping[str, Any]],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    endpoint_kind = str(blueprint["endpoint_kind"])
    endpoint = _ENDPOINTS[endpoint_kind]
    entities: dict[str, Any] = {}
    field_contracts: list[dict[str, Any]] = []
    selected_review_paths: set[str] = set()
    selected_review_scopes: set[str] = set()

    for entity_name, raw_entity in _required_object(blueprint["entities"], "blueprint.entities").items():
        entity = _required_object(raw_entity, f"blueprint.entities.{entity_name}")
        raw_fields = entity["fields"]
        fields: dict[str, Any] = {}
        for raw_contract in raw_fields:
            contract = _required_object(raw_contract, "blueprint field contract")
            _validate_field_contract(scopes, endpoint_kind=endpoint_kind, contract=contract)
            canonical_field = str(contract["canonical_field"])
            fields[canonical_field] = contract["expression"]
            selected_review_paths.add(str(contract["review_path"]))
            selected_review_scopes.add(str(contract["review_scope"]))
            field_contracts.append(
                {
                    "entity": entity_name,
                    **contract,
                    "semantic_status": "reviewed_candidate",
                }
            )
        entities[entity_name] = {
            "collection": entity["collection"],
            "fields": fields,
            "required": list(entity["required"]),
        }

    deferred_fields: list[str] = []
    for review_scope in sorted(selected_review_scopes):
        scope = scopes[(endpoint_kind, review_scope)]
        for path in sorted(_field_index(scope)):
            if path not in selected_review_paths:
                deferred_fields.append(path)

    mapping = {
        "mapping_schema_version": 1,
        "mapping_id": blueprint["mapping_id"],
        "source_code": _SOURCE_CODE,
        "mapping_version": "1",
        "status": "candidate",
        "route_template": endpoint["route_template"],
        "schema_fingerprint": endpoint["schema_fingerprint"],
        "reviewed_payload_hash": endpoint["payload_hash"],
        "review_summary_schema_version": 1,
        "provenance_type": "upstream_derived",
        "entities": entities,
        "event_type_map": {},
        "field_contracts": field_contracts,
        "deferred_fields": deferred_fields,
        "deferred_scopes": [],
        "review_notes": list(blueprint["review_notes"]),
    }
    return mapping, field_contracts


def select_observed_report_slice_fields(scope_review_path: Path) -> dict[str, Any]:
    """Select the minimal scalar-free candidate mappings from the exact scope review."""
    review = _load_review(scope_review_path)
    scopes = _validate_review(review)

    mappings: list[dict[str, Any]] = []
    selected_contract_count = 0
    selected_scope_keys: set[tuple[str, str]] = set()
    for blueprint in _MAPPING_BLUEPRINTS:
        mapping, contracts = _mapping_from_blueprint(blueprint, scopes)
        selected_contract_count += len(contracts)
        selected_scope_keys.update(
            (str(blueprint["endpoint_kind"]), str(contract["review_scope"]))
            for contract in contracts
        )
        mappings.append(
            {
                "mapping_file": blueprint["mapping_file"],
                "mapping": mapping,
                "selected_field_contract_count": len(contracts),
            }
        )

    deferred_scope_keys = sorted(_EXPECTED_SCOPES - selected_scope_keys)
    deferred_scopes = [
        {
            "endpoint_kind": endpoint_kind,
            "scope": scope,
            "decision": "deferred",
            "reason": (
                "combatants-info is companion-addon enrichment; actor merge provenance, nested player fields, "
                "specialization codebooks and nested talent/gear contracts require a separate review"
            ),
        }
        for endpoint_kind, scope in deferred_scope_keys
    ]

    return {
        "schema_version": _SELECTION_SCHEMA_VERSION,
        "selection_kind": "observed_report_slice_field_selection",
        "generated_at": _generated_at(),
        "source_scope_review_name": scope_review_path.name,
        "mappings": mappings,
        "deferred_scopes": deferred_scopes,
        "decision_boundary": {
            "status": "candidate",
            "automatic_promotion": False,
            "can_promote": False,
            "semantic_verification_required": True,
            "normalization_allowed": False,
            "manual_mapping_review_required": True,
        },
        "summary": {
            "mapping_count": len(mappings),
            "selected_scope_count": len(selected_scope_keys),
            "selected_field_contract_count": selected_contract_count,
            "deferred_scope_count": len(deferred_scopes),
            "contains_source_scalar_values": False,
            "all_source_scopes_consistent": True,
            "candidate_mapping_files_ready": True,
            "normalization_allowed": False,
        },
    }
