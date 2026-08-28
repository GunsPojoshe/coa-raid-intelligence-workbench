from __future__ import annotations

import json

import pytest

from coa_workbench.analytics.difficulty_context_binding import (
    build_difficulty_context_binding_review_from_inputs,
)


def _snapshot(
    *,
    pull_id: object,
    difficulty_index: int,
    difficulty_name: str,
    boss_name: str,
    map_id: int = 900001,
) -> dict[str, object]:
    return {
        "captured_at": "private-captured-at",
        "captured_for_boss": boss_name,
        "captured_for_pull_id": pull_id,
        "player": {},
        "guild": {},
        "instance": {
            "difficulty_index": difficulty_index,
            "difficulty_name": difficulty_name,
            "player_difficulty": difficulty_index,
            "instance_type": "raid",
            "is_dynamic": False,
            "map_id": map_id,
            "max_players": 25,
            "name": "Private Instance Name",
        },
        "specialization": {
            "resolved_ca_talent_ranks": [],
            "hero_build": {},
            "talents": {"trees": {}},
        },
        "gear": {},
    }


def _roster(*snapshots: dict[str, object]) -> dict[str, object]:
    return {
        "roster": [
            {
                "character_id": "private-character-id",
                "name": "Private Character Name",
                "snapshots": list(snapshots),
            }
        ]
    }


def _encounters(*rows: tuple[object, str, str]) -> dict[str, object]:
    return {
        "reportDifficulty": "Private Report Aggregate Difficulty",
        "encounters": [
            {"id": encounter_id, "name": name, "difficulty": difficulty}
            for encounter_id, name, difficulty in rows
        ],
    }


def test_pull_scoped_binding_handles_mixed_report_difficulties_without_leaking_values() -> None:
    reports = ("private-report-alpha", "private-report-beta")
    shared_boss = "Private Shared Boss"
    first_other_boss = "Private First Other Boss"
    second_other_boss = "Private Second Other Boss"
    shared_difficulty = "Private Shared Difficulty"
    first_other_difficulty = "Private First Other Difficulty"
    second_other_difficulty = "Private Second Other Difficulty"

    review = build_difficulty_context_binding_review_from_inputs(
        report_ids=reports,
        encounter_payloads={
            reports[0]: [
                _encounters(
                    (910001, shared_boss, shared_difficulty),
                    (910002, first_other_boss, first_other_difficulty),
                )
            ],
            reports[1]: [
                _encounters(
                    (920001, shared_boss, shared_difficulty),
                    (920002, second_other_boss, second_other_difficulty),
                )
            ],
        },
        roster_payloads={
            reports[0]: [
                _roster(
                    _snapshot(
                        pull_id=910001,
                        difficulty_index=41,
                        difficulty_name=shared_difficulty,
                        boss_name=shared_boss,
                    ),
                    _snapshot(
                        pull_id=910002,
                        difficulty_index=42,
                        difficulty_name=first_other_difficulty,
                        boss_name=first_other_boss,
                    ),
                )
            ],
            reports[1]: [
                _roster(
                    _snapshot(
                        pull_id=920001,
                        difficulty_index=41,
                        difficulty_name=shared_difficulty,
                        boss_name=shared_boss,
                    ),
                    _snapshot(
                        pull_id=920002,
                        difficulty_index=43,
                        difficulty_name=second_other_difficulty,
                        boss_name=second_other_boss,
                    ),
                )
            ],
        },
    )

    assert review["status"] == "cross_report_context_candidate_observed"
    assert review["client_context"]["pull_context_count"] == 4
    assert review["client_context"]["stable_difficulty_pair_pull_count"] == 4
    assert review["client_context"]["ambiguous_difficulty_pull_count"] == 0
    assert review["private_relation_candidates"]["typed_pull_id_exact_match_count"] == 4
    assert review["private_relation_candidates"]["id_linked_boss_name_match_count"] == 4
    assert review["private_relation_candidates"]["id_linked_difficulty_name_match_count"] == 4
    assert review["cross_report_context"]["shared_server_linked_encounter_context_count"] == 1
    assert review["cross_report_context"]["same_server_linked_client_difficulty_pair_count"] == 1
    assert review["cross_report_context"]["cross_report_difficulty_context_candidate_observed"] is True
    assert review["verification"]["final_cross_report_encounter_equivalence_verified"] is False
    assert review["verification"]["numeric_cross_report_scoring_allowed"] is False

    rendered = json.dumps(review, ensure_ascii=False, sort_keys=True)
    for private_value in (
        *reports,
        shared_boss,
        first_other_boss,
        second_other_boss,
        shared_difficulty,
        first_other_difficulty,
        second_other_difficulty,
        "Private Instance Name",
        "Private Character Name",
        "private-character-id",
        "private-captured-at",
    ):
        assert private_value not in rendered
    assert review["privacy"]["pull_ids_included"] is False
    assert review["privacy"]["private_hashes_included"] is False
    assert review["public_release_safe"] is True


