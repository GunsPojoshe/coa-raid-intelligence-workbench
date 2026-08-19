from __future__ import annotations

from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable, Mapping

from coa_workbench.collector.current_combatants_roster import parse_current_combatants_roster

from .difficulty_context_binding import (
    _read_raw_payload,
    _report_id_from_request_url,
    _target_report_ids,
)

DIFFICULTY_SEQUENCE_BINDING_VERSION = "difficulty-sequence-binding-v3"
_SCOPED_ENDPOINTS = (
    "report_detail_api",
    "report_encounters_api",
    "report_combatants_roster_api",
)

PrivateScalar = tuple[str, str]
PrivateDifficultyPair = tuple[PrivateScalar, PrivateScalar]


def _mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    return value


def _private_scalar(value: Any) -> PrivateScalar | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, str):
        return ("string", value) if value else None
    if isinstance(value, int):
        return ("integer", str(value))
    if isinstance(value, float):
        return ("number", repr(value))
    return None


def _private_string(value: Any) -> str | None:
    return value if isinstance(value, str) and value else None


def _single(values: set[PrivateScalar]) -> PrivateScalar | None:
    return next(iter(values)) if len(values) == 1 else None


def _private_number(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _server_time(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        raw = float(value)
        return raw / 1000.0 if abs(raw) >= 10_000_000_000 else raw
    if not isinstance(value, str) or not value:
        return None
    prepared = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(prepared)
    except ValueError:
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return None
    return parsed.astimezone(timezone.utc).timestamp()


def _empty_pull_context(pull_id: PrivateScalar) -> dict[str, Any]:
    return {
        "pull_id": pull_id,
        "pull_order": int(pull_id[1]) if pull_id[0] == "integer" else None,
        "snapshot_count": 0,
        "boss_names": set(),
        "difficulty_index": set(),
        "difficulty_name": set(),
        "local_boss_capture_times": [],
    }


def _difficulty_pair(context: Mapping[str, Any]) -> PrivateDifficultyPair | None:
    index = _single(set(context["difficulty_index"]))
    name = _single(set(context["difficulty_name"]))
    if index is None or name is None:
        return None
    return index, name


def _stable_boss(context: Mapping[str, Any]) -> str | None:
    values = set(context["boss_names"])
    return next(iter(values)) if len(values) == 1 else None


def _collect_client_contexts(
    payloads: Iterable[Mapping[str, Any]],
) -> dict[PrivateScalar, dict[str, Any]]:
    pulls: dict[PrivateScalar, dict[str, Any]] = {}
    seen: set[tuple[str, str]] = set()
    for payload in payloads:
        parsed = parse_current_combatants_roster(payload)
        for snapshot in parsed.snapshots:
            snapshot_key = (
                str(snapshot.get("source_character_id") or ""),
                str(snapshot.get("snapshot_hash") or ""),
            )
            if snapshot_key in seen:
                continue
            seen.add(snapshot_key)
            pull_id = _private_scalar(snapshot.get("captured_for_pull_id"))
            if pull_id is None:
                continue
            context = pulls.setdefault(pull_id, _empty_pull_context(pull_id))
            context["snapshot_count"] += 1

            boss = _private_string(snapshot.get("captured_for_boss"))
            if boss is not None:
                context["boss_names"].add(boss)
            instance = _mapping(snapshot.get("instance"), "parsed snapshot.instance")
            for field in ("difficulty_index", "difficulty_name"):
                scalar = _private_scalar(instance.get(field))
                if scalar is not None:
                    context[field].add(scalar)

            captured_at = _private_number(snapshot.get("captured_at"))
            if snapshot.get("source") == "local" and boss is not None and captured_at is not None:
                context["local_boss_capture_times"].append(captured_at / 1000.0)
    return pulls


def _collect_report_detail_rows(
    payloads: Iterable[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    rows_by_key: dict[tuple[Any, ...], dict[str, Any]] = {}
    for payload in payloads:
        encounters = payload.get("encounters")
        if not isinstance(encounters, list):
            continue
        for raw_row in encounters:
            if not isinstance(raw_row, dict):
                continue
            row = _mapping(raw_row, "report detail.encounters[]")
            encounter_id = _private_scalar(row.get("id"))
            name = _private_string(row.get("name"))
            difficulty = _private_scalar(row.get("difficulty"))
            start_time = _server_time(row.get("start_time"))
            end_time = _server_time(row.get("end_time"))
            key = (encounter_id, name, difficulty, start_time, end_time)
            rows_by_key[key] = {
                "encounter_id": encounter_id,
                "name": name,
                "difficulty": difficulty,
                "start_time": start_time,
                "end_time": end_time,
            }
    return list(rows_by_key.values())


def _collect_catalog_rows(
    payloads: Iterable[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    rows_by_key: dict[tuple[Any, ...], dict[str, Any]] = {}
    for payload in payloads:
        encounters = payload.get("encounters")
        if not isinstance(encounters, list):
            continue
        for raw_row in encounters:
            if not isinstance(raw_row, dict):
                continue
            row = _mapping(raw_row, "encounter catalog.encounters[]")
            encounter_id = _private_scalar(row.get("id"))
            name = _private_string(row.get("name"))
            difficulty = _private_scalar(row.get("difficulty"))
            key = (encounter_id, name, difficulty)
            rows_by_key[key] = {
                "encounter_id": encounter_id,
                "name": name,
                "difficulty": difficulty,
            }
    return list(rows_by_key.values())


def _unique_monotonic_alignment(
    client_names: tuple[str, ...],
    server_names: tuple[str, ...],
) -> tuple[int, tuple[int, ...] | None]:
    """Return 0, 1 or 2 where 2 means two-or-more monotonic exact-name alignments."""

    @lru_cache(maxsize=None)
    def solve(client_index: int, server_start: int) -> tuple[int, tuple[int, ...] | None]:
        if client_index == len(client_names):
            return 1, ()
        total = 0
        unique_path: tuple[int, ...] | None = None
        wanted = client_names[client_index]
        remaining = len(client_names) - client_index
        final_start = len(server_names) - remaining
        for server_index in range(server_start, final_start + 1):
            if server_names[server_index] != wanted:
                continue
            count, tail = solve(client_index + 1, server_index + 1)
            if count == 0:
                continue
            if count == 1 and tail is not None and total == 0:
                unique_path = (server_index, *tail)
            else:
                unique_path = None
            total = min(2, total + count)
            if total >= 2:
                return 2, None
        return total, unique_path if total == 1 else None

    return solve(0, 0)


def _catalog_index(rows: Iterable[Mapping[str, Any]]) -> dict[PrivateScalar, list[Mapping[str, Any]]]:
    result: dict[PrivateScalar, list[Mapping[str, Any]]] = {}
    for row in rows:
        encounter_id = row.get("encounter_id")
        if isinstance(encounter_id, tuple) and len(encounter_id) == 2:
            typed = (str(encounter_id[0]), str(encounter_id[1]))
            result.setdefault(typed, []).append(row)
    return result


def _resolve_server_difficulty(
    detail_row: Mapping[str, Any],
    catalog_rows: list[Mapping[str, Any]],
) -> tuple[PrivateScalar | None, bool]:
    detail = detail_row.get("difficulty")
    detail_value = detail if isinstance(detail, tuple) and len(detail) == 2 else None
    catalog_values = {
        row["difficulty"]
        for row in catalog_rows
        if isinstance(row.get("difficulty"), tuple) and len(row["difficulty"]) == 2
    }
    if detail_value is not None and catalog_values and catalog_values != {detail_value}:
        return None, True
    if detail_value is not None:
        return detail_value, False
    if len(catalog_values) == 1:
        return next(iter(catalog_values)), False
    return None, len(catalog_values) > 1


def _report_assessment(
    roster_payloads: Iterable[Mapping[str, Any]],
    detail_payloads: Iterable[Mapping[str, Any]],
    catalog_payloads: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    pulls = _collect_client_contexts(roster_payloads)
    detail_rows = _collect_report_detail_rows(detail_payloads)
    catalog_rows = _collect_catalog_rows(catalog_payloads)
    catalog_by_id = _catalog_index(catalog_rows)

    integer_contexts = [row for row in pulls.values() if row["pull_order"] is not None]
    integer_contexts.sort(key=lambda row: int(row["pull_order"]))
    stable_named_contexts = [row for row in integer_contexts if _stable_boss(row) is not None]

    local_time_contexts = [
        row for row in stable_named_contexts if row["local_boss_capture_times"]
    ]
    local_time_order_consistent = True
    previous_time: float | None = None
    for context in local_time_contexts:
        current_time = min(context["local_boss_capture_times"])
        if previous_time is not None and current_time <= previous_time:
            local_time_order_consistent = False
            break
        previous_time = current_time

    sortable_server_rows = [
        row
        for row in detail_rows
        if isinstance(row.get("name"), str) and row.get("start_time") is not None
    ]
    duplicate_server_starts = len({row["start_time"] for row in sortable_server_rows}) != len(
        sortable_server_rows
    )
    sortable_server_rows.sort(key=lambda row: float(row["start_time"]))

    alignment_count = 0
    alignment: tuple[int, ...] | None = None
    alignment_attempted = bool(stable_named_contexts) and bool(sortable_server_rows)
    if alignment_attempted and not duplicate_server_starts:
        client_names = tuple(str(_stable_boss(row)) for row in stable_named_contexts)
        server_names = tuple(str(row["name"]) for row in sortable_server_rows)
        alignment_count, alignment = _unique_monotonic_alignment(client_names, server_names)

    counts: dict[str, Any] = {
        "pull_context_count": len(pulls),
        "integer_pull_context_count": len(integer_contexts),
        "stable_boss_integer_pull_context_count": len(stable_named_contexts),
        "stable_difficulty_pair_pull_count": sum(
            _difficulty_pair(row) is not None for row in integer_contexts
        ),
        "local_boss_timestamp_pull_count": len(local_time_contexts),
        "local_timestamp_order_corroborated": (
            len(local_time_contexts) >= 2 and local_time_order_consistent
        ),
        "report_detail_row_count": len(detail_rows),
        "report_detail_named_parseable_start_count": len(sortable_server_rows),
        "duplicate_server_start_order": duplicate_server_starts,
        "sequence_alignment_attempted": alignment_attempted,
        "unique_full_sequence_alignment": alignment_count == 1,
        "ambiguous_full_sequence_alignment": alignment_count >= 2,
        "no_full_sequence_alignment": alignment_attempted and alignment_count == 0,
        "sequence_linked_pull_count": 0,
        "sequence_linked_catalog_id_match_count": 0,
        "sequence_linked_catalog_id_ambiguous_count": 0,
        "sequence_linked_catalog_id_missing_count": 0,
        "sequence_linked_boss_name_match_count": 0,
        "sequence_linked_boss_name_mismatch_count": 0,
        "sequence_linked_difficulty_name_match_count": 0,
        "sequence_linked_difficulty_name_mismatch_count": 0,
        "sequence_linked_difficulty_unavailable_count": 0,
        "server_difficulty_surface_conflict_count": 0,
    }
    private_linked_contexts: list[tuple[str, PrivateDifficultyPair, PrivateScalar | None]] = []

    if alignment is not None:
        for context, server_index in zip(stable_named_contexts, alignment, strict=True):
            detail_row = sortable_server_rows[server_index]
            counts["sequence_linked_pull_count"] += 1
            client_boss = _stable_boss(context)
            server_name = detail_row.get("name")
            if client_boss == server_name:
                counts["sequence_linked_boss_name_match_count"] += 1
            else:
                counts["sequence_linked_boss_name_mismatch_count"] += 1

            catalog_matches: list[Mapping[str, Any]] = []
            encounter_id = detail_row.get("encounter_id")
            if isinstance(encounter_id, tuple) and len(encounter_id) == 2:
                typed_id = (str(encounter_id[0]), str(encounter_id[1]))
                catalog_matches = catalog_by_id.get(typed_id, [])
            if len(catalog_matches) == 1:
                counts["sequence_linked_catalog_id_match_count"] += 1
            elif len(catalog_matches) > 1:
                counts["sequence_linked_catalog_id_ambiguous_count"] += 1
            else:
                counts["sequence_linked_catalog_id_missing_count"] += 1

            server_difficulty, conflict = _resolve_server_difficulty(detail_row, catalog_matches)
            if conflict:
                counts["server_difficulty_surface_conflict_count"] += 1
            client_name_difficulty = _single(set(context["difficulty_name"]))
            if client_name_difficulty is None or server_difficulty is None or conflict:
                counts["sequence_linked_difficulty_unavailable_count"] += 1
            elif client_name_difficulty == server_difficulty:
                counts["sequence_linked_difficulty_name_match_count"] += 1
            else:
                counts["sequence_linked_difficulty_name_mismatch_count"] += 1

            pair = _difficulty_pair(context)
            if isinstance(server_name, str) and server_name and pair is not None:
                private_linked_contexts.append((server_name, pair, server_difficulty))

    counts["private_linked_contexts"] = tuple(private_linked_contexts)
    return counts


def _context_map(
    rows: Iterable[tuple[str, PrivateDifficultyPair, PrivateScalar | None]],
) -> dict[str, dict[str, set[Any]]]:
    result: dict[str, dict[str, set[Any]]] = {}
    for name, pair, server_difficulty in rows:
        target = result.setdefault(name, {"client_pairs": set(), "server_difficulties": set()})
        target["client_pairs"].add(pair)
        if server_difficulty is not None:
            target["server_difficulties"].add(server_difficulty)
    return result


def _cross_report_counts(assessments: list[Mapping[str, Any]]) -> dict[str, int | bool]:
    pair_count = 0
    shared_context_count = 0
    comparable_client_count = 0
    same_client_count = 0
    different_client_count = 0
    ambiguous_client_count = 0
    comparable_server_count = 0
    same_server_count = 0
    different_server_count = 0
    ambiguous_server_count = 0

    for left_index in range(len(assessments)):
        for right_index in range(left_index + 1, len(assessments)):
            pair_count += 1
            left = _context_map(assessments[left_index]["private_linked_contexts"])
            right = _context_map(assessments[right_index]["private_linked_contexts"])
            for name in set(left) & set(right):
                shared_context_count += 1
                left_pairs = left[name]["client_pairs"]
                right_pairs = right[name]["client_pairs"]
                if len(left_pairs) == 1 and len(right_pairs) == 1:
                    comparable_client_count += 1
                    if next(iter(left_pairs)) == next(iter(right_pairs)):
                        same_client_count += 1
                    else:
                        different_client_count += 1
                else:
                    ambiguous_client_count += 1

                left_server = left[name]["server_difficulties"]
                right_server = right[name]["server_difficulties"]
                if len(left_server) == 1 and len(right_server) == 1:
                    comparable_server_count += 1
                    if next(iter(left_server)) == next(iter(right_server)):
                        same_server_count += 1
                    else:
                        different_server_count += 1
                elif left_server or right_server:
                    ambiguous_server_count += 1

    return {
        "report_pair_count": pair_count,
        "shared_sequence_linked_boss_context_count": shared_context_count,
        "comparable_client_difficulty_context_count": comparable_client_count,
        "same_client_difficulty_pair_count": same_client_count,
        "different_client_difficulty_pair_count": different_client_count,
        "ambiguous_client_difficulty_context_count": ambiguous_client_count,
        "comparable_server_difficulty_context_count": comparable_server_count,
        "same_server_difficulty_count": same_server_count,
        "different_server_difficulty_count": different_server_count,
        "ambiguous_server_difficulty_context_count": ambiguous_server_count,
        "cross_report_same_difficulty_context_candidate_observed": same_client_count > 0,
        "cross_report_different_difficulty_context_candidate_observed": different_client_count > 0,
    }


def build_difficulty_sequence_binding_review_from_inputs(
    *,
    report_ids: Iterable[str],
    roster_payloads: Mapping[str, Iterable[Mapping[str, Any]]],
    report_detail_payloads: Mapping[str, Iterable[Mapping[str, Any]]],
    encounter_payloads: Mapping[str, Iterable[Mapping[str, Any]]],
) -> dict[str, Any]:
    target_ids = {str(value) for value in report_ids}
    if len(target_ids) < 2:
        raise ValueError("difficulty sequence binding requires at least two reports")

    assessments = [
        _report_assessment(
            tuple(roster_payloads.get(report_id, ())),
            tuple(report_detail_payloads.get(report_id, ())),
            tuple(encounter_payloads.get(report_id, ())),
        )
        for report_id in sorted(target_ids)
    ]
    cross = _cross_report_counts(assessments)

    totals = {
        "report_count": len(assessments),
        "pull_context_count": sum(row["pull_context_count"] for row in assessments),
        "integer_pull_context_count": sum(
            row["integer_pull_context_count"] for row in assessments
        ),
        "stable_boss_integer_pull_context_count": sum(
            row["stable_boss_integer_pull_context_count"] for row in assessments
        ),
        "stable_difficulty_pair_pull_count": sum(
            row["stable_difficulty_pair_pull_count"] for row in assessments
        ),
        "local_boss_timestamp_pull_count": sum(
            row["local_boss_timestamp_pull_count"] for row in assessments
        ),
        "local_timestamp_order_corroborated_report_count": sum(
            row["local_timestamp_order_corroborated"] for row in assessments
        ),
        "report_detail_row_count": sum(row["report_detail_row_count"] for row in assessments),
        "report_detail_named_parseable_start_count": sum(
            row["report_detail_named_parseable_start_count"] for row in assessments
        ),
        "duplicate_server_start_order_report_count": sum(
            row["duplicate_server_start_order"] for row in assessments
        ),
        "unique_full_sequence_alignment_report_count": sum(
            row["unique_full_sequence_alignment"] for row in assessments
        ),
        "ambiguous_full_sequence_alignment_report_count": sum(
            row["ambiguous_full_sequence_alignment"] for row in assessments
        ),
        "no_full_sequence_alignment_report_count": sum(
            row["no_full_sequence_alignment"] for row in assessments
        ),
        "sequence_linked_pull_count": sum(
            row["sequence_linked_pull_count"] for row in assessments
        ),
        "sequence_linked_catalog_id_match_count": sum(
            row["sequence_linked_catalog_id_match_count"] for row in assessments
        ),
        "sequence_linked_catalog_id_ambiguous_count": sum(
            row["sequence_linked_catalog_id_ambiguous_count"] for row in assessments
        ),
        "sequence_linked_catalog_id_missing_count": sum(
            row["sequence_linked_catalog_id_missing_count"] for row in assessments
        ),
        "sequence_linked_boss_name_match_count": sum(
            row["sequence_linked_boss_name_match_count"] for row in assessments
        ),
        "sequence_linked_boss_name_mismatch_count": sum(
            row["sequence_linked_boss_name_mismatch_count"] for row in assessments
        ),
        "sequence_linked_difficulty_name_match_count": sum(
            row["sequence_linked_difficulty_name_match_count"] for row in assessments
        ),
        "sequence_linked_difficulty_name_mismatch_count": sum(
            row["sequence_linked_difficulty_name_mismatch_count"] for row in assessments
        ),
        "sequence_linked_difficulty_unavailable_count": sum(
            row["sequence_linked_difficulty_unavailable_count"] for row in assessments
        ),
        "server_difficulty_surface_conflict_count": sum(
            row["server_difficulty_surface_conflict_count"] for row in assessments
        ),
    }

    if cross["cross_report_same_difficulty_context_candidate_observed"]:
        status = "cross_report_same_difficulty_context_candidate_observed"
    elif cross["cross_report_different_difficulty_context_candidate_observed"]:
        status = "cross_report_different_difficulty_context_candidate_observed"
    elif totals["sequence_linked_pull_count"] > 0:
        status = "server_sequence_context_candidate_observed"
    elif totals["unique_full_sequence_alignment_report_count"] > 0:
        status = "unique_sequence_alignment_observed"
    else:
        status = "insufficient_evidence"

    return {
        "review_version": DIFFICULTY_SEQUENCE_BINDING_VERSION,
        "status": status,
        "source_semantics": {
            "client_pull_order_basis": (
                "pinned_companion_pull_counter_incremented_on_player_regen_disabled"
            ),
            "client_timestamp_basis": "local_ci_time_times_1000_only",
            "peer_timestamp_used_for_server_binding": False,
            "boss_name_used_as_verified_identity": False,
            "sequence_order_used_as_verified_identity": False,
        },
        "sequence_context": totals,
        "cross_report_context": cross,
        "privacy": {
            "report_ids_included": False,
            "pull_ids_included": False,
            "encounter_ids_included": False,
            "boss_names_included": False,
            "difficulty_values_included": False,
            "captured_at_values_included": False,
            "server_time_values_included": False,
            "raw_paths_included": False,
            "raw_payloads_included": False,
            "request_urls_included": False,
            "private_hashes_included": False,
        },
        "verification": {
            "client_pull_counter_source_semantics_verified": True,
            "client_local_capture_timestamp_source_semantics_verified": True,
            "server_encounter_start_time_semantics_verified": False,
            "sequence_relation_semantics_verified": False,
            "runtime_client_server_difficulty_binding_observed": (
                totals["sequence_linked_difficulty_name_match_count"] > 0
            ),
            "final_cross_report_encounter_equivalence_verified": False,
            "fight_duration_comparison_unit_verified": False,
            "cross_report_player_identity_verified": False,
            "numeric_cross_report_scoring_allowed": False,
            "mechanic_semantics_verified": False,
            "planner_scoring_allowed": False,
        },
        "public_release_safe": True,
    }


def _load_scoped_payloads(
    database_path: Path,
    raw_root: Path,
    *,
    endpoint_code: str,
    target_report_ids: set[str],
) -> dict[str, tuple[Mapping[str, Any], ...]]:
    if endpoint_code not in _SCOPED_ENDPOINTS:
        raise ValueError("endpoint is not a reviewed report-scoped sequence source")
    import duckdb

    with duckdb.connect(str(database_path), read_only=True) as connection:
        rows = connection.execute(
            """
            SELECT DISTINCT sc.raw_id, ro.storage_path, rfo.request_url_sanitized
            FROM source_capture AS sc
            JOIN raw_object AS ro ON ro.raw_id = sc.raw_id
            JOIN raw_fetch_observation AS rfo
              ON rfo.observation_id = sc.raw_observation_id
            WHERE sc.endpoint_code = ?
              AND sc.http_status BETWEEN 200 AND 299
              AND rfo.request_url_sanitized IS NOT NULL
            ORDER BY sc.raw_id, rfo.request_url_sanitized
            """,
            [endpoint_code],
        ).fetchall()

    result: dict[str, list[Mapping[str, Any]]] = {
        report_id: [] for report_id in target_report_ids
    }
    seen: set[tuple[str, str]] = set()
    for raw_id, storage_path, request_url in rows:
        report_id = _report_id_from_request_url(str(request_url))
        if report_id not in result:
            continue
        dedupe = (report_id, str(raw_id))
        if dedupe in seen:
            continue
        seen.add(dedupe)
        result[report_id].append(_read_raw_payload(raw_root, storage_path, raw_id))
    return {report_id: tuple(values) for report_id, values in result.items()}


def build_difficulty_sequence_binding_review(
    database_path: Path,
    raw_root: Path,
) -> dict[str, Any]:
    report_ids = _target_report_ids(database_path)
    return build_difficulty_sequence_binding_review_from_inputs(
        report_ids=report_ids,
        roster_payloads=_load_scoped_payloads(
            database_path,
            raw_root,
            endpoint_code="report_combatants_roster_api",
            target_report_ids=report_ids,
        ),
        report_detail_payloads=_load_scoped_payloads(
            database_path,
            raw_root,
            endpoint_code="report_detail_api",
            target_report_ids=report_ids,
        ),
        encounter_payloads=_load_scoped_payloads(
            database_path,
            raw_root,
            endpoint_code="report_encounters_api",
            target_report_ids=report_ids,
        ),
    )


__all__ = [
    "DIFFICULTY_SEQUENCE_BINDING_VERSION",
    "build_difficulty_sequence_binding_review",
    "build_difficulty_sequence_binding_review_from_inputs",
]
