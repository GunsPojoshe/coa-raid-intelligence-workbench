from __future__ import annotations

import json
from pathlib import Path

import pytest

from coa_workbench.collector.compatible_normalization import (
    normalize_verified_compatible_payload,
)
from coa_workbench.collector.current_combatants_roster import parse_current_combatants_roster
from coa_workbench.collector.current_report_har import extract_current_report_har_slice
from coa_workbench.collector.raw_archive import RawArchive
from coa_workbench.collector.source_acquisition import observe_reviewed_har
from coa_workbench.collector.source_observatory import ReviewedGetContract
from coa_workbench.storage.current_report_observations import (
    persist_current_report_derived_observations,
)


duckdb = pytest.importorskip("duckdb")


def _report_payload() -> dict[str, object]:
    return {
        "success": True,
        "report": {
            "id": 123,
            "title": "Example Report",
            "created_at": "2026-08-14T00:00:00Z",
            "start_time": "2026-08-14T00:00:00Z",
            "end_time": "2026-08-14T01:00:00Z",
            "visibility": "public",
            "timezone": "UTC",
            "realm": "Example",
            "zone": "Example Zone",
            "status": "complete",
            "has_telemetry": True,
        },
        "encounters": [
            {
                "id": 1,
                "name": "Boss One",
                "start_time": "2026-08-14T00:01:00Z",
                "end_time": "2026-08-14T00:05:00Z",
                "success": True,
                "kill_time": {"minutes": 4},
                "wipe_percent": None,
            }
        ],
        "summary": {
            "total_encounters": 1,
            "successful_encounters": 1,
            "duration": 3600,
        },
    }


def _encounter_payload() -> dict[str, object]:
    return {
        "success": True,
        "report": {"id": 123, "title": "Example Report"},
        "encounters": [
            {
                "id": 1,
                "name": "Boss One",
                "start_time": "2026-08-14T00:01:00Z",
                "end_time": "2026-08-14T00:05:00Z",
                "success": True,
                "zone": "Example Zone",
                "kill_time": {"minutes": 4},
                "wipe_percent": None,
                "difficulty": "example",
                "is_boss_encounter": True,
                "participant_count": 1,
            }
        ],
        "summary": {"total_encounters": 1},
    }


def _roster_payload() -> dict[str, object]:
    return {
        "success": True,
        "roster": [
            {
                "character_id": 101,
                "name": "Example",
                "class": "ExampleClass",
                "role": "damage",
                "specs": ["ExampleSpec"],
                "primary_stats": [],
                "potions": {"total": 0, "items": []},
                "healthstones": {"total": 0, "items": []},
                "snapshots": [
                    {
                        "captured_at": 123456,
                        "captured_for_boss": "Boss One",
                        "captured_for_pull_id": 55,
                        "source": "addon",
                        "player": {
                            "class": "ExampleClass",
                            "gender": 0,
                            "guid": "Player-Example",
                            "level": 60,
                            "name": "Example",
                            "race": "Human",
                            "realm": "ExampleRealm",
                        },
                        "guild": {"name": "Guild", "rank_index": 1, "rank_name": "Member"},
                        "instance": {
                            "difficulty_index": 1,
                            "difficulty_name": "Example",
                            "instance_type": "raid",
                            "is_dynamic": False,
                            "map_id": 1,
                            "max_players": 25,
                            "name": "Example Raid",
                            "player_difficulty": 1,
                        },
                        "specialization": {
                            "active_spec_idx": 1,
                            "active_spec_name": "Example Spec",
                            "active_spec_role": "damage",
                            "active_spec_slot": 1,
                            "resolved_ca_talent_ranks": [
                                {
                                    "bisbeard_tree": "example",
                                    "cao_id": 7,
                                    "icon": "icon",
                                    "name": "Talent",
                                    "rank": 1,
                                }
                            ],
                            "hero_build": {"1": {"entry_id": 7, "rank": 1}},
                            "talents": {
                                "class_label": "ExampleClass",
                                "class_slug": "example",
                                "tree_order": ["example"],
                                "trees": {
                                    "1": {
                                        "label": "Example",
                                        "points": 1,
                                        "slug": "example",
                                        "spec_icon": None,
                                        "talents": [
                                            {
                                                "talent_id": "talent",
                                                "entry_id": 7,
                                                "rank": 1,
                                                "max_ranks": 1,
                                                "grid_col": 1,
                                                "grid_row": 1,
                                                "name": "Talent",
                                                "icon": "icon",
                                                "tree_slug": "example",
                                                "tree_label": "Example",
                                                "category_label": None,
                                                "per_rank_text": [],
                                            }
                                        ],
                                    }
                                },
                            },
                        },
                        "gear": {
                            "1": {
                                "enchant": 0,
                                "item_id": 123,
                                "slot": 1,
                                "suffix": 0,
                                "unique": 0,
                                "resolved_item": {"id": 123, "name": "Item"},
                                "resolved_bisbeard": {"version": "v1"},
                                "resolved_enchant": None,
                                "resolved_set": None,
                                "resolved_gems": [],
                            }
                        },
                    }
                ],
            }
        ],
    }


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


