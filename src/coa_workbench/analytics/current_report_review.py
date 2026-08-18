from __future__ import annotations

from typing import Any, Mapping

from coa_workbench.analytics.current_report_read_model import (
    CURRENT_REPORT_COMPARISON_READ_MODEL_VERSION,
)

CURRENT_REPORT_COMPARISON_REVIEW_VERSION = "current-report-comparison-review-v1"


def _list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"{label} must be an array")
    return value


def _mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    return value


def _int(value: Any, label: str) -> int:
    if isinstance(value, bool):
        raise ValueError(f"{label} must be an integer")
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be an integer") from exc


def _float(value: Any, label: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{label} must be numeric")
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be numeric") from exc


def build_public_comparison_review(
    model: Mapping[str, Any],
    catalog: Mapping[str, Any],
    *,
    deterministic_requery_equal: bool,
) -> dict[str, Any]:
    """Return a scalar-safe receipt for a local/private current-report comparison model."""
    if model.get("read_model_version") != CURRENT_REPORT_COMPARISON_READ_MODEL_VERSION:
        raise ValueError("unexpected current-report comparison read-model version")
    if catalog.get("read_model_version") != CURRENT_REPORT_COMPARISON_READ_MODEL_VERSION:
        raise ValueError("unexpected current-report comparison catalog version")
    if model.get("local_private_payload") is not True:
        raise ValueError("comparison model must be explicitly marked local/private")
    if model.get("public_release_safe") is not False:
        raise ValueError("comparison model must not claim public-release safety")
    if model.get("interpretation", {}).get("planner_scoring_allowed") is not False:
        raise ValueError("comparison model unexpectedly allows planner scoring")
    if catalog.get("planner_scoring_allowed") is not False:
        raise ValueError("comparison catalog unexpectedly allows planner scoring")

    players = _list(model.get("players"), "players")
    profiles = _list(model.get("throughput_profiles"), "throughput_profiles")
    summary = _mapping(model.get("summary"), "summary")

    player_ids: set[str] = set()
    for row in players:
        player = _mapping(row, "players[]")
        source_character_id = str(player.get("source_character_id") or "")
        if not source_character_id:
            raise ValueError("players[] has no source_character_id")
        if source_character_id in player_ids:
            raise ValueError("comparison model contains duplicate roster character IDs")
        player_ids.add(source_character_id)

    ranked_rows = 0
    rankings_valid = True
    all_ranked_players_in_roster = True
    for raw_profile in profiles:
        profile = _mapping(raw_profile, "throughput_profiles[]")
        rows = _list(profile.get("rows"), "throughput_profiles[].rows")
        if profile.get("ranking_basis") != "upstream_characters_total_amount_desc":
            raise ValueError("unexpected throughput ranking basis")
        if profile.get("planner_scoring_allowed") is not False:
            raise ValueError("throughput profile unexpectedly allows planner scoring")
        previous_total: float | None = None
        previous_rank = 0
        for position, raw_row in enumerate(rows, start=1):
            row = _mapping(raw_row, "throughput_profiles[].rows[]")
            character_id = str(row.get("source_character_id") or "")
            if not character_id or character_id not in player_ids:
                all_ranked_players_in_roster = False
            total = _float(row.get("total_amount"), "throughput total_amount")
            rank = _int(row.get("rank"), "throughput rank")
            if previous_total is not None and total > previous_total:
                rankings_valid = False
            if rank < previous_rank or rank > position:
                rankings_valid = False
            previous_total = total
            previous_rank = rank
            ranked_rows += 1

    aggregate_player_counts = {
        "damage_taken_exact_roster_key_match_row_count": sum(
            _int(
                _mapping(row, "players[]").get("damage_taken_ability_exact_key_match_count", 0),
                "damage_taken_ability_exact_key_match_count",
            )
            for row in players
        ),
        "healing_spell_explicit_roster_match_row_count": sum(
            _int(
                _mapping(row, "players[]").get("healing_spell_observation_count", 0),
                "healing_spell_observation_count",
            )
            for row in players
        ),
        "healing_source_explicit_roster_match_row_count": sum(
            _int(
                _mapping(row, "players[]").get(
                    "healing_source_breakdown_observation_count", 0
                ),
                "healing_source_breakdown_observation_count",
            )
            for row in players
        ),
        "healing_target_explicit_roster_match_row_count": sum(
            _int(
                _mapping(row, "players[]").get(
                    "healing_target_breakdown_observation_count", 0
                ),
                "healing_target_breakdown_observation_count",
            )
            for row in players
        ),
    }
    for key, expected in aggregate_player_counts.items():
        if _int(summary.get(key), f"summary.{key}") != expected:
            raise ValueError(f"player-count aggregation disagrees with summary.{key}")

    matched_ranked = _int(
        summary.get("matched_ranked_character_rows"),
        "summary.matched_ranked_character_rows",
    )
    if ranked_rows != matched_ranked:
        raise ValueError("throughput ranked row count disagrees with summary")
    if len(players) != _int(model.get("roster_character_count"), "roster_character_count"):
        raise ValueError("player list count disagrees with roster_character_count")

    interpretation = _mapping(model.get("interpretation"), "interpretation")
    if interpretation.get("damage_group_key_target_semantics_verified") is not False:
        raise ValueError("damage dynamic-group target semantics were unexpectedly promoted")
    if interpretation.get("mechanic_semantics_verified") is not False:
        raise ValueError("mechanic semantics were unexpectedly promoted")

    return {
        "schema_version": 1,
        "review_version": CURRENT_REPORT_COMPARISON_REVIEW_VERSION,
        "read_model_version": CURRENT_REPORT_COMPARISON_READ_MODEL_VERSION,
        "status": "completed",
        "catalog_report_count": _int(catalog.get("report_count"), "catalog.report_count"),
        "encounter_count": _int(model.get("encounter_count"), "encounter_count"),
        "roster_character_count": _int(
            model.get("roster_character_count"),
            "roster_character_count",
        ),
        "throughput_profile_count": len(profiles),
        "throughput_request_count": _int(
            summary.get("request_count"),
            "summary.request_count",
        ),
        "throughput_ranked_player_row_count": ranked_rows,
        "throughput_unmatched_character_row_count": _int(
            summary.get("unmatched_character_rows"),
            "summary.unmatched_character_rows",
        ),
        "throughput_missing_total_row_count": _int(
            summary.get("missing_total_rows"),
            "summary.missing_total_rows",
        ),
        "throughput_point_count": _int(
            summary.get("throughput_point_count"),
            "summary.throughput_point_count",
        ),
        "throughput_point_exact_character_link_count": _int(
            summary.get("throughput_point_exact_character_link_count"),
            "summary.throughput_point_exact_character_link_count",
        ),
        "throughput_point_opaque_group_count": _int(
            summary.get("throughput_point_opaque_group_count"),
            "summary.throughput_point_opaque_group_count",
        ),
        "damage_taken_ability_row_count": _int(
            summary.get("damage_taken_ability_row_count"),
            "summary.damage_taken_ability_row_count",
        ),
        "damage_taken_exact_roster_key_match_row_count": aggregate_player_counts[
            "damage_taken_exact_roster_key_match_row_count"
        ],
        "damage_taken_exact_roster_key_match_character_count": _int(
            summary.get("damage_taken_exact_roster_key_match_character_count"),
            "summary.damage_taken_exact_roster_key_match_character_count",
        ),
        "healing_spell_row_count": _int(
            summary.get("healing_spell_row_count"),
            "summary.healing_spell_row_count",
        ),
        "healing_spell_explicit_roster_match_row_count": aggregate_player_counts[
            "healing_spell_explicit_roster_match_row_count"
        ],
        "healing_source_breakdown_row_count": _int(
            summary.get("healing_source_breakdown_row_count"),
            "summary.healing_source_breakdown_row_count",
        ),
        "healing_source_explicit_roster_match_row_count": aggregate_player_counts[
            "healing_source_explicit_roster_match_row_count"
        ],
        "healing_target_breakdown_row_count": _int(
            summary.get("healing_target_breakdown_row_count"),
            "summary.healing_target_breakdown_row_count",
        ),
        "healing_target_explicit_roster_match_row_count": aggregate_player_counts[
            "healing_target_explicit_roster_match_row_count"
        ],
        "verification": {
            "deterministic_requery_equal": bool(deterministic_requery_equal),
            "throughput_rankings_sorted_by_observed_total": rankings_valid,
            "all_ranked_players_in_roster": all_ranked_players_in_roster,
            "damage_join_is_exact_key_only": True,
            "damage_group_key_target_semantics_verified": False,
            "healing_join_uses_explicit_character_ids": True,
            "mechanic_semantics_verified": False,
            "planner_scoring_allowed": False,
        },
        "privacy": {
            "local_private_model_included": False,
            "report_ids_included": False,
            "encounter_ids_included": False,
            "character_ids_included": False,
            "character_names_included": False,
            "dynamic_group_keys_included": False,
            "source_capture_ids_included": False,
            "source_scope_values_included": False,
            "source_scope_fingerprints_included": False,
            "input_output_fingerprints_included": False,
        },
    }


__all__ = [
    "CURRENT_REPORT_COMPARISON_REVIEW_VERSION",
    "build_public_comparison_review",
]
