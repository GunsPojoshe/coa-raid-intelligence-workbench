from __future__ import annotations

import json
from pathlib import Path

import pytest

from coa_workbench.collector.current_combatants_roster import CurrentRosterParseResult
from coa_workbench.collector.current_report_analytics import parse_current_report_analytics
from coa_workbench.collector.current_report_analytics_dependencies import (
    register_current_report_analytics_scoped_dependencies,
)
from coa_workbench.collector.current_report_har import extract_current_report_har_slice
from coa_workbench.collector.raw_archive import RawArchive
from coa_workbench.collector.source_acquisition import observe_reviewed_har
from coa_workbench.collector.source_observatory import ReviewedGetContract
from coa_workbench.collector.source_registry import load_source_registry
from coa_workbench.storage.current_report_analytics import (
    persist_current_report_analytics_observations,
)


duckdb = pytest.importorskip("duckdb")


def _entry(path: str, body: dict[str, object], timestamp: str) -> dict[str, object]:
    return {
        "startedDateTime": timestamp,
        "_resourceType": "xhr",
        "request": {"method": "GET", "url": f"https://coa.ascensionlogs.gg{path}"},
        "response": {
            "status": 200,
            "content": {"mimeType": "application/json", "text": json.dumps(body)},
        },
    }


def _contract(
    endpoint_code: str,
    route_template: str,
    parameter_keys: tuple[str, ...],
    *,
    schema_profile_keys: tuple[str, ...] = (),
) -> ReviewedGetContract:
    return ReviewedGetContract(
        source_code="coa_ascension_logs",
        endpoint_code=endpoint_code,
        base_url="https://coa.ascensionlogs.gg",
        route_template=route_template,
        parameter_keys=parameter_keys,
        schema_profile_keys=schema_profile_keys,
        auth_state="browser_context_observed",
        discovery_source="test",
        review_state="verified",
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


def test_current_report_analytics_persistence_is_idempotent_and_report_scoped(
    tmp_path: Path,
) -> None:
    root = Path(__file__).resolve().parents[2]
    migrations = root / "migrations"
    database = tmp_path / "coa.duckdb"
    har = tmp_path / "analytics.har"
    har.write_text(
        json.dumps(
            {
                "log": {
                    "entries": [
                        _entry(
                            "/api/reports/123",
                            {
                                "success": True,
                                "report": {"id": 123},
                                "encounters": [{"id": 1}],
                                "summary": {},
                            },
                            "2026-08-14T12:00:00.000Z",
                        ),
                        _entry(
                            "/api/reports/123/encounters?includeTrash=false",
                            {"success": True, "encounters": [{"id": 1}]},
                            "2026-08-14T12:00:00.010Z",
                        ),
                        _entry(
                            "/api/reports/123/combatants-roster?encounterIds=1",
                            {"success": True, "roster": []},
                            "2026-08-14T12:00:00.020Z",
                        ),
                        _entry(
                            (
                                "/api/reports/123/encounters/1/throughput-timeline"
                                "?bucket_size_ms=1000&metric=damage&perspective=source"
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
                                    "opaque": [
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
                            "2026-08-14T12:00:00.030Z",
                        ),
                        _entry(
                            (
                                "/api/reports/123/character_damage_taken_abilities"
                                "?encounterIds[]=1&format=json"
                            ),
                            {
                                "success": True,
                                "report_id": 123,
                                "damage_taken_abilities_by_target": {
                                    "target": [
                                        {
                                            "spell_id": 7,
                                            "spell_name": "Hit",
                                            "damage": 12,
                                            "total": 12,
                                        }
                                    ]
                                },
                            },
                            "2026-08-14T12:00:00.040Z",
                        ),
                        _entry(
                            (
                                "/api/reports/123/character_spell_healing"
                                "?encounterIds[]=1&format=json"
                            ),
                            {
                                "success": True,
                                "report_id": 123,
                                "spell_healing_by_source": {
                                    "source": [
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
                                    "spell": [
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
                                    "spell": [
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
                            "2026-08-14T12:00:00.050Z",
                        ),
                    ]
                }
            }
        ),
        encoding="utf-8",
    )

    archive = RawArchive(
        tmp_path / "raw",
        database_path=database,
        migrations_dir=migrations,
    )
    contracts = (
        _contract("report_detail_api", "/api/reports/{reportId}", ()),
        _contract(
            "report_encounters_api",
            "/api/reports/{reportId}/encounters",
            ("includeTrash",),
        ),
        _contract(
            "report_combatants_roster_api",
            "/api/reports/{reportId}/combatants-roster",
            ("encounterIds",),
        ),
        _contract(
            "report_encounter_throughput_timeline_api",
            "/api/reports/{reportId}/encounters/{encounterId}/throughput-timeline",
            ("bucket_size_ms", "metric", "perspective"),
            schema_profile_keys=("metric", "perspective"),
        ),
        _contract(
            "report_character_damage_taken_abilities_api",
            "/api/reports/{reportId}/character_damage_taken_abilities",
            ("encounterIds[]", "format"),
        ),
        _contract(
            "report_character_spell_healing_api",
            "/api/reports/{reportId}/character_spell_healing",
            ("encounterIds[]", "format"),
        ),
    )
    for contract in contracts:
        observed = observe_reviewed_har(
            har,
            archive=archive,
            database_path=database,
            migrations_dir=migrations,
            contract=contract,
        )
        assert observed
        assert all(item.outcome == "schema_candidate" for item in observed)

    har_slice = extract_current_report_har_slice(har)
    analytics = parse_current_report_analytics(har_slice, roster=_roster())

    first = persist_current_report_analytics_observations(
        database_path=database,
        migrations_path=migrations,
        har_slice=har_slice,
        analytics=analytics,
    )
    second = persist_current_report_analytics_observations(
        database_path=database,
        migrations_path=migrations,
        har_slice=har_slice,
        analytics=analytics,
    )

    assert first["entity_count"] == 9
    assert first["inserted_observation_count"] == 9
    assert first["matched_observation_count"] == 0
    assert second["inserted_observation_count"] == 0
    assert second["matched_observation_count"] == 9
    assert first["entity_counts"] == {
        "current_damage_taken_ability_observation": 1,
        "current_healing_source_breakdown_observation": 1,
        "current_healing_spell_observation": 1,
        "current_healing_target_breakdown_observation": 1,
        "current_throughput_character_observation": 2,
        "current_throughput_point_observation": 2,
        "current_throughput_request_observation": 1,
    }
    assert first["mechanic_semantics_verified"] is False
    assert first["planner_scoring_allowed"] is False

    registry = load_source_registry(root / "config" / "ascension_logs_sources.yaml")
    dependencies = register_current_report_analytics_scoped_dependencies(
        database,
        migrations,
        registry=registry,
        artifact_key=str(first["input_fingerprint"]),
    )
    assert dependencies.dependency_count == 6
    assert dependencies.scope_path_keys == ("reportId",)

    with duckdb.connect(str(database), read_only=True) as connection:
        assert connection.execute(
            """
            SELECT COUNT(*)
            FROM analysis_run
            WHERE analysis_type = 'current_report_analytics_parse'
            """
        ).fetchone()[0] == 1
        assert connection.execute(
            """
            SELECT COUNT(*)
            FROM artifact_dependency
            WHERE dependency_type = 'source_endpoint_scope'
              AND analysis_type = 'current_report_analytics_parse'
            """
        ).fetchone()[0] == 6
        assert connection.execute(
            """
            SELECT COUNT(*)
            FROM canonical_entity_observation
            WHERE provenance_type = 'source_observatory_current_report_analytics_v1'
            """
        ).fetchone()[0] == 9
        assert connection.execute("SELECT COUNT(*) FROM report").fetchone()[0] == 0
        assert connection.execute("SELECT COUNT(*) FROM encounter").fetchone()[0] == 0
