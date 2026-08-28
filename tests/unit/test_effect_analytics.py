from pathlib import Path

from fastapi.testclient import TestClient

from coa_workbench.web import create_app
from coa_workbench.web.effects import EFFECTS, EFFECT_CODES_BY_PAIR, analyze_composition


def client(tmp_path: Path) -> TestClient:
    return TestClient(create_app(tmp_path / "coa.duckdb", Path("migrations")))


def test_legacy_effect_catalog_contains_45_effects_and_all_class_specs() -> None:
    assert len(EFFECTS) == 45
    assert len(EFFECT_CODES_BY_PAIR) == 70
    assert all(EFFECT_CODES_BY_PAIR.values())
    assert {effect.priority for effect in EFFECTS} == {
        "Критично",
        "Важно",
        "Опционально",
    }


def test_effect_catalog_endpoint_exposes_migration_metadata(tmp_path: Path) -> None:
    response = client(tmp_path).get("/api/catalog/effects")
    assert response.status_code == 200
    payload = response.json()
    assert payload["effect_count"] == 45
    assert payload["provider_link_count"] > 45
    assert sum(payload["categories"].values()) == 45
    assert sum(payload["priorities"].values()) == 45


def test_legacy_empty_composition_remains_available_for_forensics() -> None:
    result = analyze_composition([], top_n=3)
    coverage = result["coverage"]
    assert coverage["total_effects"] == 45
    assert coverage["covered_effects"] == 0
    assert coverage["missing_effects"] == 45
    assert coverage["coverage_percent"] == 0.0
    assert len(result["recommendations"]) == 3


def test_legacy_felsworn_tyrant_fixture_is_not_deleted() -> None:
    result = analyze_composition(
        [
            {
                "slot_no": 1,
                "active": True,
                "player_name": "Tank",
                "class_code": "felsworn",
                "spec_code": "tyrant",
            }
        ],
        top_n=3,
    )
    covered_names = {effect["name"] for effect in result["coverage"]["covered"]}
    assert "Defensive Cooldown (Raid-Wide)" in covered_names
    assert "3% Damage Done (all)" in covered_names
    assert "Attack Speed Slow" in covered_names


def test_preview_disables_legacy_scoring_by_default(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("COA_ENABLE_LEGACY_EFFECTS", raising=False)
    response = client(tmp_path).post(
        "/api/plans/preview",
        json={
            "raid_format": "10",
            "slots": [
                {
                    "slot_no": 1,
                    "player_name": "Tank",
                    "class_code": "felsworn",
                    "spec_code": "tyrant",
                }
            ],
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["coverage"]["availability"] == "unavailable"
    assert payload["coverage"]["data_trust_status"] == "legacy_unverified"
    assert payload["coverage"]["total_effects"] == 0
    assert payload["recommendations"] == []
    assert payload["scoring"]["canonical"] is False
    assert payload["scoring"]["algorithm"] == "disabled-unverified-data"


def test_preview_can_enable_legacy_forensic_comparison(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("COA_ENABLE_LEGACY_EFFECTS", "1")
    response = client(tmp_path).post(
        "/api/plans/preview",
        json={
            "raid_format": "10",
            "slots": [
                {
                    "slot_no": 1,
                    "player_name": "Tank",
                    "class_code": "felsworn",
                    "spec_code": "tyrant",
                }
            ],
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["coverage"]["availability"] == "forensic_only"
    assert payload["coverage"]["data_trust_status"] == "legacy_unverified"
    assert payload["coverage"]["covered_effects"] > 0
    assert len(payload["recommendations"]) == 3
    assert payload["scoring"]["canonical"] is False
