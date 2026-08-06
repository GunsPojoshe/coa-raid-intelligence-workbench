from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts" / "validate_armory_mappings.py"
SPEC = spec_from_file_location("validate_armory_mappings", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
_route_path = MODULE._route_path


def test_route_path_extracts_path_from_absolute_url():
    assert _route_path(
        "https://coa.ascensionlogs.gg/api/armory/character/156120"
    ) == "/api/armory/character/156120"


def test_route_path_preserves_relative_route_and_drops_query():
    assert _route_path(
        "/api/armory/talent-grid/felsworn?source=capture"
    ) == "/api/armory/talent-grid/felsworn"


def test_route_path_rejects_missing_or_non_string_values():
    assert _route_path(None) is None
    assert _route_path(156120) is None
    assert _route_path("") is None
