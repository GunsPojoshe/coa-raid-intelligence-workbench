from __future__ import annotations

import pytest

from coa_workbench.analytics.current_report_review import build_public_comparison_review


def _model() -> dict[str, object]:
    return {
        "read_model_version": "current-report-comparison-read-model-v1",
        "local_private_payload": True,
        "public_release_safe": False,
        "encounter_count": 1,
        "roster_character_count": 2,
        "players": [
            {
                "source_character_id": "101",
                "name": "Alpha",
                "damage_taken_ability_exact_key_match_count": 2,
                "healing_spell_observation_count": 1,
                "healing_source_breakdown_observation_count": 3,
                "healing_target_breakdown_observation_count": 4,
            },
            {
                "source_character_id": "102",
                "name": "Beta",
                "damage_taken_ability_exact_key_match_count": 0,
                "healing_spell_observation_count": 2,
                "healing_source_breakdown_observation_count": 0,
                "healing_target_breakdown_observation_count": 1,
            },
        ],
        "throughput_profiles": [
            {
                "ranking_basis": "upstream_characters_total_amount_desc",
                "planner_scoring_allowed": False,
                "rows": [
                    {"rank": 1, "source_character_id": "101", "total_amount": 100},
                    {"rank": 2, "source_character_id": "102", "total_amount": 50},
                ],
            }
        ],
        "summary": {
            "request_count": 1,
            "matched_ranked_character_rows": 2,
            "unmatched_character_rows": 0,
            "missing_total_rows": 0,
            "throughput_point_count": 3,
            "throughput_point_exact_character_link_count": 2,
            "throughput_point_opaque_group_count": 1,
            "damage_taken_ability_row_count": 2,
            "damage_taken_exact_roster_key_match_row_count": 2,
            "damage_taken_exact_roster_key_match_character_count": 1,
            "healing_spell_row_count": 3,
            "healing_spell_explicit_roster_match_row_count": 3,
            "healing_source_breakdown_row_count": 3,
            "healing_source_explicit_roster_match_row_count": 3,
            "healing_target_breakdown_row_count": 5,
            "healing_target_explicit_roster_match_row_count": 5,
        },
        "interpretation": {
            "damage_group_key_target_semantics_verified": False,
            "mechanic_semantics_verified": False,
            "planner_scoring_allowed": False,
        },
    }


def _catalog() -> dict[str, object]:
    return {
        "read_model_version": "current-report-comparison-read-model-v1",
        "report_count": 1,
        "planner_scoring_allowed": False,
    }


def test_public_comparison_review_emits_only_counts_and_safe_flags() -> None:
    result = build_public_comparison_review(
        _model(),
        _catalog(),
        deterministic_requery_equal=True,
    )

    assert result["status"] == "completed"
    assert result["roster_character_count"] == 2
    assert result["throughput_ranked_player_row_count"] == 2
    assert result["damage_taken_exact_roster_key_match_row_count"] == 2
    assert result["healing_target_explicit_roster_match_row_count"] == 5
    assert result["verification"] == {
        "deterministic_requery_equal": True,
        "throughput_rankings_sorted_by_observed_total": True,
        "all_ranked_players_in_roster": True,
        "damage_join_is_exact_key_only": True,
        "damage_group_key_target_semantics_verified": False,
        "healing_join_uses_explicit_character_ids": True,
        "mechanic_semantics_verified": False,
        "planner_scoring_allowed": False,
    }
    assert all(value is False for value in result["privacy"].values())
    rendered = str(result)
    assert "Alpha" not in rendered
    assert "Beta" not in rendered
    assert "101" not in rendered
    assert "102" not in rendered


def test_public_comparison_review_fails_closed_on_rank_order_mismatch() -> None:
    model = _model()
    model["throughput_profiles"][0]["rows"] = [
        {"rank": 1, "source_character_id": "102", "total_amount": 50},
        {"rank": 2, "source_character_id": "101", "total_amount": 100},
    ]

    result = build_public_comparison_review(
        model,
        _catalog(),
        deterministic_requery_equal=True,
    )
    assert result["verification"]["throughput_rankings_sorted_by_observed_total"] is False


def test_public_comparison_review_rejects_promoted_planner_scoring() -> None:
    model = _model()
    model["interpretation"]["planner_scoring_allowed"] = True

    with pytest.raises(ValueError, match="planner scoring"):
        build_public_comparison_review(
            model,
            _catalog(),
            deterministic_requery_equal=True,
        )
