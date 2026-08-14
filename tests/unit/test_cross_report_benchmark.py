from __future__ import annotations

from coa_workbench.analytics.cross_report_benchmark import (
    build_cross_report_structural_benchmark_from_models,
)
from coa_workbench.analytics.cross_report_review import build_public_cross_report_review


def _model(report_id: str, source_report_id: str, total: int) -> dict[str, object]:
    return {
        "read_model_version": "current-report-comparison-read-model-v1",
        "report": {
            "report_id": report_id,
            "source_report_id": source_report_id,
            "zone": "Example Raid",
        },
        "throughput_profiles": [
            {
                "source_encounter_id": f"enc-{report_id}",
                "encounter_name": "Example Boss",
                "request_index": 0,
                "metric": "damage",
                "perspective": "source",
                "planner_scoring_allowed": False,
                "rows": [
                    {
                        "rank": 1,
                        "source_character_id": f"char-{report_id}",
                        "name": "Private Name",
                        "total_amount": total,
                    }
                ],
            }
        ],
        "interpretation": {
            "mechanic_semantics_verified": False,
            "planner_scoring_allowed": False,
        },
        "local_private_payload": True,
        "public_release_safe": False,
    }


def test_cross_report_structural_benchmark_builds_exact_peer_cohort() -> None:
    result = build_cross_report_structural_benchmark_from_models(
        (_model("r1", "s1", 100), _model("r2", "s2", 90))
    )

    assert result["report_count"] == 2
    assert result["candidate_peer_cohort_count"] == 1
    assert result["eligible_peer_cohort_count"] == 1
    assert result["ambiguous_peer_cohort_count"] == 0
    assert result["eligible_profile_count"] == 2
    assert result["eligible_ranked_player_row_count"] == 2

    cohort = result["cohorts"][0]
    assert cohort["status"] == "eligible_structural_peer"
    assert cohort["distinct_report_count"] == 2
    assert cohort["difficulty_equivalence_verified"] is False
    assert cohort["cross_report_player_identity_verified"] is False
    assert cohort["numeric_cross_report_scoring_allowed"] is False
    assert result["interpretation"]["planner_scoring_allowed"] is False


def test_cross_report_structural_benchmark_marks_repeated_report_profile_ambiguous() -> None:
    first = _model("r1", "s1", 100)
    first["throughput_profiles"] = [
        *first["throughput_profiles"],
        {
            "source_encounter_id": "enc-r1-repeat",
            "encounter_name": "Example Boss",
            "request_index": 1,
            "metric": "damage",
            "perspective": "source",
            "planner_scoring_allowed": False,
            "rows": [],
        },
    ]

    result = build_cross_report_structural_benchmark_from_models(
        (first, _model("r2", "s2", 90))
    )

    assert result["eligible_peer_cohort_count"] == 0
    assert result["ambiguous_peer_cohort_count"] == 1
    assert result["cohorts"][0]["status"] == "ambiguous_repeated_profile_per_report"


def test_public_cross_report_review_contains_no_private_scalar_values() -> None:
    model = build_cross_report_structural_benchmark_from_models(
        (_model("private-r1", "private-s1", 100), _model("private-r2", "private-s2", 90))
    )
    public = build_public_cross_report_review(model, deterministic_requery_equal=True)
    rendered = str(public)

    assert public["status"] == "completed"
    assert public["eligible_peer_cohort_count"] == 1
    assert public["verification"]["deterministic_requery_equal"] is True
    assert public["verification"]["numeric_cross_report_scoring_allowed"] is False
    assert public["privacy"]["report_ids_included"] is False
    assert "private-r1" not in rendered
    assert "Example Raid" not in rendered
    assert "Example Boss" not in rendered
    assert "Private Name" not in rendered
