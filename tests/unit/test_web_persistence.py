from pathlib import Path

from fastapi.testclient import TestClient

from coa_workbench.web import create_app


def client(tmp_path: Path) -> TestClient:
    return TestClient(create_app(tmp_path / "coa.duckdb", Path("migrations")))


def test_catalog_contains_legacy_70_pairs(tmp_path: Path) -> None:
    payload = client(tmp_path).get("/api/catalog/class-specs").json()
    assert payload["entry_count"] == 70
    assert payload["classes"]


def test_role_is_derived_from_class_and_spec(tmp_path: Path) -> None:
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
    assert response.json()["slots"][0]["role"] == "Танк"


def test_plan_round_trip_and_delete(tmp_path: Path) -> None:
    api = client(tmp_path)
    saved = api.post(
        "/api/plans",
        json={
            "plan_name": "Регрессия 10",
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
    assert saved.status_code == 200
    plan_id = saved.json()["plan_id"]
    loaded = api.get(f"/api/plans/{plan_id}")
    assert loaded.status_code == 200
    assert loaded.json()["plan_name"] == "Регрессия 10"
    assert loaded.json()["slots"][0]["role"] == "Танк"
    assert api.get("/api/plans").json()["plans"][0]["plan_id"] == plan_id
    assert api.delete(f"/api/plans/{plan_id}").status_code == 204
    assert api.get(f"/api/plans/{plan_id}").status_code == 404
