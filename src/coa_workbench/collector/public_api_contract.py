from __future__ import annotations

from typing import Any, Mapping

from .source_registry import SourceRegistry

PUBLIC_API_CONTRACT_REVIEW_VERSION = "coa-public-api-contract-v1"
PUBLIC_API_SERVER = "https://coa.ascensionlogs.gg/api/public/v1"


def _mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    return value


def _array(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"{label} must be an array")
    return value


def _schema_type(schema: Mapping[str, Any]) -> tuple[str, ...]:
    value = schema.get("type")
    if isinstance(value, str):
        return (value,)
    if isinstance(value, list):
        return tuple(str(item) for item in value)
    return ()


def _parameters(operation: Mapping[str, Any]) -> tuple[dict[str, Any], ...]:
    rows: list[dict[str, Any]] = []
    for raw in operation.get("parameters", []):
        if not isinstance(raw, dict):
            continue
        schema = raw.get("schema") if isinstance(raw.get("schema"), dict) else {}
        enum = schema.get("enum") if isinstance(schema, dict) else None
        rows.append(
            {
                "name": str(raw.get("name", "")),
                "in": str(raw.get("in", "")),
                "required": bool(raw.get("required", False)),
                "types": list(_schema_type(schema)),
                "enum": [str(value) for value in enum] if isinstance(enum, list) else [],
                "has_default": "default" in schema,
            }
        )
    return tuple(rows)


def _effective_security(
    operation: Mapping[str, Any],
    document_security: Any,
) -> tuple[Mapping[str, Any], ...]:
    raw = operation["security"] if "security" in operation else document_security
    if raw is None:
        return ()
    return tuple(item for item in _array(raw, "security") if isinstance(item, dict))


def _route_inventory(openapi: Mapping[str, Any]) -> tuple[dict[str, Any], ...]:
    document_security = openapi.get("security")
    paths = _mapping(openapi.get("paths"), "paths")
    rows: list[dict[str, Any]] = []
    for path in sorted(paths):
        path_item = _mapping(paths[path], f"paths[{path}]")
        raw_get = path_item.get("get")
        if not isinstance(raw_get, dict):
            continue
        operation = _mapping(raw_get, f"paths[{path}].get")
        parameters = _parameters(operation)
        rows.append(
            {
                "path": str(path),
                "method": "GET",
                "scope": str(operation.get("x-scope")) if operation.get("x-scope") else None,
                "experimental": bool(operation.get("x-experimental", False)),
                "auth_required": bool(_effective_security(operation, document_security)),
                "parameter_keys": [
                    row["name"] for row in parameters if row["in"] == "query" and row["name"]
                ],
                "path_parameter_keys": [
                    row["name"] for row in parameters if row["in"] == "path" and row["name"]
                ],
                "required_parameter_keys": [
                    row["name"] for row in parameters if row["required"] and row["name"]
                ],
                "parameters": list(parameters),
            }
        )
    return tuple(rows)


def _parameter_enum(routes: tuple[dict[str, Any], ...], path: str, name: str) -> list[str]:
    for route in routes:
        if route["path"] != path:
            continue
        for parameter in route["parameters"]:
            if parameter["name"] == name:
                return list(parameter["enum"])
    return []


def _schema_property(
    openapi: Mapping[str, Any],
    schema_name: str,
    property_name: str,
) -> Mapping[str, Any]:
    components = _mapping(openapi.get("components"), "components")
    schemas = _mapping(components.get("schemas"), "components.schemas")
    schema = _mapping(schemas.get(schema_name), f"components.schemas.{schema_name}")
    properties = _mapping(schema.get("properties"), f"components.schemas.{schema_name}.properties")
    return _mapping(
        properties.get(property_name),
        f"components.schemas.{schema_name}.properties.{property_name}",
    )


def _contains_text(value: Any, *needles: str) -> bool:
    text = str(value or "").casefold()
    return all(needle.casefold() in text for needle in needles)


