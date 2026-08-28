from __future__ import annotations

import gzip
import json
import re
from pathlib import Path
from typing import Any, Iterable, Mapping
from urllib.parse import urlsplit

from coa_workbench.collector.current_combatants_roster import parse_current_combatants_roster

DIFFICULTY_CONTEXT_BINDING_VERSION = "difficulty-context-binding-v2"
_REPORT_SCOPE_RE = re.compile(r"^/api/reports/([^/]+)(?:/|$)")
_SCOPED_ENDPOINTS = (
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


def _empty_pull_context() -> dict[str, Any]:
    return {
        "snapshot_count": 0,
        "difficulty_index": set(),
        "difficulty_name": set(),
        "player_difficulty": set(),
        "map_id": set(),
        "instance_name": set(),
        "boss_names": set(),
        "captured_at_present_count": 0,
    }


def _empty_report_evidence() -> dict[str, Any]:
    return {
        "roster_payload_count": 0,
        "roster_snapshot_observation_count": 0,
        "duplicate_roster_snapshot_count": 0,
        "unscoped_roster_snapshot_count": 0,
        "seen_snapshot_keys": set(),
        "pull_contexts": {},
        "encounter_payload_count": 0,
        "encounter_row_observation_count": 0,
        "encounter_rows": {},
        "report_difficulty": set(),
    }


def _prepare_payload_map(
    values: Mapping[str, Iterable[Mapping[str, Any]]] | None,
    report_ids: set[str],
    label: str,
) -> dict[str, tuple[Mapping[str, Any], ...]]:
    result = {report_id: () for report_id in report_ids}
    if values is None:
        return result
    unknown = set(str(key) for key in values) - report_ids
    if unknown:
        raise ValueError(f"{label} contains reports outside the target corpus")
    for report_id, rows in values.items():
        result[str(report_id)] = tuple(
            _mapping(row, f"{label}[{report_id}][]") for row in rows
        )
    return result


def _collect_roster(
    evidence: dict[str, Any],
    payloads: Iterable[Mapping[str, Any]],
) -> None:
    seen_snapshot_keys: set[tuple[str, str]] = evidence["seen_snapshot_keys"]
    pulls: dict[PrivateScalar, dict[str, Any]] = evidence["pull_contexts"]
    for payload in payloads:
        parsed = parse_current_combatants_roster(payload)
        evidence["roster_payload_count"] += 1
        evidence["roster_snapshot_observation_count"] += len(parsed.snapshots)
        for snapshot in parsed.snapshots:
            snapshot_key = (str(snapshot.get("source_character_id") or ""), str(snapshot["snapshot_hash"]))
            if snapshot_key in seen_snapshot_keys:
                evidence["duplicate_roster_snapshot_count"] += 1
                continue
            seen_snapshot_keys.add(snapshot_key)

            pull_id = _private_scalar(snapshot.get("captured_for_pull_id"))
            if pull_id is None:
                evidence["unscoped_roster_snapshot_count"] += 1
                continue
            context = pulls.setdefault(pull_id, _empty_pull_context())
            context["snapshot_count"] += 1
            if snapshot.get("captured_at") is not None:
                context["captured_at_present_count"] += 1

            instance = _mapping(snapshot.get("instance"), "parsed snapshot.instance")
            for field, target in (
                ("difficulty_index", "difficulty_index"),
                ("difficulty_name", "difficulty_name"),
                ("player_difficulty", "player_difficulty"),
                ("map_id", "map_id"),
                ("name", "instance_name"),
            ):
                scalar = _private_scalar(instance.get(field))
                if scalar is not None:
                    context[target].add(scalar)
            boss_name = _private_string(snapshot.get("captured_for_boss"))
            if boss_name is not None:
                context["boss_names"].add(boss_name)


def _collect_encounters(
    evidence: dict[str, Any],
    payloads: Iterable[Mapping[str, Any]],
) -> None:
    rows: dict[tuple[PrivateScalar | None, str | None, PrivateScalar | None], dict[str, Any]] = evidence[
        "encounter_rows"
    ]
    for payload in payloads:
        evidence["encounter_payload_count"] += 1
        report_difficulty = _private_scalar(payload.get("reportDifficulty"))
        if report_difficulty is not None:
            evidence["report_difficulty"].add(report_difficulty)
        encounters_raw = payload.get("encounters")
        if not isinstance(encounters_raw, list):
            continue
        evidence["encounter_row_observation_count"] += len(encounters_raw)
        for row_raw in encounters_raw:
            if not isinstance(row_raw, dict):
                continue
            row = _mapping(row_raw, "encounter catalog.encounters[]")
            encounter_id = _private_scalar(row.get("id"))
            name = _private_string(row.get("name"))
            difficulty = _private_scalar(row.get("difficulty"))
            key = (encounter_id, name, difficulty)
            rows[key] = {
                "encounter_id": encounter_id,
                "name": name,
                "difficulty": difficulty,
            }


def _indexes(evidence: Mapping[str, Any]) -> tuple[
    dict[PrivateScalar, list[Mapping[str, Any]]],
    dict[str, list[Mapping[str, Any]]],
    dict[str, list[Mapping[str, Any]]],
]:
    by_typed_id: dict[PrivateScalar, list[Mapping[str, Any]]] = {}
    by_text_id: dict[str, list[Mapping[str, Any]]] = {}
    by_name: dict[str, list[Mapping[str, Any]]] = {}
    rows = _mapping(evidence["encounter_rows"], "encounter rows")
    for row_raw in rows.values():
        row = _mapping(row_raw, "encounter row")
        encounter_id = row.get("encounter_id")
        if isinstance(encounter_id, tuple) and len(encounter_id) == 2:
            typed_id = (str(encounter_id[0]), str(encounter_id[1]))
            by_typed_id.setdefault(typed_id, []).append(row)
            by_text_id.setdefault(typed_id[1], []).append(row)
        name = row.get("name")
        if isinstance(name, str) and name:
            by_name.setdefault(name, []).append(row)
    return by_typed_id, by_text_id, by_name


def _difficulty_pair(context: Mapping[str, Any]) -> PrivateDifficultyPair | None:
    index = _single(set(context["difficulty_index"]))
    name = _single(set(context["difficulty_name"]))
    if index is None or name is None:
        return None
    return index, name


def _report_assessment(evidence: Mapping[str, Any]) -> dict[str, Any]:
    by_typed_id, by_text_id, by_name = _indexes(evidence)
    pulls = _mapping(evidence["pull_contexts"], "pull contexts")

    counts = {
        "pull_context_count": 0,
        "stable_difficulty_index_pull_count": 0,
        "stable_difficulty_name_pull_count": 0,
        "stable_difficulty_pair_pull_count": 0,
        "stable_player_difficulty_pull_count": 0,
        "stable_map_id_pull_count": 0,
        "stable_instance_name_pull_count": 0,
        "stable_boss_name_pull_count": 0,
        "ambiguous_difficulty_pull_count": 0,
        "typed_pull_id_exact_match_count": 0,
        "text_only_pull_id_match_count": 0,
        "pull_id_no_match_count": 0,
        "pull_id_ambiguous_match_count": 0,
        "id_linked_boss_name_match_count": 0,
        "id_linked_boss_name_mismatch_count": 0,
        "id_linked_boss_name_unavailable_count": 0,
        "id_linked_difficulty_name_match_count": 0,
        "id_linked_difficulty_name_mismatch_count": 0,
        "id_linked_difficulty_name_unavailable_count": 0,
        "unique_boss_name_fallback_count": 0,
        "ambiguous_boss_name_fallback_count": 0,
        "missing_boss_name_fallback_count": 0,
    }
    server_linked_contexts: list[tuple[str, PrivateDifficultyPair]] = []
    client_boss_contexts: list[tuple[str, PrivateDifficultyPair]] = []

    for pull_id_raw, context_raw in pulls.items():
        pull_id = pull_id_raw
        if not isinstance(pull_id, tuple) or len(pull_id) != 2:
            raise ValueError("private pull context key is malformed")
        context = _mapping(context_raw, "pull context")
        counts["pull_context_count"] += 1

        index_stable = _single(set(context["difficulty_index"])) is not None
        name_stable = _single(set(context["difficulty_name"])) is not None
        pair = _difficulty_pair(context)
        counts["stable_difficulty_index_pull_count"] += index_stable
        counts["stable_difficulty_name_pull_count"] += name_stable
        counts["stable_difficulty_pair_pull_count"] += pair is not None
        counts["stable_player_difficulty_pull_count"] += (
            _single(set(context["player_difficulty"])) is not None
        )
        counts["stable_map_id_pull_count"] += _single(set(context["map_id"])) is not None
        counts["stable_instance_name_pull_count"] += (
            _single(set(context["instance_name"])) is not None
        )
        boss_names = set(context["boss_names"])
        stable_boss = next(iter(boss_names)) if len(boss_names) == 1 else None
        counts["stable_boss_name_pull_count"] += stable_boss is not None
        counts["ambiguous_difficulty_pull_count"] += not (index_stable and name_stable)
        if stable_boss is not None and pair is not None:
            client_boss_contexts.append((stable_boss, pair))

        typed_rows = by_typed_id.get(pull_id, [])
        text_rows = by_text_id.get(str(pull_id[1]), [])
        linked_row: Mapping[str, Any] | None = None
        if len(typed_rows) == 1:
            counts["typed_pull_id_exact_match_count"] += 1
            linked_row = typed_rows[0]
        elif len(typed_rows) > 1:
            counts["pull_id_ambiguous_match_count"] += 1
        elif len(text_rows) == 1:
            counts["text_only_pull_id_match_count"] += 1
        elif len(text_rows) > 1:
            counts["pull_id_ambiguous_match_count"] += 1
        else:
            counts["pull_id_no_match_count"] += 1

        if linked_row is not None:
            server_name = linked_row.get("name")
            if stable_boss is None or not isinstance(server_name, str) or not server_name:
                counts["id_linked_boss_name_unavailable_count"] += 1
            elif stable_boss == server_name:
                counts["id_linked_boss_name_match_count"] += 1
            else:
                counts["id_linked_boss_name_mismatch_count"] += 1

            client_difficulty = _single(set(context["difficulty_name"]))
            server_difficulty = linked_row.get("difficulty")
            if client_difficulty is None or not isinstance(server_difficulty, tuple):
                counts["id_linked_difficulty_name_unavailable_count"] += 1
            elif client_difficulty == server_difficulty:
                counts["id_linked_difficulty_name_match_count"] += 1
            else:
                counts["id_linked_difficulty_name_mismatch_count"] += 1

            if isinstance(server_name, str) and server_name and pair is not None:
                server_linked_contexts.append((server_name, pair))

        if stable_boss is None:
            counts["missing_boss_name_fallback_count"] += 1
        else:
            name_rows = by_name.get(stable_boss, [])
            if len(name_rows) == 1:
                counts["unique_boss_name_fallback_count"] += 1
            elif len(name_rows) > 1:
                counts["ambiguous_boss_name_fallback_count"] += 1
            else:
                counts["missing_boss_name_fallback_count"] += 1

    unique_rows = list(_mapping(evidence["encounter_rows"], "encounter rows").values())
    counts.update(
        {
            "roster_payload_count": int(evidence["roster_payload_count"]),
            "roster_snapshot_observation_count": int(
                evidence["roster_snapshot_observation_count"]
            ),
            "duplicate_roster_snapshot_count": int(evidence["duplicate_roster_snapshot_count"]),
            "unscoped_roster_snapshot_count": int(evidence["unscoped_roster_snapshot_count"]),
            "encounter_payload_count": int(evidence["encounter_payload_count"]),
            "encounter_row_observation_count": int(evidence["encounter_row_observation_count"]),
            "unique_encounter_row_count": len(unique_rows),
            "encounter_row_with_id_count": sum(
                _mapping(row, "encounter row").get("encounter_id") is not None
                for row in unique_rows
            ),
            "encounter_row_with_name_count": sum(
                isinstance(_mapping(row, "encounter row").get("name"), str)
                for row in unique_rows
            ),
            "encounter_row_with_difficulty_count": sum(
                _mapping(row, "encounter row").get("difficulty") is not None
                for row in unique_rows
            ),
            "report_difficulty_stable": _single(set(evidence["report_difficulty"])) is not None,
        }
    )
    counts["private_server_linked_contexts"] = tuple(server_linked_contexts)
    counts["private_client_boss_contexts"] = tuple(client_boss_contexts)
    return counts


def _private_context_map(
    rows: Iterable[tuple[str, PrivateDifficultyPair]],
) -> dict[str, set[PrivateDifficultyPair]]:
    result: dict[str, set[PrivateDifficultyPair]] = {}
    for name, pair in rows:
        result.setdefault(name, set()).add(pair)
    return result


def _cross_report_context_counts(assessments: list[Mapping[str, Any]]) -> dict[str, int | bool]:
    pair_count = 0
    shared_client_boss_count = 0
    comparable_client_boss_count = 0
    same_client_difficulty_count = 0
    different_client_difficulty_count = 0
    ambiguous_client_boss_count = 0
    shared_server_encounter_count = 0
    comparable_server_encounter_count = 0
    same_server_linked_difficulty_count = 0
    different_server_linked_difficulty_count = 0
    ambiguous_server_encounter_count = 0

    for left_index in range(len(assessments)):
        for right_index in range(left_index + 1, len(assessments)):
            pair_count += 1
            left = assessments[left_index]
            right = assessments[right_index]

            left_client = _private_context_map(left["private_client_boss_contexts"])
            right_client = _private_context_map(right["private_client_boss_contexts"])
            for name in set(left_client) & set(right_client):
                shared_client_boss_count += 1
                if len(left_client[name]) == 1 and len(right_client[name]) == 1:
                    comparable_client_boss_count += 1
                    if next(iter(left_client[name])) == next(iter(right_client[name])):
                        same_client_difficulty_count += 1
                    else:
                        different_client_difficulty_count += 1
                else:
                    ambiguous_client_boss_count += 1

            left_server = _private_context_map(left["private_server_linked_contexts"])
            right_server = _private_context_map(right["private_server_linked_contexts"])
            for name in set(left_server) & set(right_server):
                shared_server_encounter_count += 1
                if len(left_server[name]) == 1 and len(right_server[name]) == 1:
                    comparable_server_encounter_count += 1
                    if next(iter(left_server[name])) == next(iter(right_server[name])):
                        same_server_linked_difficulty_count += 1
                    else:
                        different_server_linked_difficulty_count += 1
                else:
                    ambiguous_server_encounter_count += 1

    candidate = (
        same_server_linked_difficulty_count > 0
        and different_server_linked_difficulty_count == 0
        and ambiguous_server_encounter_count == 0
    )
    return {
        "report_pair_count": pair_count,
        "shared_client_boss_context_count": shared_client_boss_count,
        "comparable_client_boss_context_count": comparable_client_boss_count,
        "same_client_difficulty_pair_count": same_client_difficulty_count,
        "different_client_difficulty_pair_count": different_client_difficulty_count,
        "ambiguous_client_boss_context_count": ambiguous_client_boss_count,
        "shared_server_linked_encounter_context_count": shared_server_encounter_count,
        "comparable_server_linked_encounter_context_count": comparable_server_encounter_count,
        "same_server_linked_client_difficulty_pair_count": same_server_linked_difficulty_count,
        "different_server_linked_client_difficulty_pair_count": different_server_linked_difficulty_count,
        "ambiguous_server_linked_encounter_context_count": ambiguous_server_encounter_count,
        "cross_report_difficulty_context_candidate_observed": candidate,
    }


def build_difficulty_context_binding_review_from_inputs(
    *,
    report_ids: Iterable[str],
    encounter_payloads: Mapping[str, Iterable[Mapping[str, Any]]] | None = None,
    roster_payloads: Mapping[str, Iterable[Mapping[str, Any]]] | None = None,
) -> dict[str, Any]:
    prepared_ids = {str(value) for value in report_ids if str(value)}
    if len(prepared_ids) < 2:
        raise ValueError("difficulty context binding requires at least two target reports")
    encounters = _prepare_payload_map(encounter_payloads, prepared_ids, "encounter_payloads")
    rosters = _prepare_payload_map(roster_payloads, prepared_ids, "roster_payloads")

    evidence_by_report = {report_id: _empty_report_evidence() for report_id in prepared_ids}
    for report_id in sorted(prepared_ids):
        evidence = evidence_by_report[report_id]
        _collect_encounters(evidence, encounters[report_id])
        _collect_roster(evidence, rosters[report_id])

    assessments = [_report_assessment(evidence_by_report[key]) for key in sorted(prepared_ids)]
    cross_report = _cross_report_context_counts(assessments)

    exact_id_matches = sum(item["typed_pull_id_exact_match_count"] for item in assessments)
    stable_pairs = sum(item["stable_difficulty_pair_pull_count"] for item in assessments)
    difficulty_matches = sum(item["id_linked_difficulty_name_match_count"] for item in assessments)
    difficulty_mismatches = sum(
        item["id_linked_difficulty_name_mismatch_count"] for item in assessments
    )

    if cross_report["cross_report_difficulty_context_candidate_observed"]:
        status = "cross_report_context_candidate_observed"
    elif exact_id_matches > 0:
        status = "pull_context_id_relation_observed"
    elif stable_pairs > 0:
        status = "client_pull_context_observed"
    else:
        status = "insufficient_evidence"

    return {
        "review_version": DIFFICULTY_CONTEXT_BINDING_VERSION,
        "status": status,
        "report_count": len(assessments),
        "client_context": {
            "roster_payload_count": sum(item["roster_payload_count"] for item in assessments),
            "roster_snapshot_observation_count": sum(
                item["roster_snapshot_observation_count"] for item in assessments
            ),
            "duplicate_roster_snapshot_count": sum(
                item["duplicate_roster_snapshot_count"] for item in assessments
            ),
            "unscoped_roster_snapshot_count": sum(
                item["unscoped_roster_snapshot_count"] for item in assessments
            ),
            "pull_context_count": sum(item["pull_context_count"] for item in assessments),
            "stable_difficulty_index_pull_count": sum(
                item["stable_difficulty_index_pull_count"] for item in assessments
            ),
            "stable_difficulty_name_pull_count": sum(
                item["stable_difficulty_name_pull_count"] for item in assessments
            ),
            "stable_difficulty_pair_pull_count": stable_pairs,
            "stable_player_difficulty_pull_count": sum(
                item["stable_player_difficulty_pull_count"] for item in assessments
            ),
            "stable_map_id_pull_count": sum(
                item["stable_map_id_pull_count"] for item in assessments
            ),
            "stable_instance_name_pull_count": sum(
                item["stable_instance_name_pull_count"] for item in assessments
            ),
            "stable_boss_name_pull_count": sum(
                item["stable_boss_name_pull_count"] for item in assessments
            ),
            "ambiguous_difficulty_pull_count": sum(
                item["ambiguous_difficulty_pull_count"] for item in assessments
            ),
            "basis": "current_combatants_roster_grouped_by_private_captured_for_pull_id",
        },
        "server_context": {
            "encounter_payload_count": sum(item["encounter_payload_count"] for item in assessments),
            "encounter_row_observation_count": sum(
                item["encounter_row_observation_count"] for item in assessments
            ),
            "unique_encounter_row_count": sum(
                item["unique_encounter_row_count"] for item in assessments
            ),
            "encounter_row_with_id_count": sum(
                item["encounter_row_with_id_count"] for item in assessments
            ),
            "encounter_row_with_name_count": sum(
                item["encounter_row_with_name_count"] for item in assessments
            ),
            "encounter_row_with_difficulty_count": sum(
                item["encounter_row_with_difficulty_count"] for item in assessments
            ),
            "stable_report_difficulty_report_count": sum(
                item["report_difficulty_stable"] for item in assessments
            ),
        },
        "private_relation_candidates": {
            "typed_pull_id_exact_match_count": exact_id_matches,
            "text_only_pull_id_match_count": sum(
                item["text_only_pull_id_match_count"] for item in assessments
            ),
            "pull_id_no_match_count": sum(item["pull_id_no_match_count"] for item in assessments),
            "pull_id_ambiguous_match_count": sum(
                item["pull_id_ambiguous_match_count"] for item in assessments
            ),
            "id_linked_boss_name_match_count": sum(
                item["id_linked_boss_name_match_count"] for item in assessments
            ),
            "id_linked_boss_name_mismatch_count": sum(
                item["id_linked_boss_name_mismatch_count"] for item in assessments
            ),
            "id_linked_boss_name_unavailable_count": sum(
                item["id_linked_boss_name_unavailable_count"] for item in assessments
            ),
            "id_linked_difficulty_name_match_count": difficulty_matches,
            "id_linked_difficulty_name_mismatch_count": difficulty_mismatches,
            "id_linked_difficulty_name_unavailable_count": sum(
                item["id_linked_difficulty_name_unavailable_count"] for item in assessments
            ),
            "unique_boss_name_fallback_count": sum(
                item["unique_boss_name_fallback_count"] for item in assessments
            ),
            "ambiguous_boss_name_fallback_count": sum(
                item["ambiguous_boss_name_fallback_count"] for item in assessments
            ),
            "missing_boss_name_fallback_count": sum(
                item["missing_boss_name_fallback_count"] for item in assessments
            ),
            "basis": (
                "private_typed_scalar_equality_candidate_for_captured_for_pull_id_vs_encounter_id_"
                "plus_private_exact_boss_name_diagnostic"
            ),
            "pull_id_semantics_promoted": False,
            "boss_name_used_as_verified_identity": False,
        },
        "cross_report_context": cross_report,
        "verification": {
            "exact_pull_id_value_equality_observed": exact_id_matches > 0,
            "pull_id_semantics_verified": False,
            "runtime_client_server_difficulty_binding_observed": (
                difficulty_matches > 0 and difficulty_mismatches == 0
            ),
            "final_cross_report_encounter_equivalence_verified": False,
            "backend_transformation_semantics_verified": False,
            "fight_duration_comparison_unit_verified": False,
            "cross_report_player_identity_verified": False,
            "numeric_cross_report_scoring_allowed": False,
            "mechanic_semantics_verified": False,
            "planner_scoring_allowed": False,
        },
        "privacy": {
            "report_ids_included": False,
            "pull_ids_included": False,
            "encounter_ids_included": False,
            "boss_names_included": False,
            "character_ids_included": False,
            "character_names_included": False,
            "difficulty_values_included": False,
            "instance_names_included": False,
            "map_values_included": False,
            "captured_at_values_included": False,
            "raw_payloads_included": False,
            "raw_paths_included": False,
            "request_urls_included": False,
            "query_values_included": False,
            "private_hashes_included": False,
        },
        "public_release_safe": True,
    }


def _report_id_from_request_url(request_url: str) -> str:
    match = _REPORT_SCOPE_RE.match(urlsplit(request_url).path)
    if match is None:
        raise ValueError("scoped source request URL has no report path segment")
    report_id = match.group(1)
    if report_id == "public":
        raise ValueError("public route cannot be used as a private report scope")
    return report_id


def _read_raw_payload(raw_root: Path, storage_path_raw: Any, raw_id: Any) -> Mapping[str, Any]:
    root = raw_root.resolve()
    storage_path = Path(str(storage_path_raw))
    path = storage_path if storage_path.is_absolute() else root / storage_path
    resolved = path.resolve()
    if root not in resolved.parents and resolved != root:
        raise ValueError(f"raw storage path escapes raw root for {raw_id}")
    if not resolved.is_file():
        raise FileNotFoundError(resolved)
    if resolved.suffix.casefold() == ".gz":
        with gzip.open(resolved, "rt", encoding="utf-8") as stream:
            payload = json.load(stream)
    else:
        payload = json.loads(resolved.read_text(encoding="utf-8"))
    return _mapping(payload, "raw JSON payload")


def _target_report_ids(database_path: Path) -> set[str]:
    import duckdb

    with duckdb.connect(str(database_path), read_only=True) as connection:
        rows = connection.execute(
            """
            SELECT DISTINCT json_extract_string(entity_json, '$.source_report_id')
            FROM canonical_entity_observation
            WHERE entity_type = 'current_report_observation'
              AND trust_status = 'observed'
              AND json_extract_string(entity_json, '$.source_report_id') IS NOT NULL
            ORDER BY 1
            """
        ).fetchall()
    result = {str(row[0]) for row in rows if row[0] is not None and str(row[0])}
    if len(result) < 2:
        raise ValueError("difficulty context binding requires at least two persisted reports")
    return result


def _load_scoped_payloads(
    database_path: Path,
    raw_root: Path,
    *,
    endpoint_code: str,
    target_report_ids: set[str],
) -> dict[str, tuple[Mapping[str, Any], ...]]:
    if endpoint_code not in _SCOPED_ENDPOINTS:
        raise ValueError("endpoint is not a reviewed report-scoped context source")
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
        dedup_key = (report_id, str(raw_id))
        if dedup_key in seen:
            continue
        seen.add(dedup_key)
        result[report_id].append(_read_raw_payload(raw_root, storage_path, raw_id))
    return {key: tuple(value) for key, value in result.items()}


def build_difficulty_context_binding_review(
    database_path: Path,
    raw_root: Path,
) -> dict[str, Any]:
    report_ids = _target_report_ids(database_path)
    return build_difficulty_context_binding_review_from_inputs(
        report_ids=report_ids,
        encounter_payloads=_load_scoped_payloads(
            database_path,
            raw_root,
            endpoint_code="report_encounters_api",
            target_report_ids=report_ids,
        ),
        roster_payloads=_load_scoped_payloads(
            database_path,
            raw_root,
            endpoint_code="report_combatants_roster_api",
            target_report_ids=report_ids,
        ),
    )


__all__ = [
    "DIFFICULTY_CONTEXT_BINDING_VERSION",
    "build_difficulty_context_binding_review",
    "build_difficulty_context_binding_review_from_inputs",
]
