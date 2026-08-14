from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from coa_workbench.analytics.current_report_read_model import (
    CURRENT_REPORT_COMPARISON_READ_MODEL_VERSION,
    build_current_report_comparison_read_model,
    list_current_report_comparison_reports,
)


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class CurrentReportAnalyticsCatalogItem(_StrictModel):
    report_id: str
    source_report_id: str
    title: str | None = None
    zone: str | None = None
    start_time: str | None = None
    analytics_artifact_key: str
    analytics_observed_at: str
    encounter_count: int
    roster_character_count: int
    entity_counts: dict[str, int]


class CurrentReportAnalyticsCatalogResponse(_StrictModel):
    read_model_version: str
    report_count: int
    reports: list[CurrentReportAnalyticsCatalogItem]
    local_private_payload: bool
    public_release_safe: bool
    planner_scoring_allowed: bool


class CurrentReportAnalyticsPlayer(_StrictModel):
    source_character_id: str
    name: str | None = None
    class_name: str | None = Field(default=None, alias="class")
    role: str | None = None
    specs: Any = None
    snapshot_count: int | None = None
    throughput_character_observation_count: int
    damage_taken_ability_exact_key_match_count: int
    healing_spell_observation_count: int
    healing_source_breakdown_observation_count: int
    healing_target_breakdown_observation_count: int


class CurrentReportThroughputRankingRow(_StrictModel):
    rank: int
    source_character_id: str
    name: str | None = None
    class_name: str | None = Field(default=None, alias="class")
    role: str | None = None
    total_amount: int | float | str | None = None


class CurrentReportThroughputProfile(_StrictModel):
    source_encounter_id: str
    encounter_name: str | None = None
    request_index: int
    metric: str
    perspective: str | None = None
    player_count: int
    ranking_basis: str
    planner_scoring_allowed: bool
    rows: list[CurrentReportThroughputRankingRow]


class CurrentReportAnalyticsSummary(_StrictModel):
    request_count: int
    profile_count: int
    matched_ranked_character_rows: int
    unmatched_character_rows: int
    missing_total_rows: int
    throughput_point_count: int
    throughput_point_exact_character_link_count: int
    throughput_point_opaque_group_count: int
    damage_taken_ability_row_count: int
    healing_spell_row_count: int
    healing_source_breakdown_row_count: int
    healing_target_breakdown_row_count: int
    throughput_unmatched_character_row_count: int
    damage_taken_exact_roster_key_match_row_count: int
    damage_taken_exact_roster_key_match_character_count: int
    healing_spell_explicit_roster_match_row_count: int
    healing_source_explicit_roster_match_row_count: int
    healing_target_explicit_roster_match_row_count: int


class CurrentReportAnalyticsInterpretation(_StrictModel):
    throughput_rank_is_observed_total_only: bool
    damage_group_key_target_semantics_verified: bool
    damage_player_link_basis: str
    healing_player_link_basis: str
    mechanic_semantics_verified: bool
    planner_scoring_allowed: bool


class CurrentReportAnalyticsDetailResponse(_StrictModel):
    read_model_version: str
    report: dict[str, Any]
    analytics_artifact_key: str
    analytics_observed_at: str
    encounter_count: int
    roster_character_count: int
    players: list[CurrentReportAnalyticsPlayer]
    throughput_profiles: list[CurrentReportThroughputProfile]
    summary: CurrentReportAnalyticsSummary
    interpretation: CurrentReportAnalyticsInterpretation
    local_private_payload: bool
    public_release_safe: bool


def _validate_boundary(payload: dict[str, Any]) -> dict[str, Any]:
    if payload.get("read_model_version") != CURRENT_REPORT_COMPARISON_READ_MODEL_VERSION:
        raise ValueError("unexpected current-report comparison read-model version")
    if payload.get("local_private_payload") is not True:
        raise ValueError("current-report analytics API requires the local/private read model")
    if payload.get("public_release_safe") is not False:
        raise ValueError("current-report analytics API must remain explicitly private")
    if payload.get("planner_scoring_allowed") is True:
        raise ValueError("planner scoring is not allowed on the current-report comparison surface")
    interpretation = payload.get("interpretation")
    if isinstance(interpretation, dict):
        if interpretation.get("planner_scoring_allowed") is not False:
            raise ValueError("detail read model must keep planner scoring disabled")
        if interpretation.get("mechanic_semantics_verified") is not False:
            raise ValueError("detail read model must keep mechanic semantics unverified")
    return payload


def install_current_report_analytics_routes(
    app: FastAPI,
    *,
    database_path: Path,
    migrations_dir: Path,
) -> None:
    """Install typed localhost/private current-report analytics read routes."""

    @app.get(
        "/api/current-report-analytics/reports",
        response_model=CurrentReportAnalyticsCatalogResponse,
        tags=["current-report-analytics"],
    )
    def current_report_analytics_catalog() -> dict[str, Any]:
        try:
            payload = list_current_report_comparison_reports(database_path, migrations_dir)
            return _validate_boundary(payload)
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail="Current report analytics catalog is unavailable",
            ) from exc

    @app.get(
        "/api/current-report-analytics/latest",
        response_model=CurrentReportAnalyticsDetailResponse,
        tags=["current-report-analytics"],
    )
    def current_report_analytics_latest() -> dict[str, Any]:
        try:
            payload = build_current_report_comparison_read_model(
                database_path,
                migrations_dir,
            )
            return _validate_boundary(payload)
        except KeyError as exc:
            raise HTTPException(
                status_code=404,
                detail="Current report analytics are not available",
            ) from exc
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail="Current report analytics are unavailable",
            ) from exc

    @app.get(
        "/api/current-report-analytics/reports/{report_id}",
        response_model=CurrentReportAnalyticsDetailResponse,
        tags=["current-report-analytics"],
    )
    def current_report_analytics_report(report_id: str) -> dict[str, Any]:
        try:
            payload = build_current_report_comparison_read_model(
                database_path,
                migrations_dir,
                report_id=report_id,
            )
            return _validate_boundary(payload)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Report analytics not found") from exc
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail="Current report analytics are unavailable",
            ) from exc


__all__ = [
    "CurrentReportAnalyticsCatalogResponse",
    "CurrentReportAnalyticsDetailResponse",
    "install_current_report_analytics_routes",
]
