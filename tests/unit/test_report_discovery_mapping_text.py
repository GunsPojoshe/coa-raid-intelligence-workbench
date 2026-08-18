from __future__ import annotations

from coa_workbench.collector.report_discovery_mapping_text import (
    render_report_discovery_mapping_summary_text,
)


def test_plain_text_summary_is_complete_and_scalar_free():
    summary = {
        "schema_version": 1,
        "summary_kind": "report_discovery_mapping_summary",
        "payload": {
            "payload_hash": "a" * 64,
            "schema_fingerprint": "b" * 64,
            "top_level_kind": "object",
            "top_level_keys": ["pagination", "reports", "success"],
            "review_status": "candidate",
        },
        "candidate_decision": {
            "status": "candidate",
            "unique_report_like_collection": True,
            "report_collection_path": "/reports",
            "report_item_selector": "/reports/*",
            "can_promote": False,
            "semantic_verification_required": True,
            "category_semantics_verified": False,
            "pagination_policy_verified": False,
        },
        "report_item_shape": {
            "path": "/reports/*",
            "occurrence_count": 2,
            "observed_keys": ["id", "locations", "title"],
            "required_keys": ["id", "locations", "title"],
            "fields": [
                {
                    "name": "id",
                    "path": "/reports/*/id",
                    "types": ["integer"],
                    "nullable": False,
                    "observed_on_all_items": True,
                    "occurrence_count": 2,
                },
                {
                    "name": "title",
                    "path": "/reports/*/title",
                    "types": ["null", "string"],
                    "nullable": True,
                    "observed_on_all_items": True,
                    "occurrence_count": 2,
                },
            ],
        },
        "array_paths": [
            {
                "path": "/reports",
                "occurrence_count": 1,
                "total_items": 2,
                "min_length": 2,
                "max_length": 2,
                "item_type_counts": {"object": 2},
            }
        ],
        "nullable_paths": [
            {
                "path": "/reports/*/title",
                "occurrence_count": 2,
                "type_counts": {"null": 1, "string": 1},
            }
        ],
        "summary": {
            "field_path_count": 6,
            "node_occurrence_count": 12,
            "numeric_map_path_count": 0,
            "candidate_collection_count": 2,
            "array_path_count": 1,
            "nullable_path_count": 1,
            "report_field_count": 2,
            "contains_source_scalar_values": False,
        },
    }

    rendered = render_report_discovery_mapping_summary_text(summary)

    assert "REPORT_MAPPING_SUMMARY" in rendered
    assert "CANDIDATE_DECISION" in rendered
    assert "REPORT_FIELDS" in rendered
    assert "ARRAY_PATHS" in rendered
    assert "NULLABLE_PATHS" in rendered
    assert "report_item_selector=/reports/*" in rendered
    assert "name=title | path=/reports/*/title | types=null, string" in rendered
    assert "item_type_counts=object=2" in rendered
    assert "type_counts=null=1, string=1" in rendered
    assert "Private Guild" not in rendered
    assert "987654" not in rendered