def test_pull_id_type_difference_is_reported_as_text_only_candidate_not_verified_identity() -> None:
    reports = ("r-one", "r-two")
    boss = "Private Boss"
    difficulty = "Private Difficulty"
    review = build_difficulty_context_binding_review_from_inputs(
        report_ids=reports,
        encounter_payloads={
            report: [_encounters((700001, boss, difficulty))] for report in reports
        },
        roster_payloads={
            report: [
                _roster(
                    _snapshot(
                        pull_id="700001",
                        difficulty_index=9,
                        difficulty_name=difficulty,
                        boss_name=boss,
                    )
                )
            ]
            for report in reports
        },
    )

    assert review["status"] == "client_pull_context_observed"
    assert review["private_relation_candidates"]["typed_pull_id_exact_match_count"] == 0
    assert review["private_relation_candidates"]["text_only_pull_id_match_count"] == 2
    assert review["private_relation_candidates"]["pull_id_semantics_promoted"] is False
    assert review["verification"]["exact_pull_id_value_equality_observed"] is False
    assert review["cross_report_context"]["shared_server_linked_encounter_context_count"] == 0


def test_ambiguous_difficulty_inside_one_pull_fails_closed_for_that_context() -> None:
    reports = ("r-one", "r-two")
    boss = "Private Boss"
    difficulty = "Private Difficulty"
    review = build_difficulty_context_binding_review_from_inputs(
        report_ids=reports,
        encounter_payloads={
            "r-one": [_encounters((810001, boss, difficulty))],
            "r-two": [_encounters((820001, boss, difficulty))],
        },
        roster_payloads={
            "r-one": [
                _roster(
                    _snapshot(
                        pull_id=810001,
                        difficulty_index=11,
                        difficulty_name=difficulty,
                        boss_name=boss,
                    ),
                    _snapshot(
                        pull_id=810001,
                        difficulty_index=12,
                        difficulty_name=difficulty,
                        boss_name=boss,
                    ),
                )
            ],
            "r-two": [
                _roster(
                    _snapshot(
                        pull_id=820001,
                        difficulty_index=11,
                        difficulty_name=difficulty,
                        boss_name=boss,
                    )
                )
            ],
        },
    )

    assert review["client_context"]["pull_context_count"] == 2
    assert review["client_context"]["ambiguous_difficulty_pull_count"] == 1
    assert review["client_context"]["stable_difficulty_pair_pull_count"] == 1
    assert review["cross_report_context"]["cross_report_difficulty_context_candidate_observed"] is False
    assert review["verification"]["numeric_cross_report_scoring_allowed"] is False


def test_duplicate_roster_payload_does_not_multiply_pull_context_evidence() -> None:
    reports = ("r-one", "r-two")
    boss = "Private Boss"
    difficulty = "Private Difficulty"
    snapshot = _snapshot(
        pull_id=830001,
        difficulty_index=13,
        difficulty_name=difficulty,
        boss_name=boss,
    )
    duplicated = _roster(snapshot)
    review = build_difficulty_context_binding_review_from_inputs(
        report_ids=reports,
        encounter_payloads={
            "r-one": [_encounters((830001, boss, difficulty))],
            "r-two": [_encounters((840001, boss, difficulty))],
        },
        roster_payloads={
            "r-one": [duplicated, duplicated],
            "r-two": [
                _roster(
                    _snapshot(
                        pull_id=840001,
                        difficulty_index=13,
                        difficulty_name=difficulty,
                        boss_name=boss,
                    )
                )
            ],
        },
    )

    assert review["client_context"]["roster_snapshot_observation_count"] == 3
    assert review["client_context"]["duplicate_roster_snapshot_count"] == 1
    assert review["client_context"]["pull_context_count"] == 2


def test_requires_two_target_reports() -> None:
    with pytest.raises(ValueError, match="at least two"):
        build_difficulty_context_binding_review_from_inputs(report_ids=["only-one"])
