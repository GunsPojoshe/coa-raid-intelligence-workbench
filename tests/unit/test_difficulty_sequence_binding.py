from __future__ import annotations

from types import SimpleNamespace

import coa_workbench.analytics.difficulty_sequence_binding as sequence_binding


def _snapshot(
    *,
    pull_id: int,
    boss: str,
    difficulty_index: int,
    difficulty_name: str,
    captured_at: int,
    key: str,
) -> dict[str, object]:
    return {
        "source_character_id": "private-character",
        "snapshot_hash": key,
        "captured_for_pull_id": pull_id,
        "captured_for_boss": boss,
        "captured_at": captured_at,
        "source": "local",
        "instance": {
            "difficulty_index": difficulty_index,
            "difficulty_name": difficulty_name,
        },
    }


def _parser(payload: dict[str, object]) -> SimpleNamespace:
    return SimpleNamespace(snapshots=tuple(payload["snapshots"]))


def test_sequence_binding_links_unique_ordered_contexts(monkeypatch) -> None:
    monkeypatch.setattr(sequence_binding, "parse_current_combatants_roster", _parser)
    roster_payloads = {
        "r1": [
            {
                "snapshots": [
                    _snapshot(
                        pull_id=11,
                        boss="Boss A",
                        difficulty_index=4,
                        difficulty_name="Hard",
                        captured_at=1_000_000,
                        key="a1",
                    ),
                    _snapshot(
                        pull_id=14,
                        boss="Boss B",
                        difficulty_index=4,
                        difficulty_name="Hard",
                        captured_at=2_000_000,
                        key="b1",
                    ),
                ]
            }
        ],
        "r2": [
            {
                "snapshots": [
                    _snapshot(
                        pull_id=21,
                        boss="Boss A",
                        difficulty_index=4,
                        difficulty_name="Hard",
                        captured_at=3_000_000,
                        key="a2",
                    ),
                    _snapshot(
                        pull_id=25,
                        boss="Boss C",
                        difficulty_index=4,
                        difficulty_name="Hard",
                        captured_at=4_000_000,
                        key="c2",
                    ),
                ]
            }
        ],
    }
    detail_payloads = {
        "r1": [
            {
                "encounters": [
                    {
                        "id": 101,
                        "name": "Boss A",
                        "difficulty": "Hard",
                        "start_time": "2026-01-01T00:00:00Z",
                    },
                    {
                        "id": 102,
                        "name": "Boss B",
                        "difficulty": "Hard",
                        "start_time": "2026-01-01T00:05:00Z",
                    },
                ]
            }
        ],
        "r2": [
            {
                "encounters": [
                    {
                        "id": 201,
                        "name": "Boss A",
                        "difficulty": "Hard",
                        "start_time": "2026-01-02T00:00:00Z",
                    },
                    {
                        "id": 202,
                        "name": "Boss C",
                        "difficulty": "Hard",
                        "start_time": "2026-01-02T00:05:00Z",
                    },
                ]
            }
        ],
    }
    encounter_payloads = {
        "r1": [
            {
                "encounters": [
                    {"id": 101, "name": "Boss A", "difficulty": "Hard"},
                    {"id": 102, "name": "Boss B", "difficulty": "Hard"},
                ]
            }
        ],
        "r2": [
            {
                "encounters": [
                    {"id": 201, "name": "Boss A", "difficulty": "Hard"},
                    {"id": 202, "name": "Boss C", "difficulty": "Hard"},
                ]
            }
        ],
    }

    result = sequence_binding.build_difficulty_sequence_binding_review_from_inputs(
        report_ids={"r1", "r2"},
        roster_payloads=roster_payloads,
        report_detail_payloads=detail_payloads,
        encounter_payloads=encounter_payloads,
    )

    assert result["review_version"] == "difficulty-sequence-binding-v3"
    assert result["status"] == "cross_report_same_difficulty_context_candidate_observed"
    assert result["sequence_context"]["unique_full_sequence_alignment_report_count"] == 2
    assert result["sequence_context"]["sequence_linked_pull_count"] == 4
    assert result["sequence_context"]["sequence_linked_catalog_id_match_count"] == 4
    assert result["sequence_context"]["sequence_linked_difficulty_name_match_count"] == 4
    assert result["cross_report_context"]["shared_sequence_linked_boss_context_count"] == 1
    assert result["cross_report_context"]["same_client_difficulty_pair_count"] == 1
    assert result["privacy"]["boss_names_included"] is False
    assert result["verification"]["final_cross_report_encounter_equivalence_verified"] is False
    assert result["verification"]["numeric_cross_report_scoring_allowed"] is False


def test_sequence_binding_fails_closed_on_repeated_name_alignment(monkeypatch) -> None:
    monkeypatch.setattr(sequence_binding, "parse_current_combatants_roster", _parser)
    roster_payloads = {
        report_id: [
            {
                "snapshots": [
                    _snapshot(
                        pull_id=1,
                        boss="Repeated Boss",
                        difficulty_index=3,
                        difficulty_name="Observed",
                        captured_at=1_000_000,
                        key=f"{report_id}-1",
                    )
                ]
            }
        ]
        for report_id in ("r1", "r2")
    }
    detail_payloads = {
        report_id: [
            {
                "encounters": [
                    {
                        "id": 1,
                        "name": "Repeated Boss",
                        "start_time": f"2026-01-0{index}T00:00:00Z",
                    },
                    {
                        "id": 2,
                        "name": "Repeated Boss",
                        "start_time": f"2026-01-0{index}T00:05:00Z",
                    },
                ]
            }
        ]
        for index, report_id in enumerate(("r1", "r2"), start=1)
    }
    encounter_payloads = {"r1": [], "r2": []}

    result = sequence_binding.build_difficulty_sequence_binding_review_from_inputs(
        report_ids={"r1", "r2"},
        roster_payloads=roster_payloads,
        report_detail_payloads=detail_payloads,
        encounter_payloads=encounter_payloads,
    )

    assert result["status"] == "insufficient_evidence"
    assert result["sequence_context"]["ambiguous_full_sequence_alignment_report_count"] == 2
    assert result["sequence_context"]["sequence_linked_pull_count"] == 0
    assert result["verification"]["sequence_relation_semantics_verified"] is False
