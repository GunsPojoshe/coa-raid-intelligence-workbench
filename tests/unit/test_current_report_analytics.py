from __future__ import annotations

import json

import pytest

from coa_workbench.collector.current_combatants_roster import CurrentRosterParseResult
from coa_workbench.collector.current_report_analytics import parse_current_report_analytics
from coa_workbench.collector.current_report_har import CurrentReportHarSlice, HarJsonObservation


def _observation(endpoint_code: str, url: str, payload: dict[str, object]) -> HarJsonObservation:
    body = json.dumps(payload, sort_keys=True).encode()
    return HarJsonObservation(
        endpoint_code=endpoint_code,
        request_url=url,
        observed_at="2026-08-14T12:00:00Z",
        payload_bytes=body,
        payload=payload,
    )


def _roster() -> CurrentRosterParseResult:
    return CurrentRosterParseResult(
        characters=(
            {"source_character_id": "101"},
            {"source_character_id": "102"},
        ),
        snapshots=(),
        talent_entries=(),
        gear_entries=(),
        exact_talent_alignment_snapshot_count=0,
    )


def _slice() -> CurrentReportHarSlice:
    return CurrentReportHarSlice(
        report_detail=_observation(
            "report_detail_api",
            "https://coa.ascensionlogs.gg/api/reports/123",
            {"success": True, "report": {"id": 123}, "encounters": [], "summary": {}},
        ),
        encounter_catalog=_observation(
            "report_encounters_api",
            "https://coa.ascensionlogs.gg/api/reports/123/encounters?includeTrash=false",
            {"success": True, "encounters": [{"id": 1}]},
        ),
        combatants_roster=_observation(
            "report_combatants_roster_api",
            "https://coa.ascensionlogs.gg/api/reports/123/combatants-roster?encounterIds=1",
            {"success": True, "roster": []},
        ),
        throughput=(
            _observation(
                "report_encounter_throughput_timeline_api",
                (
                    "https://coa.ascensionlogs.gg/api/reports/123/encounters/1/"
                    "throughput-timeline?bucket_size_ms=1000&metric=damage&perspective=source"
                ),
                {
                    "success": True,
                    "bucket_size_ms": 1000,
                    "duration_ms": 5000,
                    "characters": [
                        {
                            "character_id": 101,
                            "class": "Example",
                            "name": "A",
                            "total_amount": 100,
                        },
                        {
                            "character_id": 102,
                            "class": "Example",
                            "name": "B",
                            "total_amount": 50,
                        },
                    ],
                    "series": {
                        "101": [
                            {
                                "bucket_ms": 0,
                                "amount": 10,
                                "effective_amount": 10,
                                "overheal_amount": 0,
                                "absorb_amount": 0,
                            }
                        ],
                        "opaque-group": [
                            {
                                "bucket_ms": 0,
                                "amount": 2,
                                "effective_amount": 2,
                                "overheal_amount": 0,
                                "absorb_amount": 0,
                            }
                        ],
                    },
                    "total": [],
                    "heroism_windows": [],
                },
            ),
        ),
        damage_taken_abilities=_observation(
            "report_character_damage_taken_abilities_api",
            (
                "https://coa.ascensionlogs.gg/api/reports/123/"
                "character_damage_taken_abilities?encounterIds[]=1&format=json"
            ),
            {
                "success": True,
                "report_id": 123,
                "damage_taken_abilities_by_target": {
                    "target-group": [
                        {
                            "spell_id": 7,
                            "spell_name": "Hit",
                            "spell_school": "physical",
                            "damage": 12,
                            "total": 12,
                        }
                    ]
                },
            },
        ),
        spell_healing=_observation(
            "report_character_spell_healing_api",
            (
                "https://coa.ascensionlogs.gg/api/reports/123/"
                "character_spell_healing?encounterIds[]=1&format=json"
            ),
            {
                "success": True,
                "report_id": 123,
                "spell_healing_by_source": {
                    "source-group": [
                        {
                            "character_id": 101,
                            "character_name": "A",
                            "spell_id": 9,
                            "spell_name": "Heal",
                            "total_healing": 20,
                            "effective_healing": 18,
                            "overhealing": 2,
                            "total_absorbs": 0,
                        }
                    ]
                },
                "source_breakdowns": {
                    "spell-group": [
                        {
                            "source_character_id": 101,
                            "source_name": "A",
                            "total_healing": 20,
                            "effective_healing": 18,
                            "overhealing": 2,
                            "total_absorbs": 0,
                        }
                    ]
                },
                "target_breakdowns": {
                    "spell-group": [
                        {
                            "target_character_id": 102,
                            "target_name": "B",
                            "total_healing": 20,
                            "effective_healing": 18,
                            "overhealing": 2,
                            "total_absorbs": 0,
                        }
                    ]
                },
            },
        ),
    )


def test_current_report_analytics_parser_builds_observation_only_read_models() -> None:
    result = parse_current_report_analytics(_slice(), roster=_roster())

    assert len(result.throughput_requests) == 1
    assert len(result.throughput_characters) == 2
    assert len(result.throughput_points) == 2
    assert len(result.damage_taken_abilities) == 1
    assert len(result.healing_spells) == 1
    assert len(result.healing_source_breakdowns) == 1
    assert len(result.healing_target_breakdowns) == 1

    assert result.throughput_characters[0]["roster_match_status"] == "matched"
    assert {row["series_character_link_status"] for row in result.throughput_points} == {
        "exact_character_id_match",
        "opaque_group_key",
    }
    assert result.healing_spells[0]["roster_match_status"] == "matched"

    public = result.public_summary()
    assert public["throughput_request_count"] == 1
    assert public["throughput_point_count"] == 2
    assert public["contains_report_ids"] is False
    assert public["contains_query_values"] is False
    assert public["contains_dynamic_group_keys"] is False
    assert public["mechanic_semantics_verified"] is False
    assert public["planner_scoring_allowed"] is False


def test_current_report_analytics_parser_fails_closed_on_unknown_encounter() -> None:
    har_slice = _slice()
    bad = _observation(
        "report_encounter_throughput_timeline_api",
        (
            "https://coa.ascensionlogs.gg/api/reports/123/encounters/999/"
            "throughput-timeline?metric=damage"
        ),
        {
            "success": True,
            "characters": [],
            "series": {},
        },
    )
    mutated = CurrentReportHarSlice(
        report_detail=har_slice.report_detail,
        encounter_catalog=har_slice.encounter_catalog,
        combatants_roster=har_slice.combatants_roster,
        throughput=(bad,),
        damage_taken_abilities=har_slice.damage_taken_abilities,
        spell_healing=har_slice.spell_healing,
    )
    with pytest.raises(ValueError, match="absent from the catalog"):
        parse_current_report_analytics(mutated, roster=_roster())
