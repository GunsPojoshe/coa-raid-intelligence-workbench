from pathlib import Path

from coa_workbench.normalizer import (
    AuraTimelineContract,
    structure_fingerprint,
    validate_single_encounter_aura_capture,
)


def timeline_payload():
    return {
        "success": True,
        "report_id": 2987,
        "encounter_duration_ms": 79602,
        "full_encounter_duration_ms": 79602,
        "window_start_ms": None,
        "window_end_ms": None,
        "spell": {
            "id": "968746",
            "name": "Ninja's Focus",
            "icon": "Interface\\Icons\\nhi_foreshadowing",
            "school": "Physical",
        },
        "series": [
            {
                "ms": 0,
                "event_type": None,
                "source_id": None,
                "source_name": None,
                "source_class": None,
                "target_id": None,
                "target_name": None,
                "target_class": None,
                "event_stacks": None,
                "total_stacks": 0,
                "active_targets": 0,
            },
            {
                "ms": 202,
                "event_type": "buff_applied",
                "source_id": 156120,
                "source_name": "redacted",
                "source_class": "redacted",
                "target_id": 156120,
                "target_name": "redacted",
                "target_class": "redacted",
                "event_stacks": 1,
                "total_stacks": 1,
                "active_targets": 1,
            },
            {
                "ms": 15175,
                "event_type": "buff_removed",
                "source_id": 156120,
                "source_name": "redacted",
                "source_class": "redacted",
                "target_id": 156120,
                "target_name": "redacted",
                "target_class": "redacted",
                "event_stacks": 1,
                "total_stacks": 0,
                "active_targets": 0,
            },
            {
                "ms": 30686,
                "event_type": "buff_applied",
                "source_id": 156120,
                "source_name": "redacted",
                "source_class": "redacted",
                "target_id": 156120,
                "target_name": "redacted",
                "target_class": "redacted",
                "event_stacks": 1,
                "total_stacks": 1,
                "active_targets": 1,
            },
            {
                "ms": 45624,
                "event_type": "buff_removed",
                "source_id": 156120,
                "source_name": "redacted",
                "source_class": "redacted",
                "target_id": 156120,
                "target_name": "redacted",
                "target_class": "redacted",
                "event_stacks": 1,
                "total_stacks": 0,
                "active_targets": 0,
            },
            {
                "ms": 60360,
                "event_type": "buff_applied",
                "source_id": 156120,
                "source_name": "redacted",
                "source_class": "redacted",
                "target_id": 156120,
                "target_name": "redacted",
                "target_class": "redacted",
                "event_stacks": 1,
                "total_stacks": 1,
                "active_targets": 1,
            },
            {
                "ms": 75383,
                "event_type": "buff_removed",
                "source_id": 156120,
                "source_name": "redacted",
                "source_class": "redacted",
                "target_id": 156120,
                "target_name": "redacted",
                "target_class": "redacted",
                "event_stacks": 1,
                "total_stacks": 0,
                "active_targets": 0,
            },
        ],
    }


def reference_payload():
    return {
        "success": True,
        "report_id": 2987,
        "spell_id": 968746,
        "spell_name": "Ninja's Focus",
        "target_id": 156120,
        "encounter_duration_ms": 79602,
        "full_encounter_duration_ms": 79602,
        "window_start_ms": None,
        "window_end_ms": None,
        "sources": [
            {
                "source_id": 156120,
                "source_name": "redacted",
                "source_class": "redacted",
                "source_character_type": "player",
                "source_is_boss": False,
                "application_count": 3,
                "total_uptime_ms": 44934,
                "uptime_percent": 56.45,
                "intervals": [
                    {"start_ms": 202, "end_ms": 15175, "max_stacks": 1},
                    {"start_ms": 30686, "end_ms": 45624, "max_stacks": 1},
                    {"start_ms": 60360, "end_ms": 75383, "max_stacks": 1},
                ],
            }
        ],
    }


def reviewed_contract(payload):
    return AuraTimelineContract.from_dict(
        {
            "mapping_id": "test-single-encounter-v1",
            "source_code": "coa_ascension_logs",
            "mapping_version": "1",
            "status": "verified",
            "schema_fingerprints": [structure_fingerprint(payload)],
            "required_top_level": [
                "encounter_duration_ms",
                "report_id",
                "series",
                "spell",
            ],
            "required_event_fields": ["event_type", "ms", "source_id", "target_id"],
            "event_type_map": {
                "buff_applied": "APPLIED",
                "buff_removed": "REMOVED",
            },
        }
    )


def test_single_encounter_timeline_matches_reference_intervals():
    timeline = timeline_payload()
    result = validate_single_encounter_aura_capture(
        timeline,
        reference_payload(),
        source_encounter_id="64795",
        contract=reviewed_contract(timeline),
    )

    assert result["status"] == "matched"
    assert result["event_count"] == 6
    assert result["ignored"] == [{"path": "/series/0", "reason": "timeline_baseline"}]
    assert result["rejects"] == []
    assert result["anomalies"] == []
    assert result["actual_interval_count"] == 3
    assert result["expected_interval_count"] == 3
    assert [item["termination_reason"] for item in result["actual_intervals"]] == [
        "removed",
        "removed",
        "removed",
    ]


def test_repository_contract_keeps_reviewed_event_map():
    contract = AuraTimelineContract.from_path(
        Path("config/mappings/coa_aura_timeline_single_encounter_v1.json")
    )

    assert contract.production_ready
    assert contract.event_type_map == {
        "buff_applied": "APPLIED",
        "buff_removed": "REMOVED",
    }
    assert "2994424cb95c2a7e1997651226b7942367ebe77003e0f4614aae5da4920f8b98" in (
        contract.schema_fingerprints
    )