def _contract(endpoint_code: str, route_template: str, parameter_keys: tuple[str, ...]) -> ReviewedGetContract:
    return ReviewedGetContract(
        source_code="coa_ascension_logs",
        endpoint_code=endpoint_code,
        base_url="https://coa.ascensionlogs.gg",
        route_template=route_template,
        parameter_keys=parameter_keys,
        auth_state="browser_context_observed",
        discovery_source="test",
        review_state="verified",
    )


def test_current_report_runtime_persistence_is_idempotent_and_observation_only(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[2]
    migrations = root / "migrations"
    database = tmp_path / "coa.duckdb"
    raw_root = tmp_path / "raw"
    har = tmp_path / "report.har"
    har.write_text(
        json.dumps(
            {
                "log": {
                    "entries": [
                        _entry("/api/reports/123", _report_payload(), "2026-08-14T12:00:00.000Z"),
                        _entry(
                            "/api/reports/123/encounters?includeTrash=false",
                            _encounter_payload(),
                            "2026-08-14T12:00:00.010Z",
                        ),
                        _entry(
                            "/api/reports/123/combatants-roster?encounterIds=1",
                            _roster_payload(),
                            "2026-08-14T12:00:00.020Z",
                        ),
                        _entry(
                            "/api/reports/123/encounters/1/throughput-timeline?metric=damage",
                            {"success": True, "series": {}},
                            "2026-08-14T12:00:00.030Z",
                        ),
                        _entry(
                            "/api/reports/123/character_damage_taken_abilities?encounterIds[]=1",
                            {"success": True, "damage_taken_abilities_by_target": {}},
                            "2026-08-14T12:00:00.040Z",
                        ),
                        _entry(
                            "/api/reports/123/character_spell_healing?encounterIds[]=1",
                            {"success": True, "spell_healing_by_source": {}},
                            "2026-08-14T12:00:00.050Z",
                        ),
                    ]
                }
            }
        ),
        encoding="utf-8",
    )

    archive = RawArchive(raw_root, database_path=database, migrations_dir=migrations)
    for contract in (
        _contract("report_detail_api", "/api/reports/{reportId}", ()),
        _contract("report_encounters_api", "/api/reports/{reportId}/encounters", ("includeTrash",)),
        _contract(
            "report_combatants_roster_api",
            "/api/reports/{reportId}/combatants-roster",
            ("encounterIds",),
        ),
    ):
        observed = observe_reviewed_har(
            har,
            archive=archive,
            database_path=database,
            migrations_dir=migrations,
            contract=contract,
        )
        assert len(observed) == 1
        assert observed[0].outcome == "schema_candidate"

    har_slice = extract_current_report_har_slice(har)
    mapping = json.loads(
        (root / "config" / "mappings" / "coa_report_detail_v1.json").read_text(
            encoding="utf-8"
        )
    )
    normalization = normalize_verified_compatible_payload(har_slice.report_detail.payload, mapping)
    roster = parse_current_combatants_roster(har_slice.combatants_roster.payload)

    first = persist_current_report_derived_observations(
        database_path=database,
        migrations_path=migrations,
        har_slice=har_slice,
        normalization=normalization,
        roster=roster,
    )
    second = persist_current_report_derived_observations(
        database_path=database,
        migrations_path=migrations,
        har_slice=har_slice,
        normalization=normalization,
        roster=roster,
    )

    assert first["entity_count"] == 6
    assert first["inserted_observation_count"] == 6
    assert first["matched_observation_count"] == 0
    assert second["entity_count"] == 6
    assert second["inserted_observation_count"] == 0
    assert second["matched_observation_count"] == 6
    assert first["entity_counts"] == {
        "current_encounter_observation": 1,
        "current_gear_slot_observation": 1,
        "current_report_observation": 1,
        "current_roster_character_observation": 1,
        "current_roster_snapshot_observation": 1,
        "current_talent_entry_observation": 1,
    }
    assert first["core_entity_mutation_allowed"] is False
    assert first["reanalysis_dependencies_registered"] is False

    with duckdb.connect(str(database), read_only=True) as connection:
        assert connection.execute("SELECT COUNT(*) FROM canonical_entity_observation").fetchone()[0] == 6
        assert connection.execute("SELECT COUNT(*) FROM parser_slice_persistence_run").fetchone()[0] == 1
        assert connection.execute(
            "SELECT COUNT(*) FROM analysis_run WHERE analysis_type = 'current_report_runtime_parse'"
        ).fetchone()[0] == 1
        assert connection.execute("SELECT COUNT(*) FROM report").fetchone()[0] == 0
        assert connection.execute("SELECT COUNT(*) FROM encounter").fetchone()[0] == 0