def _registry_crosscheck(
    routes: tuple[dict[str, Any], ...],
    registry: SourceRegistry,
) -> dict[str, Any]:
    documented = {str(route["path"]): route for route in routes}
    registered = {
        str(route.route_template): route
        for route in registry.routes
        if route.route_template is not None
    }
    missing = sorted(set(documented) - set(registered))
    extra = sorted(set(registered) - set(documented))
    parameter_match_count = 0
    parameter_mismatch_count = 0
    scope_match_count = 0
    scope_mismatch_count = 0
    experimental_match_count = 0
    experimental_mismatch_count = 0

    for path in sorted(set(documented) & set(registered)):
        doc = documented[path]
        reg = registered[path]
        if tuple(doc["parameter_keys"]) == reg.parameter_keys:
            parameter_match_count += 1
        else:
            parameter_mismatch_count += 1
        if doc["scope"] == reg.access_scope:
            scope_match_count += 1
        else:
            scope_mismatch_count += 1
        if bool(doc["experimental"]) == reg.experimental:
            experimental_match_count += 1
        else:
            experimental_mismatch_count += 1

    return {
        "server_url_matches": registry.base_url == PUBLIC_API_SERVER,
        "documented_route_count": len(documented),
        "registered_route_count": len(registered),
        "missing_registry_route_count": len(missing),
        "extra_registry_route_count": len(extra),
        "missing_registry_routes": missing,
        "extra_registry_routes": extra,
        "parameter_match_count": parameter_match_count,
        "parameter_mismatch_count": parameter_mismatch_count,
        "scope_match_count": scope_match_count,
        "scope_mismatch_count": scope_mismatch_count,
        "experimental_match_count": experimental_match_count,
        "experimental_mismatch_count": experimental_mismatch_count,
        "contract_registry_exact": (
            registry.base_url == PUBLIC_API_SERVER
            and not missing
            and not extra
            and parameter_mismatch_count == 0
            and scope_mismatch_count == 0
            and experimental_mismatch_count == 0
        ),
    }


