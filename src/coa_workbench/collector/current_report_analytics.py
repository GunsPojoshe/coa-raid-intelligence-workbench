from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping
from urllib.parse import parse_qs, urlsplit

from coa_workbench.collector.current_combatants_roster import CurrentRosterParseResult
from coa_workbench.collector.current_report_har import CurrentReportHarSlice, HarJsonObservation
from coa_workbench.collector.source_scope import route_path_parameters

CURRENT_REPORT_ANALYTICS_PARSER_VERSION = "current-report-analytics-v1"

_THROUGHPUT_ROUTE = "/api/reports/{reportId}/encounters/{encounterId}/throughput-timeline"
_DAMAGE_ROUTE = "/api/reports/{reportId}/character_damage_taken_abilities"
_HEALING_ROUTE = "/api/reports/{reportId}/character_spell_healing"

_THROUGHPUT_ROW_FIELDS = (
    "absorb_amount",
    "amount",
    "bucket_ms",
    "effective_amount",
    "overheal_amount",
)
_DAMAGE_ROW_FIELDS = (
    "absorb_count",
    "absorb_full_amount",
    "absorb_full_count",
    "absorbs",
    "block_count",
    "block_full_amount",
    "block_full_count",
    "blocked",
    "casts",
    "damage",
    "deflect_count",
    "dodge_count",
    "evade_count",
    "hit_count",
    "immune_count",
    "miss_count",
    "parry_count",
    "reflect_count",
    "resist_count",
    "resist_full_amount",
    "resist_full_count",
    "resisted",
    "spell_icon",
    "spell_id",
    "spell_name",
    "spell_school",
    "total",
)
_HEALING_SPELL_ROW_FIELDS = (
    "casts",
    "character_class",
    "character_id",
    "character_name",
    "character_spec",
    "character_type",
    "crits",
    "effective_healing",
    "hits",
    "is_boss",
    "overhealing",
    "spell_icon",
    "spell_id",
    "spell_name",
    "spell_school",
    "total_absorbs",
    "total_healing",
)
_HEALING_SOURCE_ROW_FIELDS = (
    "effective_healing",
    "hit_count",
    "overhealing",
    "source_character_id",
    "source_class",
    "source_name",
    "source_type",
    "total_absorbs",
    "total_healing",
)
_HEALING_TARGET_ROW_FIELDS = (
    "effective_healing",
    "hit_count",
    "overhealing",
    "target_character_id",
    "target_class",
    "target_name",
    "target_type",
    "total_absorbs",
    "total_healing",
)


def _object(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field} must be an object")
    return value


def _array(value: Any, field: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"{field} must be an array")
    return value


def _scalar_id(value: Any, field: str) -> str:
    if isinstance(value, bool) or not isinstance(value, (int, str)) or str(value) == "":
        raise ValueError(f"{field} must be an integer or non-empty string identifier")
    return str(value)


def _selected(source: Mapping[str, Any], fields: Iterable[str]) -> dict[str, Any]:
    return {field: source.get(field) for field in fields}


def _query_single(request_url: str, key: str) -> str | None:
    values = parse_qs(urlsplit(request_url).query, keep_blank_values=True).get(key, [])
    if not values:
        return None
    if len(values) != 1:
        raise ValueError(f"query key {key!r} must occur at most once for analytics parsing")
    return str(values[0])


def _query_multi(request_url: str, key: str) -> tuple[str, ...]:
    return tuple(
        str(value)
        for value in parse_qs(urlsplit(request_url).query, keep_blank_values=True).get(key, [])
    )


def _require_success(payload: Mapping[str, Any], field: str) -> None:
    if payload.get("success") is not True:
        raise ValueError(f"{field}.success must be true")


