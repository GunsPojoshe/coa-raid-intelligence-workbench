from pathlib import Path

import pytest

from coa_workbench.collector.source_registry import (
    UnverifiedSourceRouteError,
    load_source_registry,
)


def registry_path() -> Path:
    return Path(__file__).resolve().parents[2] / "config" / "ascension_logs_sources.yaml"


def test_registry_loads_primary_observation_source() -> None:
    registry = load_source_registry(registry_path())
    assert registry.schema_version == 7
    assert registry.source_code == "coa_ascension_logs"
    assert registry.base_url == "https://coa.ascensionlogs.gg"
    assert registry.truth_role == "primary_observation_source"
    assert len(registry.routes) == 22
    assert registry.prohibited_assumptions


def test_public_routes_are_available_only_as_discovery_probes() -> None:
    registry = load_source_registry(registry_path())
    assert {
        "public_home",
        "public_reports",
        "public_faq",
        "public_guild_progression",
    } <= {route.endpoint_code for route in registry.routes}
    for endpoint_code in (
        "public_home",
        "public_reports",
        "public_faq",
        "public_guild_progression",
    ):
        route = registry.route(endpoint_code)
        assert route.status == "verified_html"
        assert route.production_ready is False
        assert route.observatory_ready is False
        assert route.scope_path_keys == ()


def test_network_observed_progression_routes_are_observatory_ready() -> None:
    registry = load_source_registry(registry_path())

    phases = registry.route("phases_api")
    assert phases.route_template == "/api/phases"
    assert phases.method == "GET"
    assert phases.empty_params_observed is True
    assert phases.dimension_keys == ("phase_number",)
    assert phases.scope_path_keys == ()
    assert phases.observatory_ready is True
    assert phases.production_ready is False

    progression = registry.route("guild_phase_progression_api")
    assert progression.route_template == "/api/guilds/phase-progression"
    assert progression.method == "GET"
    assert progression.status == "reviewed"
    assert progression.review_state == "verified"
    assert progression.auth_mode == "browser_context_observed"
    assert progression.empty_params_observed is False
    assert progression.parameter_keys == ("phase", "board", "difficulty")
    assert progression.dimension_keys == (
        "phase",
        "board",
        "bossId",
        "difficulty",
        "location",
    )
    assert progression.schema_profile_keys == ()
    assert progression.scope_path_keys == ()
    assert progression.observatory_ready is True
    assert progression.production_ready is False


def test_alternate_rankings_contract_remains_reviewed_not_production_ready() -> None:
    registry = load_source_registry(registry_path())
    route = registry.route("guild_progression_rankings_api")

    assert route.route_template == "/api/guilds/progression/rankings"
    assert route.method == "GET"
    assert route.status == "reviewed"
    assert route.empty_params_observed is True
    assert route.scope_path_keys == ()
    assert route.observatory_ready is True
    assert route.production_ready is False


def test_reviewed_public_report_api_is_observatory_ready_without_dimensions() -> None:
    registry = load_source_registry(registry_path())
    route = registry.route("reports_public_api")

    assert route.route_template == "/api/reports/public"
    assert route.method == "GET"
    assert route.auth_mode == "public_observed"
    assert route.status == "reviewed"
    assert route.review_state == "verified"
    assert route.parameter_keys == ("page", "limit", "sortBy", "sortOrder")
    assert route.dimension_keys == ()
    assert route.scope_path_keys == ()
    assert route.empty_params_observed is False
    assert route.observatory_ready is True
    assert route.production_ready is False


def test_reports_filter_catalog_is_observatory_ready_with_low_cardinality_dimensions() -> None:
    registry = load_source_registry(registry_path())
    route = registry.route("reports_public_filter_options_api")

    assert route.route_template == "/api/reports/public/filter-options"
    assert route.method == "GET"
    assert route.auth_mode == "browser_context_observed"
    assert route.status == "reviewed"
    assert route.review_state == "verified"
    assert route.parameter_keys == ()
    assert route.dimension_keys == ("phase_number", "location")
    assert route.scope_path_keys == ()
    assert route.empty_params_observed is True
    assert route.observatory_ready is True
    assert route.production_ready is False


def test_reports_queue_status_is_reviewed_operational_health_without_dimensions() -> None:
    registry = load_source_registry(registry_path())
    route = registry.route("reports_queue_status_api")

    assert route.route_template == "/api/reports/queue-status"
    assert route.method == "GET"
    assert route.auth_mode == "browser_context_observed"
    assert route.status == "reviewed"
    assert route.review_state == "verified"
    assert route.use == "reports_collection_operational_health"
    assert route.parameter_keys == ()
    assert route.dimension_keys == ()
    assert route.scope_path_keys == ()
    assert route.empty_params_observed is True
    assert route.observatory_ready is True
    assert route.production_ready is False


