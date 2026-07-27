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
    assert registry.schema_version == 2
    assert registry.source_code == "coa_ascension_logs"
    assert registry.base_url == "https://coa.ascensionlogs.gg"
    assert registry.truth_role == "primary_observation_source"
    assert len(registry.routes) == 8
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


def test_unverified_aura_route_cannot_be_used_for_production() -> None:
    registry = load_source_registry(registry_path())
    with pytest.raises(UnverifiedSourceRouteError, match="not production-ready"):
        registry.route("aura_timeline", require_production=True)
