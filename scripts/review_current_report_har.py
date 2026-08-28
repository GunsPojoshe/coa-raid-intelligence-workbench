from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from coa_workbench.collector.compatible_normalization import (
    normalize_verified_compatible_payload,
)
from coa_workbench.collector.current_combatants_roster import (
    parse_current_combatants_roster,
)
from coa_workbench.collector.current_report_har import extract_current_report_har_slice


def _keys(value: Any) -> list[str]:
    return sorted(str(key) for key in value) if isinstance(value, dict) else []


def _union_row_keys(rows: Any) -> list[str]:
    result: set[str] = set()
    if isinstance(rows, list):
        for row in rows:
            if isinstance(row, dict):
                result.update(str(key) for key in row)
    return sorted(result)


def _dynamic_map_review(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {"key_count": 0, "row_count": 0, "row_fields": []}
    row_count = 0
    fields: set[str] = set()
    for rows in value.values():
        if isinstance(rows, list):
            row_count += len(rows)
            for row in rows:
                if isinstance(row, dict):
                    fields.update(str(key) for key in row)
    return {
        "key_count": len(value),
        "row_count": row_count,
        "row_fields": sorted(fields),
    }


def review_current_report_har(
    har_path: Path,
    *,
    mapping_path: Path,
    allowed_host: str = "coa.ascensionlogs.gg",
) -> dict[str, Any]:
    har_slice = extract_current_report_har_slice(har_path, allowed_host=allowed_host)
    report = har_slice.report_detail.payload
    encounters = har_slice.encounter_catalog.payload
    roster = har_slice.combatants_roster.payload
    damage = har_slice.damage_taken_abilities.payload
    healing = har_slice.spell_healing.payload
    throughput_payloads = [observation.payload for observation in har_slice.throughput]

    mapping_payload = json.loads(mapping_path.read_text(encoding="utf-8"))
    report_normalization = normalize_verified_compatible_payload(report, mapping_payload)
    roster_parse = parse_current_combatants_roster(roster)

    report_encounters = report.get("encounters", [])
    rich_encounters = encounters.get("encounters", [])
    throughput_fields: set[str] = set()
    throughput_character_fields: set[str] = set()
    throughput_series_fields: set[str] = set()
    throughput_total_fields: set[str] = set()
    heroism_nonempty = 0
    for payload in throughput_payloads:
        throughput_fields.update(str(key) for key in payload)
        throughput_character_fields.update(_union_row_keys(payload.get("characters")))
        throughput_total_fields.update(_union_row_keys(payload.get("total")))
        series = payload.get("series")
        if isinstance(series, dict):
            for rows in series.values():
                throughput_series_fields.update(_union_row_keys(rows))
        if isinstance(payload.get("heroism_windows"), list) and payload["heroism_windows"]:
            heroism_nonempty += 1

    healing_review = {
        "top_level_fields": _keys(healing),
        "spell_healing_by_source": _dynamic_map_review(healing.get("spell_healing_by_source")),
        "source_breakdowns": _dynamic_map_review(healing.get("source_breakdowns")),
        "target_breakdowns": _dynamic_map_review(healing.get("target_breakdowns")),
    }
    damage_review = {
        "top_level_fields": _keys(damage),
        "damage_taken_abilities_by_target": _dynamic_map_review(
            damage.get("damage_taken_abilities_by_target")
        ),
    }

    snapshot_counts: dict[int, int] = {}
    for character in roster_parse.characters:
        count = int(character["snapshot_count"])
        snapshot_counts[count] = snapshot_counts.get(count, 0) + 1

    return {
        "schema_version": 1,
        "review_kind": "current_report_private_har_structure_review",
        "source_code": "coa_ascension_logs",
        "network_requests_performed": False,
        "har_slice": har_slice.public_summary(),
        "report_detail": {
            "top_level_fields": _keys(report),
            "report_fields": _keys(report.get("report")),
            "encounter_count": len(report_encounters) if isinstance(report_encounters, list) else 0,
            "encounter_fields": _union_row_keys(report_encounters),
            "summary_fields": _keys(report.get("summary")),
            "compatible_normalization": report_normalization.public_summary(),
        },
        "encounter_catalog": {
            "top_level_fields": _keys(encounters),
            "report_fields": _keys(encounters.get("report")),
            "encounter_count": len(rich_encounters) if isinstance(rich_encounters, list) else 0,
            "encounter_fields": _union_row_keys(rich_encounters),
            "summary_fields": _keys(encounters.get("summary")),
        },
        "combatants_roster": {
            **roster_parse.public_summary(),
            "top_level_fields": _keys(roster),
            "roster_fields": _union_row_keys(roster.get("roster")),
            "snapshot_count_distribution": [
                {"snapshot_count": count, "character_count": snapshot_counts[count]}
                for count in sorted(snapshot_counts)
            ],
            "snapshot_selected_families": [
                "outer_character",
                "player",
                "guild",
                "instance",
                "specialization",
                "talent_container",
                "resolved_ca_talent_rank",
                "hero_build",
                "talent_grid",
                "gear",
                "resolved_item",
                "resolved_bisbeard",
                "resolved_enchant",
                "resolved_set",
                "resolved_gems",
            ],
        },
        "throughput_timeline": {
            "response_count": len(throughput_payloads),
            "top_level_fields": sorted(throughput_fields),
            "character_fields": sorted(throughput_character_fields),
            "series_row_fields": sorted(throughput_series_fields),
            "total_row_fields": sorted(throughput_total_fields),
            "heroism_nonempty_response_count": heroism_nonempty,
            "dynamic_series_keys_included": False,
        },
        "character_spell_healing": healing_review,
        "character_damage_taken_abilities": damage_review,
        "decision_boundary": {
            "report_mapping_reused_via_verified_field_contract_compatibility": True,
            "combatants_roster_current_parser_executed": True,
            "talent_three_way_alignment_required": True,
            "build_and_gear_values_remain_observations": True,
            "mechanic_semantics_verified": False,
            "planner_scoring_allowed": False,
        },
        "privacy": {
            "har_included": False,
            "raw_response_bodies_included": False,
            "report_ids_included": False,
            "encounter_ids_included": False,
            "character_ids_included": False,
            "character_names_included": False,
            "query_values_included": False,
            "headers_included": False,
            "cookies_included": False,
            "source_scalar_values_included": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Privately inspect the current CoA report HAR and emit a scalar-free parser/structure "
            "review. Source IDs, names, query values and response bodies are never emitted."
        )
    )
    parser.add_argument("har", type=Path)
    parser.add_argument(
        "--mapping",
        type=Path,
        default=Path("config/mappings/coa_report_detail_v1.json"),
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    result = review_current_report_har(args.har, mapping_path=args.mapping)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
