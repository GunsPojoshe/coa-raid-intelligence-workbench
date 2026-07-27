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


def test_invalid_plan_is_not_persisted(tmp_path: Path) -> None:
    api = client(tmp_path)
    response = api.post(
        "/api/plans",
        json={
            "plan_name": "Некорректный план",
            "raid_format": "10",
            "slots": [
                {
                    "slot_no": 1,
                    "player_name": "Player without class",
                }
            ],
        },
    )
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert detail["message"] == "План не сохранён: исправьте ошибки проверки"
    assert detail["validation_errors"] == [
        "Slot 1: class and spec are required for a filled slot"
    ]
    assert api.get("/api/plans").json()["plans"] == []


def test_plan_round_trip_update_without_duplicate_and_delete(tmp_path: Path) -> None:
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
    assert saved.headers["x-request-id"]
    assert saved.json()["action"] == "created"
    plan_id = saved.json()["plan_id"]

    updated = api.post(
        "/api/plans",
        json={
            "plan_id": plan_id,
            "plan_name": "Регрессия 10 — обновлено",
            "raid_format": "10",
            "boss_id": "Boss X",
            "slots": [
                {
                    "slot_no": 1,
                    "player_name": "Tank-Updated",
                    "class_code": "felsworn",
                    "spec_code": "tyrant",
                    "locked": True,
                }
            ],
        },
    )
    assert updated.status_code == 200
    assert updated.json() == {
        "plan_id": plan_id,
        "status": "saved",
        "action": "updated",
    }

    plans = api.get("/api/plans").json()["plans"]
    assert len(plans) == 1
    assert plans[0]["plan_id"] == plan_id
    assert plans[0]["plan_name"] == "Регрессия 10 — обновлено"

    loaded = api.get(f"/api/plans/{plan_id}")
    assert loaded.status_code == 200
    payload = loaded.json()
    assert payload["plan_name"] == "Регрессия 10 — обновлено"
    assert payload["boss_id"] == "Boss X"
    assert payload["slots"][0]["player_name"] == "Tank-Updated"
    assert payload["slots"][0]["role"] == "Танк"
    assert payload["slots"][0]["locked"] is True

    assert api.delete(f"/api/plans/{plan_id}").status_code == 204
    assert api.get(f"/api/plans/{plan_id}").status_code == 404


def test_save_button_has_explicit_non_conflicting_binding(tmp_path: Path) -> None:
    html = client(tmp_path).get("/").text
    assert 'id="savePlanButton"' in html
    assert 'id="savePlan"' not in html
    assert "function persistCurrentPlan()" in html
    assert "getElementById('savePlanButton').addEventListener('click',persistCurrentPlan)" in html
    assert 'id="diagnostics"' in html
    assert "function summarizeForLog(url,data)" in html
    assert "data.action==='updated'" in html
    assert "classList.toggle('current'" in html
