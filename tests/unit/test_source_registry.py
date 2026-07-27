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
    assert registry.source_code == "coa_ascension_logs"
    assert registry.base_url == "https://coa.ascensionlogs.gg"
    assert registry.truth_role == "primary_observation_source"
    assert len(registry.routes) == 5
    assert registry.prohibited_assumptions


def test_public_home_is_available_only_as_probe() -> None:
    registry = load_source_registry(registry_path())
    route = registry.route("public_home")
    assert route.route_template == "/"
    assert route.status == "verified_html"
    assert route.production_ready is False


def test_unverified_aura_route_cannot_be_used_for_production() -> None:
    registry = load_source_registry(registry_path())
    with pytest.raises(UnverifiedSourceRouteError, match="not production-ready"):
        registry.route("aura_timeline", require_production=True)
