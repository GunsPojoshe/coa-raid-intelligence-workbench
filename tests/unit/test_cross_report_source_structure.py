from __future__ import annotations

from coa_workbench.analytics.cross_report_source_structure import (
    build_cross_report_source_structure_review_from_inputs,
)


def test_source_structure_review_reports_only_field_names_and_json_types() -> None:
    result = build_cross_report_source_structure_review_from_inputs(
        source_to_canonical={"private-s1": "private-r1", "private-s2": "private-r2"},
        report_detail_payloads=(
            {
                "report": {
                    "id": "private-s1",
                    "difficulty": None,
                    "zone": "Secret Zone",
                    "title": "Secret Title",
                }
            },
            {
                "report": {
                    "id": "private-s2",
                    "difficulty": None,
                    "zone": "Secret Zone",
                    "title": "Other Secret Title",
                }
            },
        ),
        public_report_payloads=(
            {
                "reports": [
                    {
                        "id": "other-report",
                        "highest_difficulty": "secret-mode",
                        "title": "Other Report",
                    }
                ]
            },
        ),
        encounter_rows=(
            {
                "report_id": "private-r1",
                "catalog_observation": {
                    "id": "enc-private-r1",
                    "name": "Secret Boss",
                    "difficulty": "secret-mode",
                    "success": True,
                },
            },
            {
                "report_id": "private-r2",
                "catalog_observation": {
                    "id": "enc-private-r2",
                    "name": "Secret Boss",
                    "difficulty": "secret-mode",
                    "success": False,
                },
            },
        ),
    )

    assert result["report_count"] == 2
    assert result["report_detail"]["matching_report_count"] == 2
    assert result["report_detail"]["direct_field_types"]["difficulty"] == ["null"]
    assert result["encounter_catalog"]["report_count"] == 2
    assert result["encounter_catalog"]["row_count"] == 2
    assert result["encounter_catalog"]["direct_field_types"]["difficulty"] == ["string"]
    assert result["public_report_catalog"]["observed_row_count"] == 1
    assert result["public_report_catalog"]["matching_report_count"] == 0
    assert result["difficulty_structure"]["report_detail_named_fields"] == ["difficulty"]
    assert result["difficulty_structure"]["encounter_catalog_named_fields"] == ["difficulty"]
    assert result["difficulty_structure"]["public_report_named_fields"] == ["highest_difficulty"]
    assert result["difficulty_structure"]["semantic_equivalence_verified"] is False
    assert result["difficulty_structure"]["numeric_cross_report_scoring_allowed"] is False
    assert result["public_release_safe"] is True

    rendered = str(result)
    assert "private-s1" not in rendered
    assert "private-r1" not in rendered
    assert "Secret Zone" not in rendered
    assert "Secret Boss" not in rendered
    assert "secret-mode" not in rendered


def test_source_structure_review_ignores_unrelated_report_and_encounter_rows() -> None:
    result = build_cross_report_source_structure_review_from_inputs(
        source_to_canonical={"s1": "r1", "s2": "r2"},
        report_detail_payloads=(
            {"report": {"id": "other", "difficulty": "unrelated", "private_only": "x"}},
        ),
        public_report_payloads=(),
        encounter_rows=(
            {
                "report_id": "other-r",
                "catalog_observation": {"difficulty": "unrelated", "private_only": "x"},
            },
        ),
    )

    assert result["report_detail"]["matching_report_count"] == 0
    assert result["report_detail"]["direct_field_types"] == {}
    assert result["encounter_catalog"]["report_count"] == 0
    assert result["encounter_catalog"]["row_count"] == 0
    assert result["encounter_catalog"]["direct_field_types"] == {}