def test_current_report_runtime_routes_are_capture_ready_and_report_scoped() -> None:
    registry = load_source_registry(registry_path())
    expected = {
        "report_detail_api": (
            "/api/reports/{reportId}",
            (),
            (),
            True,
        ),
        "report_encounters_api": (
            "/api/reports/{reportId}/encounters",
            ("includeTrash",),
            (),
            False,
        ),
        "report_combatants_roster_api": (
            "/api/reports/{reportId}/combatants-roster",
            ("encounterIds",),
            (),
            False,
        ),
        "report_encounter_throughput_timeline_api": (
            "/api/reports/{reportId}/encounters/{encounterId}/throughput-timeline",
            ("bucket_size_ms", "metric", "perspective"),
            ("metric", "perspective"),
            False,
        ),
        "report_character_damage_taken_abilities_api": (
            "/api/reports/{reportId}/character_damage_taken_abilities",
            ("encounterIds[]", "format", "limit", "participantType", "scope"),
            (),
            False,
        ),
        "report_character_spell_healing_api": (
            "/api/reports/{reportId}/character_spell_healing",
            ("encounterIds[]", "format", "limit", "participantType", "scope"),
            (),
            False,
        ),
    }

    for endpoint_code, values in expected.items():
        route_template, parameter_keys, schema_profile_keys, empty_params_observed = values
        route = registry.route(endpoint_code)
        assert route.route_template == route_template
        assert route.method == "GET"
        assert route.auth_mode == "browser_context_observed"
        assert route.status == "reviewed"
        assert route.review_state == "verified"
        assert route.parameter_keys == parameter_keys
        assert route.schema_profile_keys == schema_profile_keys
        assert route.dimension_keys == ()
        assert route.scope_path_keys == ("reportId",)
        assert route.empty_params_observed is empty_params_observed
        assert route.observatory_ready is True
        assert route.production_ready is False


def test_historical_report_slice_routes_are_capture_ready_but_not_production_ready() -> None:
    registry = load_source_registry(registry_path())
    expected = {
        "report_encounter_detail_api": "/api/reports/{reportId}/encounters/{encounterId}",
        "report_encounter_combatants_info_api": (
            "/api/reports/{reportId}/encounters/{encounterId}/combatants-info"
        ),
    }

    for endpoint_code, route_template in expected.items():
        route = registry.route(endpoint_code)
        assert route.route_template == route_template
        assert route.method == "GET"
        assert route.auth_mode == "historical_public_observed"
        assert route.status == "reviewed"
        assert route.review_state == "verified"
        assert route.parameter_keys == ()
        assert route.dimension_keys == ()
        assert route.schema_profile_keys == ()
        assert route.scope_path_keys == ("reportId",)
        assert route.empty_params_observed is True
        assert route.observatory_ready is True
        assert route.production_ready is False


def test_registry_rejects_schema_profile_keys_outside_reviewed_query_contract(tmp_path: Path) -> None:
    path = tmp_path / "registry.yaml"
    path.write_text(
        """
schema_version: 1
source_code: test
base_url: https://example.invalid
status: discovery
truth_role: test
routes:
  - endpoint_code: bad
    route_template: /api/x
    method: GET
    auth_mode: public
    status: reviewed
    use: test
    parameter_keys: [metric]
    schema_profile_keys: [perspective]
    review_state: verified
""".lstrip(),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="schema_profile_keys"):
        load_source_registry(path)


def test_registry_rejects_scope_keys_outside_route_path_contract(tmp_path: Path) -> None:
    path = tmp_path / "registry.yaml"
    path.write_text(
        """
schema_version: 1
source_code: test
base_url: https://example.invalid
status: discovery
truth_role: test
routes:
  - endpoint_code: bad
    route_template: /api/reports/{reportId}
    method: GET
    auth_mode: public
    status: reviewed
    use: test
    scope_path_keys: [encounterId]
    review_state: verified
""".lstrip(),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="scope_path_keys"):
        load_source_registry(path)


def test_unverified_aura_route_cannot_be_used_for_production() -> None:
    registry = load_source_registry(registry_path())
    with pytest.raises(UnverifiedSourceRouteError, match="not production-ready"):
        registry.route("aura_timeline", require_production=True)