def build_public_api_contract_review(
    openapi: Mapping[str, Any],
    *,
    registry: SourceRegistry | None = None,
) -> dict[str, Any]:
    info = _mapping(openapi.get("info"), "info")
    servers = _array(openapi.get("servers"), "servers")
    server_urls = [
        str(item.get("url")) for item in servers if isinstance(item, dict) and item.get("url")
    ]
    routes = _route_inventory(openapi)

    access = _mapping(openapi.get("x-access"), "x-access")
    scopes = _mapping(access.get("scopes"), "x-access.scopes")
    tiers = _mapping(access.get("tiers"), "x-access.tiers")

    event_id = _schema_property(openapi, "Event", "id")
    event_timestamp = _schema_property(openapi, "Event", "timestamp_ms")
    event_amount = _schema_property(openapi, "Event", "amount")
    event_spell = _schema_property(openapi, "Event", "spell_id")
    event_glancing = _schema_property(openapi, "Event", "is_glancing")
    encounter_duration = _schema_property(openapi, "EncounterSummary", "duration_seconds")

    stats_paths = [route for route in routes if route["scope"] == "stats:read"]
    event_paths = [route for route in routes if route["scope"] == "events:read"]
    public_paths = [route for route in routes if not route["auth_required"]]

    info_description = str(info.get("description", ""))
    stats_scope = _mapping(scopes.get("stats:read"), "x-access.scopes.stats:read")
    events_scope = _mapping(scopes.get("events:read"), "x-access.scopes.events:read")

    surface_paths = {str(route["path"]) for route in routes}
    result: dict[str, Any] = {
        "review_version": PUBLIC_API_CONTRACT_REVIEW_VERSION,
        "source": {
            "openapi_version": str(openapi.get("openapi", "")),
            "api_title": str(info.get("title", "")),
            "api_version": str(info.get("version", "")),
            "server_urls": server_urls,
            "official_server_matches": PUBLIC_API_SERVER in server_urls,
        },
        "access": {
            "stats_read_availability": stats_scope.get("availability"),
            "events_read_availability": events_scope.get("availability"),
            "events_read_experimental": bool(events_scope.get("experimental", False)),
            "free_tier_per_minute": _mapping(tiers.get("free"), "x-access.tiers.free").get(
                "perMinute"
            ),
            "free_tier_per_day": _mapping(tiers.get("free"), "x-access.tiers.free").get(
                "perDay"
            ),
            "visible_attribution_required": _contains_text(
                info_description, "visible attribution", "linking back"
            ),
            "bulk_redistribution_permitted": not _contains_text(
                info_description, "bulk redistribution", "not permitted"
            ),
        },
        "routes": {
            "total_get_route_count": len(routes),
            "unauthenticated_route_count": len(public_paths),
            "stats_read_route_count": len(stats_paths),
            "events_read_route_count": len(event_paths),
            "experimental_route_count": sum(bool(route["experimental"]) for route in routes),
            "inventory": [
                {
                    "path": route["path"],
                    "scope": route["scope"],
                    "experimental": route["experimental"],
                    "auth_required": route["auth_required"],
                    "parameter_keys": route["parameter_keys"],
                    "path_parameter_keys": route["path_parameter_keys"],
                    "required_parameter_keys": route["required_parameter_keys"],
                }
                for route in routes
            ],
        },
        "statistics_contract": {
            "difficulty_enum": _parameter_enum(routes, "/statistics", "difficulty"),
            "metric_enum": _parameter_enum(routes, "/statistics", "metric"),
            "damage_mode_enum": _parameter_enum(routes, "/statistics", "damageMode"),
            "role_enum": _parameter_enum(routes, "/statistics", "role"),
        },
        "event_contract": {
            "event_id_serialized_as_string": _schema_type(event_id) == ("string",),
            "amount_serialized_as_string": _schema_type(event_amount) == ("string",),
            "timestamp_ms_is_integer": _schema_type(event_timestamp) == ("integer",),
            "timestamp_relative_to_combat_start_documented": _contains_text(
                event_timestamp.get("description"), "millisecond", "combat start"
            ),
            "melee_sentinel_minus_one_documented": _contains_text(
                event_spell.get("description"), "-1", "melee"
            ),
            "glancing_null_not_absence_documented": _contains_text(
                event_glancing.get("description"), "null", "not recorded"
            ),
            "duration_seconds_is_integer_or_null": set(_schema_type(encounter_duration))
            == {"integer", "null"},
            "actor_dictionary_endpoint_documented": (
                "/reports/{reportId}/encounters/{encounterId}/actors" in surface_paths
            ),
        },
        "surface_gaps": {
            "builds_endpoint_documented": any("build" in path.casefold() for path in surface_paths),
            "armory_endpoint_documented": any("armory" in path.casefold() for path in surface_paths),
            "guild_endpoint_documented": any("guild" in path.casefold() for path in surface_paths),
            "tier_list_endpoint_documented": any("tier" in path.casefold() for path in surface_paths),
        },
        "verification": {
            "official_documented_contract_observed": True,
            "stats_read_self_serve_documented": stats_scope.get("availability") == "self-serve",
            "events_read_on_request_documented": events_scope.get("availability") == "on-request",
            "site_tier_list_algorithm_verified": False,
            "planner_scoring_allowed": False,
        },
        "privacy": {
            "api_key_included": False,
            "report_ids_included": False,
            "encounter_ids_included": False,
            "player_names_included": False,
            "raw_event_values_included": False,
        },
        "public_release_safe": True,
    }
    if registry is not None:
        result["registry_crosscheck"] = _registry_crosscheck(routes, registry)
    return result


__all__ = [
    "PUBLIC_API_CONTRACT_REVIEW_VERSION",
    "PUBLIC_API_SERVER",
    "build_public_api_contract_review",
]
