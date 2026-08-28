from __future__ import annotations

import json

import pytest

from coa_workbench.analytics.difficulty_value_binding import (
    build_difficulty_value_binding_review_from_inputs,
)


def _snapshot(
    *,
    difficulty_index: int,
    difficulty_name: str,
    boss_name: str,
    map_id: int,
) -> dict[str, object]:
    return {
        "captured_for_boss": boss_name,
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


def _detail(report_id: str, difficulty: str) -> dict[str, object]:
    return {"report": {"id": report_id, "difficulty": difficulty}}


def _encounters(difficulty: str, boss_name: str) -> dict[str, object]:
    return {
        "reportDifficulty": difficulty,
        "encounters": [
            {
                "id": "private-encounter-id",
                "name": boss_name,
                "difficulty": difficulty,
            }
        ],
    }


def test_runtime_binding_correlates_two_reports_without_publishing_values() -> None:
    label = "Private Ascended Difficulty Label"
    first_report = "private-report-alpha"
    second_report = "private-report-beta"
    first_boss = "Private Boss Alpha"
    second_boss = "Private Boss Beta"

    review = build_difficulty_value_binding_review_from_inputs(
        report_ids=[first_report, second_report],
        report_detail_payloads={
            first_report: [_detail(first_report, label)],
            second_report: [_detail(second_report, label)],
        },
        encounter_payloads={
            first_report: [_encounters(label, first_boss)],
            second_report: [_encounters(label, second_boss)],
        },
        roster_payloads={
            first_report: [
                _roster(
                    _snapshot(
                        difficulty_index=47,
                        difficulty_name=label,
                        boss_name=first_boss,
                        map_id=987654321,
                    )
                )
            ],
            second_report: [
                _roster(
                    _snapshot(
                        difficulty_index=47,
                        difficulty_name=label,
                        boss_name=second_boss,
                        map_id=987654321,
                    )
                )
            ],
        },
        public_report_payloads=[
            {
                "reports": [
                    {"id": first_report, "highest_difficulty": label},
                    {"id": second_report, "highest_difficulty": label},
                ]
            }
        ],
    )

    assert review["status"] == "cross_report_client_server_correlated"
    assert review["same_report_corroboration"]["client_server_corroborated_report_count"] == 2
    assert review["same_report_corroboration"]["boss_encounter_exact_name_match_count"] == 2
    assert review["cross_report_candidate"] == {
        "all_reports_client_server_corroborated": True,
        "stable_client_difficulty_index_equal_across_reports": True,
        "stable_client_difficulty_name_equal_across_reports": True,
        "difficulty_equivalence_candidate": True,
    }
    assert review["verification"]["final_cross_report_encounter_equivalence_verified"] is False
    assert review["verification"]["numeric_cross_report_scoring_allowed"] is False

    rendered = json.dumps(review, ensure_ascii=False, sort_keys=True)
    for private_value in (
        label,
        first_report,
        second_report,
        first_boss,
        second_boss,
        "Private Instance Name",
        "Private Character Name",
        "private-character-id",
        "private-encounter-id",
        "987654321",
    ):
        assert private_value not in rendered
    assert review["privacy"]["difficulty_values_included"] is False
    assert review["public_release_safe"] is True


def test_ambiguous_client_index_fails_closed() -> None:
    label = "One Label"
    reports = ("r-one", "r-two")
    review = build_difficulty_value_binding_review_from_inputs(
        report_ids=reports,
        report_detail_payloads={report: [_detail(report, label)] for report in reports},
        encounter_payloads={
            report: [_encounters(label, f"boss-{report}")] for report in reports
        },
        roster_payloads={
            "r-one": [
                _roster(
                    _snapshot(
                        difficulty_index=7,
                        difficulty_name=label,
                        boss_name="boss-r-one",
                        map_id=1,
                    ),
                    _snapshot(
                        difficulty_index=8,
                        difficulty_name=label,
                        boss_name="boss-r-one",
                        map_id=1,
                    ),
                )
            ],
            "r-two": [
                _roster(
                    _snapshot(
                        difficulty_index=7,
                        difficulty_name=label,
                        boss_name="boss-r-two",
                        map_id=1,
                    )
                )
            ],
        },
    )

    assert review["status"] == "insufficient_evidence"
    assert review["client_observation"]["stable_difficulty_index_report_count"] == 1
    assert review["client_observation"]["ambiguous_client_difficulty_report_count"] == 1
    assert review["same_report_corroboration"]["client_server_corroborated_report_count"] == 1
    assert review["cross_report_candidate"]["difficulty_equivalence_candidate"] is False


def test_client_server_label_mismatch_is_explicit_and_blocks_candidate() -> None:
    reports = ("r-one", "r-two")
    review = build_difficulty_value_binding_review_from_inputs(
        report_ids=reports,
        report_detail_payloads={
            "r-one": [_detail("r-one", "Server Label")],
            "r-two": [_detail("r-two", "Client Label")],
        },
        encounter_payloads={
            "r-one": [_encounters("Server Label", "boss-one")],
            "r-two": [_encounters("Client Label", "boss-two")],
        },
        roster_payloads={
            "r-one": [
                _roster(
                    _snapshot(
                        difficulty_index=5,
                        difficulty_name="Client Label",
                        boss_name="boss-one",
                        map_id=1,
                    )
                )
            ],
            "r-two": [
                _roster(
                    _snapshot(
                        difficulty_index=5,
                        difficulty_name="Client Label",
                        boss_name="boss-two",
                        map_id=1,
                    )
                )
            ],
        },
    )

    assert review["status"] == "insufficient_evidence"
    assert review["same_report_corroboration"]["mismatch_report_count"] == 1
    assert review["same_report_corroboration"]["client_server_surface_mismatch_count"] >= 1
    assert review["verification"]["runtime_client_server_value_binding_verified"] is False


def test_report_detail_body_id_must_match_private_scope() -> None:
    with pytest.raises(ValueError, match="body ID disagrees"):
        build_difficulty_value_binding_review_from_inputs(
            report_ids=["r-one", "r-two"],
            report_detail_payloads={
                "r-one": [_detail("different-report", "Label")],
                "r-two": [_detail("r-two", "Label")],
            },
        )


def test_requires_two_target_reports() -> None:
    with pytest.raises(ValueError, match="at least two"):
        build_difficulty_value_binding_review_from_inputs(report_ids=["only-one"])
