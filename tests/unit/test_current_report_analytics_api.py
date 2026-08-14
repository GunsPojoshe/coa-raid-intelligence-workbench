from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

import coa_workbench.web.current_report_analytics_api as api_module
from coa_workbench.web.current_report_analytics_api import install_current_report_analytics_routes


def _catalog() -> dict[str, object]:
    return {
        "read_model_version": "current-report-comparison-read-model-v1",
        "report_count": 1,
        "reports": [
            {
                "report_id": "canonical-report",
                "source_report_id": "source-report",
                "title": "Example report",
                "zone": "Example zone",
                "start_time": "2026-08-14T12:00:00Z",
                "analytics_artifact_key": "artifact",
                "analytics_observed_at": "2026-08-14T12:01:00",
                "encounter_count": 1,
                "roster_character_count": 2,
                "entity_counts": {
                    "current_throughput_request_observation": 1,
                },
            }
        ],
        "local_private_payload": True,
        "public_release_safe": False,
        "planner_scoring_allowed": False,
    }


def _detail() -> dict[str, object]:
    return {
        "read_model_version": "current-report-comparison-read-model-v1",
        "report": {
            "report_id": "canonical-report",
            "source_report_id": "source-report",
            "title": "Example report",
        },
        "analytics_artifact_key": "artifact",
        "analytics_observed_at": "2026-08-14T12:01:00",
        "encounter_count": 1,
        "roster_character_count": 2,
        "players": [
            {
                "source_character_id": "101",
                "name": "A",
                "class": "Example",
                "role": "damage",
                "specs": ["Example"],
                "snapshot_count": 1,
                "throughput_character_observation_count": 1,
                "damage_taken_ability_exact_key_match_count": 2,
                "healing_spell_observation_count": 0,
                "healing_source_breakdown_observation_count": 0,
                "healing_target_breakdown_observation_count": 0,
            }
        ],
        "throughput_profiles": [
            {
                "source_encounter_id": "1",
                "encounter_name": "Boss",
                "request_index": 0,
                "metric": "damage",
                "perspective": "source",
                "player_count": 1,
                "ranking_basis": "upstream_characters_total_amount_desc",
                "planner_scoring_allowed": False,
                "rows": [
                    {
                        "rank": 1,
                        "source_character_id": "101",
                        "name": "A",
                        "class": "Example",
                        "role": "damage",
                        "total_amount": 100,
                    }
                ],
            }
        ],
        "summary": {
            "request_count": 1,
            "profile_count": 1,
            "matched_ranked_character_rows": 1,
            "unmatched_character_rows": 0,
            "missing_total_rows": 0,
            "throughput_point_count": 1,
            "throughput_point_exact_character_link_count": 1,
            "throughput_point_opaque_group_count": 0,
            "damage_taken_ability_row_count": 2,
            "healing_spell_row_count": 0,
            "healing_source_breakdown_row_count": 0,
            "healing_target_breakdown_row_count": 0,
            "throughput_unmatched_character_row_count": 0,
            "damage_taken_exact_roster_key_match_row_count": 2,
            "damage_taken_exact_roster_key_match_character_count": 1,
            "healing_spell_explicit_roster_match_row_count": 0,
            "healing_source_explicit_roster_match_row_count": 0,
            "healing_target_explicit_roster_match_row_count": 0,
        },
        "interpretation": {
            "throughput_rank_is_observed_total_only": True,
            "damage_group_key_target_semantics_verified": False,
            "damage_player_link_basis": "exact_source_group_key_equals_roster_character_id",
            "healing_player_link_basis": "explicit_character_id_fields",
            "mechanic_semantics_verified": False,
            "planner_scoring_allowed": False,
        },
        "local_private_payload": True,
        "public_release_safe": False,
    }


def _client(monkeypatch) -> TestClient:
    monkeypatch.setattr(
        api_module,
        "list_current_report_comparison_reports",
        lambda *_args, **_kwargs: _catalog(),
    )
    monkeypatch.setattr(
        api_module,
        "build_current_report_comparison_read_model",
        lambda *_args, **_kwargs: _detail(),
    )
    app = FastAPI()
    install_current_report_analytics_routes(
        app,
        database_path=Path("example.duckdb"),
        migrations_dir=Path("migrations"),
    )
    return TestClient(app)


def test_current_report_analytics_routes_are_typed_and_private(monkeypatch) -> None:
    client = _client(monkeypatch)

    catalog = client.get("/api/current-report-analytics/reports")
    assert catalog.status_code == 200
    assert catalog.json()["report_count"] == 1
    assert catalog.json()["public_release_safe"] is False

    latest = client.get("/api/current-report-analytics/latest")
    assert latest.status_code == 200
    payload = latest.json()
    assert payload["throughput_profiles"][0]["rows"][0]["class"] == "Example"
    assert payload["throughput_profiles"][0]["rows"][0]["rank"] == 1
    assert payload["interpretation"]["planner_scoring_allowed"] is False

    report = client.get("/api/current-report-analytics/reports/canonical-report")
    assert report.status_code == 200
    assert report.json()["report"]["report_id"] == "canonical-report"


def test_current_report_analytics_report_returns_404_when_missing(monkeypatch) -> None:
    monkeypatch.setattr(
        api_module,
        "list_current_report_comparison_reports",
        lambda *_args, **_kwargs: _catalog(),
    )

    def missing(*_args, **_kwargs):
        raise KeyError("missing")

    monkeypatch.setattr(api_module, "build_current_report_comparison_read_model", missing)
    app = FastAPI()
    install_current_report_analytics_routes(
        app,
        database_path=Path("example.duckdb"),
        migrations_dir=Path("migrations"),
    )
    client = TestClient(app)

    response = client.get("/api/current-report-analytics/reports/missing")
    assert response.status_code == 404
    assert response.json()["detail"] == "Report analytics not found"


def test_current_report_analytics_boundary_rejects_planner_scoring(monkeypatch) -> None:
    unsafe = _detail()
    unsafe["planner_scoring_allowed"] = True
    monkeypatch.setattr(
        api_module,
        "build_current_report_comparison_read_model",
        lambda *_args, **_kwargs: unsafe,
    )
    app = FastAPI()
    install_current_report_analytics_routes(
        app,
        database_path=Path("example.duckdb"),
        migrations_dir=Path("migrations"),
    )
    client = TestClient(app)

    response = client.get("/api/current-report-analytics/latest")
    assert response.status_code == 500
    assert response.json()["detail"] == "Current report analytics are unavailable"