def _group_rows(
    value: Any,
    *,
    field: str,
) -> list[tuple[str, str | None, dict[str, Any]]]:
    """Flatten reviewed dynamic dictionaries without assigning semantics to their keys.

    A current payload family is expected to use dynamic object keys whose values are arrays of rows.
    A one-level nested map of arrays is accepted as a compatibility boundary. The parser preserves
    both key segments as opaque source grouping keys and does not infer character/spell identity from
    them.
    """
    root = _object(value, field)
    rows: list[tuple[str, str | None, dict[str, Any]]] = []
    for outer_key in sorted(root, key=str):
        outer_value = root[outer_key]
        if isinstance(outer_value, list):
            for index, raw_row in enumerate(outer_value):
                rows.append(
                    (
                        str(outer_key),
                        None,
                        _object(raw_row, f"{field}[{outer_key!r}][{index}]"),
                    )
                )
            continue
        if isinstance(outer_value, dict):
            if outer_value and all(isinstance(item, list) for item in outer_value.values()):
                for inner_key in sorted(outer_value, key=str):
                    for index, raw_row in enumerate(outer_value[inner_key]):
                        rows.append(
                            (
                                str(outer_key),
                                str(inner_key),
                                _object(
                                    raw_row,
                                    f"{field}[{outer_key!r}][{inner_key!r}][{index}]",
                                ),
                            )
                        )
                continue
            rows.append((str(outer_key), None, _object(outer_value, f"{field}[{outer_key!r}]")))
            continue
        raise ValueError(f"{field}[{outer_key!r}] must be an object or array")
    return rows


def _report_segment(observation: HarJsonObservation, route_template: str) -> str:
    params = route_path_parameters(route_template, observation.request_url)
    return _scalar_id(params.get("reportId"), "request.reportId")


def _encounter_catalog_ids(har_slice: CurrentReportHarSlice) -> set[str]:
    payload = _object(har_slice.encounter_catalog.payload, "encounter_catalog")
    encounters = _array(payload.get("encounters"), "encounter_catalog.encounters")
    result: set[str] = set()
    for index, raw_row in enumerate(encounters):
        row = _object(raw_row, f"encounter_catalog.encounters[{index}]")
        encounter_id = _scalar_id(row.get("id"), f"encounter_catalog.encounters[{index}].id")
        if encounter_id in result:
            raise ValueError("encounter catalog contains duplicate ids")
        result.add(encounter_id)
    return result


def _roster_ids(roster: CurrentRosterParseResult) -> set[str]:
    return {
        _scalar_id(row.get("source_character_id"), "roster.source_character_id")
        for row in roster.characters
    }


@dataclass(frozen=True, slots=True)
class CurrentReportAnalyticsParseResult:
    source_report_id: str
    throughput_requests: tuple[dict[str, Any], ...]
    throughput_characters: tuple[dict[str, Any], ...]
    throughput_points: tuple[dict[str, Any], ...]
    damage_taken_abilities: tuple[dict[str, Any], ...]
    healing_spells: tuple[dict[str, Any], ...]
    healing_source_breakdowns: tuple[dict[str, Any], ...]
    healing_target_breakdowns: tuple[dict[str, Any], ...]

    def public_summary(self) -> dict[str, Any]:
        matched_throughput_characters = sum(
            row.get("roster_match_status") == "matched" for row in self.throughput_characters
        )
        matched_healing_characters = sum(
            row.get("roster_match_status") == "matched" for row in self.healing_spells
        )
        return {
            "parser_version": CURRENT_REPORT_ANALYTICS_PARSER_VERSION,
            "throughput_request_count": len(self.throughput_requests),
            "throughput_character_count": len(self.throughput_characters),
            "throughput_point_count": len(self.throughput_points),
            "damage_taken_ability_row_count": len(self.damage_taken_abilities),
            "healing_spell_row_count": len(self.healing_spells),
            "healing_source_breakdown_row_count": len(self.healing_source_breakdowns),
            "healing_target_breakdown_row_count": len(self.healing_target_breakdowns),
            "throughput_roster_match_count": matched_throughput_characters,
            "healing_spell_roster_match_count": matched_healing_characters,
            "contains_report_ids": False,
            "contains_encounter_ids": False,
            "contains_character_ids": False,
            "contains_character_names": False,
            "contains_query_values": False,
            "contains_dynamic_group_keys": False,
            "mechanic_semantics_verified": False,
            "planner_scoring_allowed": False,
        }


