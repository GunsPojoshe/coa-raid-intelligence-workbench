from __future__ import annotations

from coa_workbench.analytics.cross_report_equivalence import (
    build_cross_report_equivalence_review_from_inputs,
)


def _model(report_id: str, source_report_id: str) -> dict[str, object]:
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
                        "total_amount": 100,
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


def _detail(report_id: str, difficulty: str) -> dict[str, object]:
    return {"report": {"id": report_id, "difficulty": difficulty}}


def _public(*rows: tuple[str, str]) -> dict[str, object]:
    return {
        "reports": [
            {"id": report_id, "highest_difficulty": difficulty}
            for report_id, difficulty in rows
        ]
    }


def test_equivalence_review_verifies_corroborated_difficulty_and_unique_encounter() -> None:
    models = (_model("r1", "s1"), _model("r2", "s2"))
    result = build_cross_report_equivalence_review_from_inputs(
        models=models,
        report_detail_payloads=(_detail("s1", "private-mode"), _detail("s2", "private-mode")),
        public_report_payloads=(_public(("s1", "private-mode"), ("s2", "private-mode")),),
        encounter_index={
            "r1": {"Example Boss": {"enc-r1"}},
            "r2": {"Example Boss": {"enc-r2"}},
        },
    )

    assert result["status"] == "verified"
    assert result["difficulty_evidence"]["verified_report_count"] == 2
    assert result["difficulty_evidence"]["cross_surface_match_count"] == 2
    assert result["cohort_evidence"]["difficulty_verified_cohort_count"] == 1
    assert result["cohort_evidence"]["encounter_equivalence_verified_cohort_count"] == 1
    assert (
        result["verification"]["all_eligible_cohorts_difficulty_equivalence_verified"]
        is True
    )
    assert (
        result["verification"]["all_eligible_cohorts_encounter_equivalence_verified"]
        is True
    )
    assert result["verification"]["numeric_cross_report_scoring_allowed"] is False


def test_equivalence_review_fails_closed_without_public_corroboration() -> None:
    result = build_cross_report_equivalence_review_from_inputs(
        models=(_model("r1", "s1"), _model("r2", "s2")),
        report_detail_payloads=(_detail("s1", "private-mode"), _detail("s2", "private-mode")),
        public_report_payloads=(),
        encounter_index={
            "r1": {"Example Boss": {"enc-r1"}},
            "r2": {"Example Boss": {"enc-r2"}},
        },
    )

    assert result["status"] == "insufficient_evidence"
    assert result["difficulty_evidence"]["verified_report_count"] == 0
    assert result["cohort_evidence"]["difficulty_verified_cohort_count"] == 0
    assert result["cohort_evidence"]["encounter_equivalence_verified_cohort_count"] == 0


def test_equivalence_review_fails_encounter_identity_when_name_is_not_unique() -> None:
    result = build_cross_report_equivalence_review_from_inputs(
        models=(_model("r1", "s1"), _model("r2", "s2")),
        report_detail_payloads=(_detail("s1", "private-mode"), _detail("s2", "private-mode")),
        public_report_payloads=(_public(("s1", "private-mode"), ("s2", "private-mode")),),
        encounter_index={
            "r1": {"Example Boss": {"enc-r1", "enc-r1-other"}},
            "r2": {"Example Boss": {"enc-r2"}},
        },
    )

    assert result["status"] == "insufficient_evidence"
    assert result["cohort_evidence"]["difficulty_verified_cohort_count"] == 1
    assert result["cohort_evidence"]["encounter_equivalence_verified_cohort_count"] == 0
    assert result["cohort_evidence"]["encounter_non_unique_cohort_count"] == 1


def test_equivalence_review_public_result_contains_no_private_scalar_values() -> None:
    result = build_cross_report_equivalence_review_from_inputs(
        models=(_model("private-r1", "private-s1"), _model("private-r2", "private-s2")),
        report_detail_payloads=(
            _detail("private-s1", "secret-difficulty"),
            _detail("private-s2", "secret-difficulty"),
        ),
        public_report_payloads=(
            _public(
                ("private-s1", "secret-difficulty"),
                ("private-s2", "secret-difficulty"),
            ),
        ),
        encounter_index={
            "private-r1": {"Example Boss": {"enc-private-r1"}},
            "private-r2": {"Example Boss": {"enc-private-r2"}},
        },
    )
    rendered = str(result)

    assert result["public_release_safe"] is True
    assert result["privacy"]["difficulty_values_included"] is False
    assert "private-r1" not in rendered
    assert "private-s1" not in rendered
    assert "secret-difficulty" not in rendered
    assert "Example Raid" not in rendered
    assert "Example Boss" not in rendered
    assert "Private Name" not in rendered
