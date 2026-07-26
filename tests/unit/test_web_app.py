from fastapi.testclient import TestClient

from coa_workbench.web import create_app

client = TestClient(create_app())


def test_health_identifies_localhost_mode() -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["mode"] == "localhost"


def test_formats_expose_all_supported_sizes() -> None:
    payload = client.get("/api/formats").json()
    assert payload["formats"] == ["FLEX", "10", "25", "40"]
    assert payload["max_slots"] == 40


def test_preview_activates_exactly_25_slots() -> None:
    response = client.post("/api/plans/preview", json={"raid_format": "25", "target_size": 25})
    assert response.status_code == 200
    payload = response.json()
    assert payload["target_size"] == 25
    assert sum(slot["active"] for slot in payload["slots"]) == 25
    assert payload["remaining_slots"] == 25


def test_flex_requires_target_size() -> None:
    response = client.post("/api/plans/preview", json={"raid_format": "FLEX"})
    assert response.status_code == 422


def test_duplicate_player_is_rejected() -> None:
    response = client.post(
        "/api/plans/preview",
        json={
            "raid_format": "10",
            "slots": [
                {"slot_no": 1, "player_name": "Alice"},
                {"slot_no": 2, "player_name": "alice"},
            ],
        },
    )
    assert response.status_code == 422


def test_preview_counts_roles_and_filled_slots() -> None:
    response = client.post(
        "/api/plans/preview",
        json={
            "raid_format": "10",
            "slots": [
                {"slot_no": 1, "player_name": "Tank", "class_code": "A", "spec_code": "B", "role": "Танк"},
                {"slot_no": 2, "player_name": "Heal", "class_code": "C", "spec_code": "D", "role": "Хил"},
            ],
        },
    )
    payload = response.json()
    assert payload["filled_slots"] == 2
    assert payload["remaining_slots"] == 8
    assert payload["role_counts"] == {"Танк": 1, "Хил": 1}
