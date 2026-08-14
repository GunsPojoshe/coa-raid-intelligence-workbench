from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from coa_workbench.storage.current_report_analytics import (
    CURRENT_REPORT_ANALYTICS_PERSISTENCE_VERSION,
)
from coa_workbench.storage.migrations import apply_migrations

CURRENT_REPORT_COMPARISON_READ_MODEL_VERSION = "current-report-comparison-read-model-v1"

_ANALYTICS_TYPES = (
    "current_throughput_request_observation",
    "current_throughput_character_observation",
    "current_throughput_point_observation",
    "current_damage_taken_ability_observation",
    "current_healing_spell_observation",
    "current_healing_source_breakdown_observation",
    "current_healing_target_breakdown_observation",
)


def _object_json(value: Any, label: str) -> dict[str, Any]:
    try:
        result = json.loads(str(value))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{label} entity_json is not valid JSON") from exc
    if not isinstance(result, dict):
        raise ValueError(f"{label} entity_json must be an object")
    return result


def _identifier(value: Any, label: str) -> str:
    if value is None or isinstance(value, bool) or str(value) == "":
        raise ValueError(f"{label} must be a non-empty identifier")
    return str(value)


def _numeric(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value))
    except ValueError:
        return None


def _entities(
    connection: Any,
    persistence_run_id: str,
    entity_types: tuple[str, ...],
) -> dict[str, list[dict[str, Any]]]:
    placeholders = ", ".join("?" for _ in entity_types)
    rows = connection.execute(
        f"""
        SELECT entity_type, entity_json
        FROM canonical_entity_observation
        WHERE persistence_run_id = ?
          AND trust_status = 'observed'
          AND entity_type IN ({placeholders})
        ORDER BY entity_type, entity_key, observation_id
        """,
        [persistence_run_id, *entity_types],
    ).fetchall()
    result = {entity_type: [] for entity_type in entity_types}
    for entity_type_raw, entity_json in rows:
        entity_type = str(entity_type_raw)
        result[entity_type].append(_object_json(entity_json, entity_type))
    return result


def _latest_reports(connection: Any) -> dict[str, dict[str, Any]]:
    rows = connection.execute(
        """
        SELECT persistence_run_id, entity_key, entity_json, created_at
        FROM canonical_entity_observation
        WHERE entity_type = 'current_report_observation'
          AND trust_status = 'observed'
        ORDER BY created_at DESC, observation_id DESC
        """
    ).fetchall()
    reports: dict[str, dict[str, Any]] = {}
    for persistence_run_id, entity_key, entity_json, created_at in rows:
        payload = _object_json(entity_json, "current_report_observation")
        source_report_id = _identifier(payload.get("source_report_id"), "report.source_report_id")
        if source_report_id in reports:
            continue
        reports[source_report_id] = {
            "report_id": str(payload.get("report_id") or entity_key),
            "source_report_id": source_report_id,
            "persistence_run_id": str(persistence_run_id),
            "created_at": created_at,
            "payload": payload,
        }
    return reports


def _latest_analytics_runs(connection: Any) -> list[dict[str, Any]]:
    rows = connection.execute(
        """
        SELECT persistence_run_id, reconstruction_sha256,
               COALESCE(finished_at, started_at) AS observed_at
        FROM parser_slice_persistence_run
        WHERE reconstruction_version = ?
          AND status = 'completed'
        ORDER BY observed_at DESC, persistence_run_id DESC
        """,
        [CURRENT_REPORT_ANALYTICS_PERSISTENCE_VERSION],
    ).fetchall()
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for persistence_run_id, artifact_key, observed_at in rows:
        entity = connection.execute(
            """
            SELECT entity_json
            FROM canonical_entity_observation
            WHERE persistence_run_id = ?
              AND entity_type = 'current_throughput_request_observation'
              AND trust_status = 'observed'
            ORDER BY entity_key, observation_id
            LIMIT 1
            """,
            [str(persistence_run_id)],
        ).fetchone()
        if entity is None:
            raise ValueError("completed current-report analytics run has no throughput request")
        payload = _object_json(entity[0], "current_throughput_request_observation")
        source_report_id = _identifier(
            payload.get("source_report_id"),
            "throughput_request.source_report_id",
        )
        if source_report_id in seen:
            continue
        seen.add(source_report_id)
        result.append(
            {
                "persistence_run_id": str(persistence_run_id),
                "artifact_key": str(artifact_key),
                "source_report_id": source_report_id,
                "observed_at": observed_at,
            }
        )
    return result