def parse_current_report_analytics(
    har_slice: CurrentReportHarSlice,
    *,
    roster: CurrentRosterParseResult,
) -> CurrentReportAnalyticsParseResult:
    """Parse current report analytics into deterministic observations without mechanic inference."""
    report_segment = _report_segment(har_slice.report_detail, "/api/reports/{reportId}")
    encounter_ids = _encounter_catalog_ids(har_slice)
    roster_ids = _roster_ids(roster)

    throughput_requests: list[dict[str, Any]] = []
    throughput_characters: list[dict[str, Any]] = []
    throughput_points: list[dict[str, Any]] = []

    for request_index, observation in enumerate(har_slice.throughput):
        params = route_path_parameters(_THROUGHPUT_ROUTE, observation.request_url)
        if _scalar_id(params.get("reportId"), "throughput.reportId") != report_segment:
            raise ValueError("throughput response belongs to a different report")
        encounter_id = _scalar_id(params.get("encounterId"), "throughput.encounterId")
        if encounter_id not in encounter_ids:
            raise ValueError("throughput response references an encounter absent from the catalog")

        payload = _object(observation.payload, f"throughput[{request_index}]")
        _require_success(payload, f"throughput[{request_index}]")
        metric = _query_single(observation.request_url, "metric")
        if metric is None or metric == "":
            raise ValueError("throughput metric query value is required")
        perspective = _query_single(observation.request_url, "perspective")
        request_bucket_size = _query_single(observation.request_url, "bucket_size_ms")

        characters = _array(payload.get("characters"), f"throughput[{request_index}].characters")
        series = _object(payload.get("series"), f"throughput[{request_index}].series")
        character_ids: set[str] = set()

        throughput_requests.append(
            {
                "request_index": request_index,
                "source_report_id": report_segment,
                "source_encounter_id": encounter_id,
                "metric": metric,
                "perspective": perspective,
                "request_bucket_size_ms": request_bucket_size,
                "payload_bucket_size_ms": payload.get("bucket_size_ms"),
                "duration_ms": payload.get("duration_ms"),
                "total": payload.get("total"),
                "heroism_windows": payload.get("heroism_windows"),
                "source_observed_at": observation.observed_at,
                "source_payload_hash": observation.payload_hash,
            }
        )

        for character_index, raw_character in enumerate(characters):
            character = _object(
                raw_character,
                f"throughput[{request_index}].characters[{character_index}]",
            )
            character_id = _scalar_id(
                character.get("character_id"),
                f"throughput[{request_index}].characters[{character_index}].character_id",
            )
            if character_id in character_ids:
                raise ValueError("throughput characters contain duplicate character_id values")
            character_ids.add(character_id)
            throughput_characters.append(
                {
                    "request_index": request_index,
                    "source_report_id": report_segment,
                    "source_encounter_id": encounter_id,
                    "metric": metric,
                    "perspective": perspective,
                    "source_character_id": character_id,
                    "class": character.get("class"),
                    "name": character.get("name"),
                    "total_amount": character.get("total_amount"),
                    "roster_match_status": "matched" if character_id in roster_ids else "unmatched",
                }
            )

        for group_key, subgroup_key, row in _group_rows(
            series,
            field=f"throughput[{request_index}].series",
        ):
            series_character_id = group_key if group_key in character_ids else None
            throughput_points.append(
                {
                    "request_index": request_index,
                    "source_report_id": report_segment,
                    "source_encounter_id": encounter_id,
                    "metric": metric,
                    "perspective": perspective,
                    "source_group_key": group_key,
                    "source_subgroup_key": subgroup_key,
                    "source_character_id": series_character_id,
                    "series_character_link_status": (
                        "exact_character_id_match"
                        if series_character_id is not None
                        else "opaque_group_key"
                    ),
                    **_selected(row, _THROUGHPUT_ROW_FIELDS),
                }
            )

    damage_payload = _object(
        har_slice.damage_taken_abilities.payload,
        "damage_taken_abilities",
    )
    _require_success(damage_payload, "damage_taken_abilities")
    if _report_segment(har_slice.damage_taken_abilities, _DAMAGE_ROUTE) != report_segment:
        raise ValueError("damage-taken response belongs to a different report")
    damage_report_id = damage_payload.get("report_id")
    if damage_report_id is not None and _scalar_id(
        damage_report_id,
        "damage_taken_abilities.report_id",
    ) != report_segment:
        raise ValueError("damage-taken payload report_id disagrees with request path")

    damage_taken_abilities: list[dict[str, Any]] = []
    for group_key, subgroup_key, row in _group_rows(
        damage_payload.get("damage_taken_abilities_by_target"),
        field="damage_taken_abilities.damage_taken_abilities_by_target",
    ):
        damage_taken_abilities.append(
            {
                "source_report_id": report_segment,
                "source_group_key": group_key,
                "source_subgroup_key": subgroup_key,
                "requested_encounter_ids": _query_multi(
                    har_slice.damage_taken_abilities.request_url,
                    "encounterIds[]",
                ),
                **_selected(row, _DAMAGE_ROW_FIELDS),
            }
        )

    healing_payload = _object(har_slice.spell_healing.payload, "spell_healing")
    _require_success(healing_payload, "spell_healing")
    if _report_segment(har_slice.spell_healing, _HEALING_ROUTE) != report_segment:
        raise ValueError("spell-healing response belongs to a different report")
    healing_report_id = healing_payload.get("report_id")
    if healing_report_id is not None and _scalar_id(
        healing_report_id,
        "spell_healing.report_id",
    ) != report_segment:
        raise ValueError("spell-healing payload report_id disagrees with request path")

    requested_healing_encounters = _query_multi(
        har_slice.spell_healing.request_url,
        "encounterIds[]",
    )
    healing_spells: list[dict[str, Any]] = []
    for group_key, subgroup_key, row in _group_rows(
        healing_payload.get("spell_healing_by_source"),
        field="spell_healing.spell_healing_by_source",
    ):
        character_id = row.get("character_id")
        normalized_character_id = (
            _scalar_id(character_id, "spell_healing.character_id")
            if character_id is not None
            else None
        )
        healing_spells.append(
            {
                "source_report_id": report_segment,
                "source_group_key": group_key,
                "source_subgroup_key": subgroup_key,
                "requested_encounter_ids": requested_healing_encounters,
                "source_character_id": normalized_character_id,
                "roster_match_status": (
                    "matched"
                    if normalized_character_id is not None and normalized_character_id in roster_ids
                    else "unmatched"
                ),
                **_selected(row, _HEALING_SPELL_ROW_FIELDS),
            }
        )

    healing_source_breakdowns: list[dict[str, Any]] = []
    for group_key, subgroup_key, row in _group_rows(
        healing_payload.get("source_breakdowns"),
        field="spell_healing.source_breakdowns",
    ):
        healing_source_breakdowns.append(
            {
                "source_report_id": report_segment,
                "source_group_key": group_key,
                "source_subgroup_key": subgroup_key,
                "requested_encounter_ids": requested_healing_encounters,
                **_selected(row, _HEALING_SOURCE_ROW_FIELDS),
            }
        )

    healing_target_breakdowns: list[dict[str, Any]] = []
    for group_key, subgroup_key, row in _group_rows(
        healing_payload.get("target_breakdowns"),
        field="spell_healing.target_breakdowns",
    ):
        healing_target_breakdowns.append(
            {
                "source_report_id": report_segment,
                "source_group_key": group_key,
                "source_subgroup_key": subgroup_key,
                "requested_encounter_ids": requested_healing_encounters,
                **_selected(row, _HEALING_TARGET_ROW_FIELDS),
            }
        )

    return CurrentReportAnalyticsParseResult(
        source_report_id=report_segment,
        throughput_requests=tuple(throughput_requests),
        throughput_characters=tuple(throughput_characters),
        throughput_points=tuple(throughput_points),
        damage_taken_abilities=tuple(damage_taken_abilities),
        healing_spells=tuple(healing_spells),
        healing_source_breakdowns=tuple(healing_source_breakdowns),
        healing_target_breakdowns=tuple(healing_target_breakdowns),
    )


__all__ = [
    "CURRENT_REPORT_ANALYTICS_PARSER_VERSION",
    "CurrentReportAnalyticsParseResult",
    "parse_current_report_analytics",
]
