from __future__ import annotations

from pathlib import Path

from coa_workbench.collector.public_api_contract import build_public_api_contract_review
from coa_workbench.collector.source_registry import load_source_registry


def _query(name: str, *, required: bool = False, enum: list[str] | None = None) -> dict:
    schema: dict[str, object] = {"type": "string"}
    if enum is not None:
        schema["enum"] = enum
    return {"name": name, "in": "query", "required": required, "schema": schema}


def _path(name: str) -> dict:
    return {"name": name, "in": "path", "required": True, "schema": {"type": "integer"}}


def _spec() -> dict:
    return {
        "openapi": "3.1.0",
        "info": {
            "title": "Conquest of Azeroth Logs External API",
            "version": "1.0.0",
            "description": (
                "Public display of this data requires visible attribution linking back to the "
                "site; bulk redistribution of the dataset is not permitted."
            ),
        },
        "x-access": {
            "scopes": {
                "stats:read": {"availability": "self-serve"},
                "events:read": {"availability": "on-request", "experimental": True},
            },
            "tiers": {
                "free": {"perMinute": 30, "perDay": 5000, "scopes": ["stats:read"]}
            },
        },
        "servers": [{"url": "https://coa.ascensionlogs.gg/api/public/v1"}],
        "security": [{"bearerAuth": []}],
        "components": {
            "schemas": {
                "Event": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "timestamp_ms": {
                            "type": "integer",
                            "description": "Milliseconds from that encounter's combat start.",
                        },
                        "amount": {"type": "string"},
                        "spell_id": {
                            "type": ["integer", "null"],
                            "description": "-1 is the melee sentinel.",
                        },
                        "is_glancing": {
                            "type": ["boolean", "null"],
                            "description": "Null means not recorded.",
                        },
                    },
                },
                "EncounterSummary": {
                    "type": "object",
                    "properties": {
                        "duration_seconds": {"type": ["integer", "null"]},
                    },
                },
            }
        },
        "paths": {
            "/statistics": {
                "get": {
                    "x-scope": "stats:read",
                    "parameters": [
                        _query("phase", required=True),
                        _query("difficulty", enum=["normal", "heroic", "mythic", "ascended", "all"]),
                        _query("metric", enum=["avg_dps", "avg_hps", "avg_dtps"]),
                        _query("bracket"),
                        _query("location"),
                        _query("bossId"),
                        _query("damageMode", enum=["standard", "boss-only", "trash"]),
                        _query("role", enum=["tank", "dps", "tanks-and-dps", "support"]),
                        _query("class"),
                        _query("spec"),
                        _query("weekNumber"),
                        _query("realm"),
                    ],
                }
            },
            "/phases": {"get": {"x-scope": "stats:read", "parameters": [_query("realm")] }},
            "/bosses": {"get": {"x-scope": "stats:read", "parameters": []}},
            "/reports": {
                "get": {
                    "x-scope": "events:read",
                    "x-experimental": True,
                    "parameters": [_query("limit"), _query("offset"), _query("since")],
                }
            },
            "/reports/{reportId}": {
                "get": {
                    "x-scope": "events:read",
                    "x-experimental": True,
                    "parameters": [_path("reportId")],
                }
            },
            "/reports/{reportId}/encounters/{encounterId}/events": {
                "get": {
                    "x-scope": "events:read",
                    "x-experimental": True,
                    "parameters": [
                        _path("reportId"),
                        _path("encounterId"),
                        _query("groups"),
                        _query("event_types"),
                        _query("melee_only"),
                        _query("source_ids"),
                        _query("target_ids"),
                        _query("spell_ids"),
                        _query("start_ms"),
                        _query("end_ms"),
                        _query("limit"),
                        _query("cursor"),
                    ],
                }
            },
            "/reports/{reportId}/encounters/{encounterId}/actors": {
                "get": {
                    "x-scope": "events:read",
                    "x-experimental": True,
                    "parameters": [_path("reportId"), _path("encounterId")],
                }
            },
            "/health": {"get": {"security": [], "parameters": []}},
            "/openapi.json": {"get": {"security": [], "parameters": []}},
        },
    }


def _registry():
    return load_source_registry(Path("config/coa_public_api_sources.yaml"))


def test_official_public_api_registry_separates_self_serve_and_experimental_routes() -> None:
    registry = _registry()
    assert registry.source_code == "coa_ascension_logs_public_api"
    assert registry.base_url == "https://coa.ascensionlogs.gg/api/public/v1"
    assert len(registry.routes) == 9

    statistics = registry.route("public_api_statistics")
    assert statistics.access_scope == "stats:read"
    assert statistics.experimental is False
    assert statistics.production_ready is True
    assert statistics.parameter_keys == (
        "phase",
        "difficulty",
        "metric",
        "bracket",
        "location",
        "bossId",
        "damageMode",
        "role",
        "class",
        "spec",
        "weekNumber",
        "realm",
    )

    events = registry.route("public_api_encounter_events")
    assert events.access_scope == "events:read"
    assert events.experimental is True
    assert events.production_ready is False
    assert events.observatory_ready is True
    assert events.scope_path_keys == ("reportId", "encounterId")


def test_openapi_contract_review_is_scalar_safe_and_registry_exact() -> None:
    review = build_public_api_contract_review(_spec(), registry=_registry())

    assert review["source"]["api_version"] == "1.0.0"
    assert review["routes"]["total_get_route_count"] == 9
    assert review["routes"]["unauthenticated_route_count"] == 2
    assert review["routes"]["stats_read_route_count"] == 3
    assert review["routes"]["events_read_route_count"] == 4
    assert review["routes"]["experimental_route_count"] == 4
    assert review["access"] == {
        "stats_read_availability": "self-serve",
        "events_read_availability": "on-request",
        "events_read_experimental": True,
        "free_tier_per_minute": 30,
        "free_tier_per_day": 5000,
        "visible_attribution_required": True,
        "bulk_redistribution_permitted": False,
    }
    assert review["statistics_contract"]["metric_enum"] == [
        "avg_dps",
        "avg_hps",
        "avg_dtps",
    ]
    assert review["event_contract"]["timestamp_relative_to_combat_start_documented"] is True
    assert review["event_contract"]["melee_sentinel_minus_one_documented"] is True
    assert review["event_contract"]["glancing_null_not_absence_documented"] is True
    assert review["event_contract"]["duration_seconds_is_integer_or_null"] is True
    assert review["surface_gaps"] == {
        "builds_endpoint_documented": False,
        "armory_endpoint_documented": False,
        "guild_endpoint_documented": False,
        "tier_list_endpoint_documented": False,
    }
    assert review["registry_crosscheck"]["contract_registry_exact"] is True
    assert review["verification"]["planner_scoring_allowed"] is False
    assert review["privacy"]["api_key_included"] is False
    assert review["public_release_safe"] is True