def _report_context(
    connection: Any,
    report: Mapping[str, Any],
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    rows = _entities(
        connection,
        str(report["persistence_run_id"]),
        ("current_encounter_observation", "current_roster_character_observation"),
    )
    source_report_id = str(report["source_report_id"])
    report_id = str(report["report_id"])

    encounters: dict[str, dict[str, Any]] = {}
    for row in rows["current_encounter_observation"]:
        if _identifier(row.get("report_id"), "encounter.report_id") != report_id:
            raise ValueError("current-report encounter belongs to another canonical report")
        normalized = row.get("normalized")
        if not isinstance(normalized, dict):
            raise ValueError("current-report encounter has no normalized object")
        if _identifier(
            normalized.get("source_report_id"),
            "encounter.normalized.source_report_id",
        ) != source_report_id:
            raise ValueError("current-report encounter source report is inconsistent")
        source_encounter_id = _identifier(
            row.get("source_encounter_id"),
            "encounter.source_encounter_id",
        )
        if source_encounter_id in encounters:
            raise ValueError("duplicate current-report encounter source id")
        encounters[source_encounter_id] = row

    roster: dict[str, dict[str, Any]] = {}
    for row in rows["current_roster_character_observation"]:
        if _identifier(row.get("report_id"), "roster.report_id") != report_id:
            raise ValueError("current-report roster row belongs to another canonical report")
        source_character_id = _identifier(
            row.get("source_character_id"),
            "roster.source_character_id",
        )
        if source_character_id in roster:
            raise ValueError("duplicate current-report roster source id")
        roster[source_character_id] = row
    return encounters, roster


def _throughput_profiles(
    source_report_id: str,
    encounters: Mapping[str, Mapping[str, Any]],
    roster: Mapping[str, Mapping[str, Any]],
    analytics: Mapping[str, list[dict[str, Any]]],
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    requests: dict[int, dict[str, Any]] = {}
    for row in analytics["current_throughput_request_observation"]:
        if _identifier(row.get("source_report_id"), "throughput.source_report_id") != source_report_id:
            raise ValueError("throughput request belongs to another report")
        request_index = int(row["request_index"])
        if request_index in requests:
            raise ValueError("duplicate throughput request_index")
        requests[request_index] = row

    grouped: dict[tuple[str, int, str, str | None], list[dict[str, Any]]] = {}
    unmatched = 0
    missing_total = 0
    for row in analytics["current_throughput_character_observation"]:
        if _identifier(row.get("source_report_id"), "throughput.source_report_id") != source_report_id:
            raise ValueError("throughput character belongs to another report")
        request_index = int(row["request_index"])
        request = requests.get(request_index)
        if request is None:
            raise ValueError("throughput character references unknown request_index")
        encounter_id = _identifier(row.get("source_encounter_id"), "throughput.source_encounter_id")
        metric = _identifier(row.get("metric"), "throughput.metric")
        perspective = None if row.get("perspective") is None else str(row["perspective"])
        if encounter_id not in encounters:
            raise ValueError("throughput character references unknown encounter")
        expected = (
            _identifier(request.get("source_encounter_id"), "request.source_encounter_id"),
            _identifier(request.get("metric"), "request.metric"),
            None if request.get("perspective") is None else str(request["perspective"]),
        )
        if expected != (encounter_id, metric, perspective):
            raise ValueError("throughput request/character profile mismatch")

        character_id = _identifier(row.get("source_character_id"), "throughput.source_character_id")
        if character_id not in roster:
            if row.get("roster_match_status") == "matched":
                raise ValueError("throughput row claims a match for an unknown roster character")
            unmatched += 1
            continue
        total = _numeric(row.get("total_amount"))
        if total is None:
            missing_total += 1
            continue
        player = roster[character_id]
        grouped.setdefault((encounter_id, request_index, metric, perspective), []).append(
            {
                "source_character_id": character_id,
                "name": player.get("name") or row.get("name"),
                "class": player.get("class") or row.get("class"),
                "role": player.get("role"),
                "total_amount": row.get("total_amount"),
                "_total": total,
            }
        )

    profiles: list[dict[str, Any]] = []
    for key in sorted(
        grouped,
        key=lambda item: (item[0], item[1], item[2], "" if item[3] is None else item[3]),
    ):
        encounter_id, request_index, metric, perspective = key
        ordered = sorted(
            grouped[key],
            key=lambda row: (-float(row["_total"]), str(row["source_character_id"])),
        )
        ranked: list[dict[str, Any]] = []
        previous_total: float | None = None
        rank = 0
        for position, player in enumerate(ordered, start=1):
            total = float(player.pop("_total"))
            if previous_total is None or total != previous_total:
                rank = position
                previous_total = total
            ranked.append({"rank": rank, **player})
        normalized = encounters[encounter_id].get("normalized")
        profiles.append(
            {
                "source_encounter_id": encounter_id,
                "encounter_name": normalized.get("name") if isinstance(normalized, dict) else None,
                "request_index": request_index,
                "metric": metric,
                "perspective": perspective,
                "player_count": len(ranked),
                "ranking_basis": "upstream_characters_total_amount_desc",
                "planner_scoring_allowed": False,
                "rows": ranked,
            }
        )
    return profiles, {
        "request_count": len(requests),
        "profile_count": len(profiles),
        "matched_ranked_character_rows": sum(len(profile["rows"]) for profile in profiles),
        "unmatched_character_rows": unmatched,
        "missing_total_rows": missing_total,
    }


def _player_counts(
    source_report_id: str,
    roster: Mapping[str, Mapping[str, Any]],
    analytics: Mapping[str, list[dict[str, Any]]],
) -> tuple[dict[str, dict[str, int]], dict[str, int]]:
    counts = {
        character_id: {
            "throughput_character_observation_count": 0,
            "damage_taken_ability_exact_key_match_count": 0,
            "healing_spell_observation_count": 0,
            "healing_source_breakdown_observation_count": 0,
            "healing_target_breakdown_observation_count": 0,
        }
        for character_id in roster
    }

    throughput_unmatched = 0
    for row in analytics["current_throughput_character_observation"]:
        if _identifier(row.get("source_report_id"), "throughput.source_report_id") != source_report_id:
            raise ValueError("throughput character belongs to another report")
        character_id = _identifier(row.get("source_character_id"), "throughput.source_character_id")
        if character_id in counts:
            counts[character_id]["throughput_character_observation_count"] += 1
        else:
            throughput_unmatched += 1

    damage_rows = 0
    damage_characters: set[str] = set()
    for row in analytics["current_damage_taken_ability_observation"]:
        if _identifier(row.get("source_report_id"), "damage.source_report_id") != source_report_id:
            raise ValueError("damage row belongs to another report")
        group_key = _identifier(row.get("source_group_key"), "damage.source_group_key")
        if group_key in counts:
            counts[group_key]["damage_taken_ability_exact_key_match_count"] += 1
            damage_rows += 1
            damage_characters.add(group_key)

    matched = {
        "healing_spell_explicit_roster_match_row_count": 0,
        "healing_source_explicit_roster_match_row_count": 0,
        "healing_target_explicit_roster_match_row_count": 0,
    }
    rules = (
        (
            "current_healing_spell_observation",
            "source_character_id",
            "healing_spell_observation_count",
            "healing_spell_explicit_roster_match_row_count",
        ),
        (
            "current_healing_source_breakdown_observation",
            "source_character_id",
            "healing_source_breakdown_observation_count",
            "healing_source_explicit_roster_match_row_count",
        ),
        (
            "current_healing_target_breakdown_observation",
            "target_character_id",
            "healing_target_breakdown_observation_count",
            "healing_target_explicit_roster_match_row_count",
        ),
    )
    for entity_type, id_field, player_field, summary_field in rules:
        for row in analytics[entity_type]:
            if _identifier(row.get("source_report_id"), f"{entity_type}.source_report_id") != source_report_id:
                raise ValueError("healing row belongs to another report")
            raw_character_id = row.get(id_field)
            if raw_character_id is None:
                continue
            character_id = _identifier(raw_character_id, f"{entity_type}.{id_field}")
            if character_id in counts:
                counts[character_id][player_field] += 1
                matched[summary_field] += 1

    return counts, {
        "throughput_unmatched_character_row_count": throughput_unmatched,
        "damage_taken_exact_roster_key_match_row_count": damage_rows,
        "damage_taken_exact_roster_key_match_character_count": len(damage_characters),
        **matched,
    }


def _build_model(
    connection: Any,
    analytics_run: Mapping[str, Any],
    report: Mapping[str, Any],
) -> dict[str, Any]:
    source_report_id = str(analytics_run["source_report_id"])
    encounters, roster = _report_context(connection, report)
    analytics = _entities(
        connection,
        str(analytics_run["persistence_run_id"]),
        _ANALYTICS_TYPES,
    )
    profiles, throughput_summary = _throughput_profiles(
        source_report_id,
        encounters,
        roster,
        analytics,
    )
    player_counts, join_summary = _player_counts(
        source_report_id,
        roster,
        analytics,
    )

    points = analytics["current_throughput_point_observation"]
    players = []
    for character_id in sorted(
        roster,
        key=lambda value: (str(roster[value].get("name") or "").casefold(), value),
    ):
        row = roster[character_id]
        players.append(
            {
                "source_character_id": character_id,
                "name": row.get("name"),
                "class": row.get("class"),
                "role": row.get("role"),
                "specs": row.get("specs"),
                "snapshot_count": row.get("snapshot_count"),
                **player_counts[character_id],
            }
        )

    report_payload = dict(report["payload"])
    report_payload["report_id"] = str(report["report_id"])
    report_payload["source_report_id"] = source_report_id
    observed_at = analytics_run["observed_at"]
    return {
        "read_model_version": CURRENT_REPORT_COMPARISON_READ_MODEL_VERSION,
        "report": report_payload,
        "analytics_artifact_key": str(analytics_run["artifact_key"]),
        "analytics_observed_at": (
            observed_at.isoformat() if hasattr(observed_at, "isoformat") else str(observed_at)
        ),
        "encounter_count": len(encounters),
        "roster_character_count": len(roster),
        "players": players,
        "throughput_profiles": profiles,
        "summary": {
            **throughput_summary,
            "throughput_point_count": len(points),
            "throughput_point_exact_character_link_count": sum(
                row.get("series_character_link_status") == "exact_character_id_match"
                for row in points
            ),
            "throughput_point_opaque_group_count": sum(
                row.get("series_character_link_status") == "opaque_group_key"
                for row in points
            ),
            "damage_taken_ability_row_count": len(
                analytics["current_damage_taken_ability_observation"]
            ),
            "healing_spell_row_count": len(analytics["current_healing_spell_observation"]),
            "healing_source_breakdown_row_count": len(
                analytics["current_healing_source_breakdown_observation"]
            ),
            "healing_target_breakdown_row_count": len(
                analytics["current_healing_target_breakdown_observation"]
            ),
            **join_summary,
        },
        "interpretation": {
            "throughput_rank_is_observed_total_only": True,
            "damage_group_key_target_semantics_verified": False,
            "damage_player_link_basis": "exact_source_group_key_equals_roster_character_id",
            "healing_player_link_basis": "explicit_character_id_fields",
            "mechanic_semantics_verified": False,
            "planner_scoring_allowed": False,
        },
        "local_private_payload": True,
        "public_release_safe": False,
    }


def list_current_report_comparison_reports(
    database_path: Path,
    migrations_dir: Path,
) -> dict[str, Any]:
    apply_migrations(database_path, migrations_dir)
    import duckdb

    with duckdb.connect(str(database_path), read_only=True) as connection:
        reports = _latest_reports(connection)
        result = []
        for analytics_run in _latest_analytics_runs(connection):
            report = reports.get(str(analytics_run["source_report_id"]))
            if report is None:
                raise ValueError("analytics run has no matching current-report observation")
            encounters, roster = _report_context(connection, report)
            rows = connection.execute(
                """
                SELECT entity_type, COUNT(*)
                FROM canonical_entity_observation
                WHERE persistence_run_id = ?
                  AND trust_status = 'observed'
                GROUP BY entity_type
                ORDER BY entity_type
                """,
                [str(analytics_run["persistence_run_id"])],
            ).fetchall()
            payload = report["payload"]
            observed_at = analytics_run["observed_at"]
            result.append(
                {
                    "report_id": str(report["report_id"]),
                    "source_report_id": str(report["source_report_id"]),
                    "title": payload.get("title"),
                    "zone": payload.get("zone"),
                    "start_time": payload.get("start_time"),
                    "analytics_artifact_key": str(analytics_run["artifact_key"]),
                    "analytics_observed_at": (
                        observed_at.isoformat()
                        if hasattr(observed_at, "isoformat")
                        else str(observed_at)
                    ),
                    "encounter_count": len(encounters),
                    "roster_character_count": len(roster),
                    "entity_counts": {
                        str(entity_type): int(count) for entity_type, count in rows
                    },
                }
            )
    return {
        "read_model_version": CURRENT_REPORT_COMPARISON_READ_MODEL_VERSION,
        "report_count": len(result),
        "reports": result,
        "local_private_payload": True,
        "public_release_safe": False,
        "planner_scoring_allowed": False,
    }


def build_current_report_comparison_read_model(
    database_path: Path,
    migrations_dir: Path,
    *,
    report_id: str | None = None,
) -> dict[str, Any]:
    apply_migrations(database_path, migrations_dir)
    import duckdb

    with duckdb.connect(str(database_path), read_only=True) as connection:
        reports = _latest_reports(connection)
        candidates = []
        for analytics_run in _latest_analytics_runs(connection):
            report = reports.get(str(analytics_run["source_report_id"]))
            if report is None:
                raise ValueError("analytics run has no matching current-report observation")
            if report_id is not None and str(report["report_id"]) != str(report_id):
                continue
            candidates.append((analytics_run, report))
        if not candidates:
            raise KeyError(
                "no persisted current-report analytics read model"
                if report_id is None
                else str(report_id)
            )
        return _build_model(connection, *candidates[0])


__all__ = [
    "CURRENT_REPORT_COMPARISON_READ_MODEL_VERSION",
    "build_current_report_comparison_read_model",
    "list_current_report_comparison_reports",
]
