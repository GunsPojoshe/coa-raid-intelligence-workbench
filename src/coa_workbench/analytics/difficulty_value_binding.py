from __future__ import annotations

import gzip
import json
import re
from pathlib import Path
from typing import Any, Iterable, Mapping
from urllib.parse import urlsplit

from coa_workbench.collector.current_combatants_roster import parse_current_combatants_roster

DIFFICULTY_VALUE_BINDING_VERSION = "difficulty-value-binding-v1"
_REPORT_SCOPE_RE = re.compile(r"^/api/reports/([^/]+)(?:/|$)")
_SCOPED_ENDPOINTS = (
    "report_detail_api",
    "report_encounters_api",
    "report_combatants_roster_api",
)
_PUBLIC_ENDPOINT = "reports_public_api"

PrivateScalar = tuple[str, str]


def _mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    return value


def _list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"{label} must be an array")
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
    if not isinstance(value, str) or not value:
        return None
    return value


def _single(values: set[PrivateScalar]) -> PrivateScalar | None:
    return next(iter(values)) if len(values) == 1 else None


def _empty_report_evidence() -> dict[str, Any]:
    return {
        "roster_payload_count": 0,
        "roster_snapshot_count": 0,
        "roster_difficulty_index": set(),
        "roster_difficulty_name": set(),
        "roster_player_difficulty": set(),
        "roster_map_id": set(),
        "roster_instance_name": set(),
        "roster_boss_difficulty": {},
        "detail_difficulty": set(),
        "catalog_report_difficulty": set(),
        "catalog_encounter_difficulty": set(),
        "catalog_encounter_by_name": {},
        "public_highest_difficulty": set(),
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
    for payload in payloads:
        parsed = parse_current_combatants_roster(payload)
        evidence["roster_payload_count"] += 1
        evidence["roster_snapshot_count"] += len(parsed.snapshots)
        for snapshot in parsed.snapshots:
            instance = _mapping(snapshot.get("instance"), "parsed snapshot.instance")
            field_targets = (
                ("difficulty_index", "roster_difficulty_index"),
                ("difficulty_name", "roster_difficulty_name"),
                ("player_difficulty", "roster_player_difficulty"),
                ("map_id", "roster_map_id"),
                ("name", "roster_instance_name"),
            )
            for field, target in field_targets:
                scalar = _private_scalar(instance.get(field))
                if scalar is not None:
                    evidence[target].add(scalar)

            boss_name = _private_string(snapshot.get("captured_for_boss"))
            difficulty_name = _private_scalar(instance.get("difficulty_name"))
            if boss_name is not None and difficulty_name is not None:
                evidence["roster_boss_difficulty"].setdefault(boss_name, set()).add(
                    difficulty_name
                )


def _collect_detail(
    evidence: dict[str, Any],
    report_id: str,
    payloads: Iterable[Mapping[str, Any]],
) -> None:
    for payload in payloads:
        report_raw = payload.get("report")
        if not isinstance(report_raw, dict):
            continue
        report = _mapping(report_raw, "report detail.report")
        body_report_id = report.get("id")
        if body_report_id is not None and not isinstance(body_report_id, bool):
            if str(body_report_id) != report_id:
                raise ValueError("report-detail body ID disagrees with private request scope")
        difficulty = _private_scalar(report.get("difficulty"))
        if difficulty is not None:
            evidence["detail_difficulty"].add(difficulty)


def _collect_encounters(
    evidence: dict[str, Any],
    payloads: Iterable[Mapping[str, Any]],
) -> None:
    for payload in payloads:
        report_difficulty = _private_scalar(payload.get("reportDifficulty"))
        if report_difficulty is not None:
            evidence["catalog_report_difficulty"].add(report_difficulty)
        encounters_raw = payload.get("encounters")
        if not isinstance(encounters_raw, list):
            continue
        for row_raw in encounters_raw:
            if not isinstance(row_raw, dict):
                continue
            row = _mapping(row_raw, "encounter catalog.encounters[]")
            difficulty = _private_scalar(row.get("difficulty"))
            if difficulty is not None:
                evidence["catalog_encounter_difficulty"].add(difficulty)
            name = _private_string(row.get("name"))
            if name is not None and difficulty is not None:
                evidence["catalog_encounter_by_name"].setdefault(name, set()).add(difficulty)


def _collect_public(
    evidence_by_report: Mapping[str, dict[str, Any]],
    payloads: Iterable[Mapping[str, Any]],
) -> None:
    for payload in payloads:
        reports_raw = payload.get("reports")
        if not isinstance(reports_raw, list):
            continue
        for row_raw in reports_raw:
            if not isinstance(row_raw, dict):
                continue
            report_id_raw = row_raw.get("id")
            if report_id_raw is None or isinstance(report_id_raw, bool):
                continue
            report_id = str(report_id_raw)
            evidence = evidence_by_report.get(report_id)
            if evidence is None:
                continue
            difficulty = _private_scalar(row_raw.get("highest_difficulty"))
            if difficulty is not None:
                evidence["public_highest_difficulty"].add(difficulty)


def _boss_binding_counts(evidence: Mapping[str, Any]) -> tuple[int, int, int]:
    matched = 0
    mismatched = 0
    ambiguous = 0
    roster_by_name = _mapping(evidence["roster_boss_difficulty"], "roster boss map")
    catalog_by_name = _mapping(evidence["catalog_encounter_by_name"], "catalog boss map")
    for boss_name, client_values_raw in roster_by_name.items():
        server_values_raw = catalog_by_name.get(boss_name)
        if server_values_raw is None:
            continue
        client_values = set(client_values_raw)
        server_values = set(server_values_raw)
        if len(client_values) != 1 or len(server_values) != 1:
            ambiguous += 1
            continue
        if next(iter(client_values)) == next(iter(server_values)):
            matched += 1
        else:
            mismatched += 1
    return matched, mismatched, ambiguous


def _report_assessment(evidence: Mapping[str, Any]) -> dict[str, Any]:
    roster_index = set(evidence["roster_difficulty_index"])
    roster_name = set(evidence["roster_difficulty_name"])
    player_difficulty = set(evidence["roster_player_difficulty"])
    map_ids = set(evidence["roster_map_id"])
    instance_names = set(evidence["roster_instance_name"])
    detail = set(evidence["detail_difficulty"])
    catalog_top = set(evidence["catalog_report_difficulty"])
    catalog_rows = set(evidence["catalog_encounter_difficulty"])
    public = set(evidence["public_highest_difficulty"])

    client_name = _single(roster_name)
    server_surfaces = {
        "report_detail": _single(detail),
        "encounter_catalog_report": _single(catalog_top),
        "encounter_catalog_rows": _single(catalog_rows),
        "public_report": _single(public),
    }
    observed_server_values = [value for value in server_surfaces.values() if value is not None]
    matches = sum(
        client_name is not None and value == client_name for value in observed_server_values
    )
    mismatches = sum(
        client_name is not None and value != client_name for value in observed_server_values
    )
    backend_internal_mismatch = len(set(observed_server_values)) > 1
    boss_matches, boss_mismatches, boss_ambiguous = _boss_binding_counts(evidence)

    client_stable = _single(roster_index) is not None and client_name is not None
    corroborated = (
        client_stable
        and matches > 0
        and mismatches == 0
        and not backend_internal_mismatch
        and boss_mismatches == 0
    )
    return {
        "roster_payload_count": int(evidence["roster_payload_count"]),
        "roster_snapshot_count": int(evidence["roster_snapshot_count"]),
        "roster_index_stable": _single(roster_index) is not None,
        "roster_name_stable": client_name is not None,
        "roster_player_difficulty_stable": _single(player_difficulty) is not None,
        "roster_map_id_stable": _single(map_ids) is not None,
        "roster_instance_name_stable": _single(instance_names) is not None,
        "detail_observed": _single(detail) is not None,
        "catalog_report_observed": _single(catalog_top) is not None,
        "catalog_rows_observed": _single(catalog_rows) is not None,
        "public_observed": _single(public) is not None,
        "client_server_surface_match_count": matches,
        "client_server_surface_mismatch_count": mismatches,
        "backend_internal_mismatch": backend_internal_mismatch,
        "boss_encounter_match_count": boss_matches,
        "boss_encounter_mismatch_count": boss_mismatches,
        "boss_encounter_ambiguous_count": boss_ambiguous,
        "client_server_corroborated": corroborated,
        "private_index": _single(roster_index),
        "private_name": client_name,
    }


def build_difficulty_value_binding_review_from_inputs(
    *,
    report_ids: Iterable[str],
    report_detail_payloads: Mapping[str, Iterable[Mapping[str, Any]]] | None = None,
    encounter_payloads: Mapping[str, Iterable[Mapping[str, Any]]] | None = None,
    roster_payloads: Mapping[str, Iterable[Mapping[str, Any]]] | None = None,
    public_report_payloads: Iterable[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    prepared_ids = {str(value) for value in report_ids if str(value)}
    if len(prepared_ids) < 2:
        raise ValueError("difficulty value binding requires at least two target reports")

    detail = _prepare_payload_map(report_detail_payloads, prepared_ids, "report_detail_payloads")
    encounters = _prepare_payload_map(encounter_payloads, prepared_ids, "encounter_payloads")
    rosters = _prepare_payload_map(roster_payloads, prepared_ids, "roster_payloads")
    evidence_by_report = {report_id: _empty_report_evidence() for report_id in prepared_ids}

    for report_id in sorted(prepared_ids):
        evidence = evidence_by_report[report_id]
        _collect_detail(evidence, report_id, detail[report_id])
        _collect_encounters(evidence, encounters[report_id])
        _collect_roster(evidence, rosters[report_id])
    _collect_public(evidence_by_report, public_report_payloads)

    assessments = [_report_assessment(evidence_by_report[key]) for key in sorted(prepared_ids)]
    corroborated_count = sum(item["client_server_corroborated"] for item in assessments)
    mismatch_report_count = sum(
        item["client_server_surface_mismatch_count"] > 0
        or item["backend_internal_mismatch"]
        or item["boss_encounter_mismatch_count"] > 0
        for item in assessments
    )
    stable_index_report_count = sum(item["roster_index_stable"] for item in assessments)
    stable_name_report_count = sum(item["roster_name_stable"] for item in assessments)
    ambiguous_client_report_count = sum(
        not item["roster_index_stable"] or not item["roster_name_stable"]
        for item in assessments
    )

    all_corroborated = corroborated_count == len(assessments)
    private_indexes = [item["private_index"] for item in assessments]
    private_names = [item["private_name"] for item in assessments]
    index_equal = all(value is not None for value in private_indexes) and len(
        set(private_indexes)
    ) == 1
    name_equal = all(value is not None for value in private_names) and len(set(private_names)) == 1
    cross_report_candidate = all_corroborated and index_equal and name_equal

    if cross_report_candidate:
        status = "cross_report_client_server_correlated"
    elif all_corroborated:
        status = "client_server_correlated_but_not_equal"
    else:
        status = "insufficient_evidence"

    return {
        "review_version": DIFFICULTY_VALUE_BINDING_VERSION,
        "status": status,
        "report_count": len(assessments),
        "client_observation": {
            "roster_payload_count": sum(item["roster_payload_count"] for item in assessments),
            "roster_snapshot_count": sum(item["roster_snapshot_count"] for item in assessments),
            "stable_difficulty_index_report_count": stable_index_report_count,
            "stable_difficulty_name_report_count": stable_name_report_count,
            "stable_player_difficulty_report_count": sum(
                item["roster_player_difficulty_stable"] for item in assessments
            ),
            "stable_map_id_report_count": sum(item["roster_map_id_stable"] for item in assessments),
            "stable_instance_name_report_count": sum(
                item["roster_instance_name_stable"] for item in assessments
            ),
            "ambiguous_client_difficulty_report_count": ambiguous_client_report_count,
            "basis": "current_combatants_roster_snapshot_instance_fields",
        },
        "server_observation": {
            "report_detail_observed_report_count": sum(item["detail_observed"] for item in assessments),
            "encounter_catalog_report_difficulty_observed_report_count": sum(
                item["catalog_report_observed"] for item in assessments
            ),
            "encounter_catalog_row_difficulty_observed_report_count": sum(
                item["catalog_rows_observed"] for item in assessments
            ),
            "public_highest_difficulty_observed_report_count": sum(
                item["public_observed"] for item in assessments
            ),
        },
        "same_report_corroboration": {
            "client_server_corroborated_report_count": corroborated_count,
            "client_server_surface_match_count": sum(
                item["client_server_surface_match_count"] for item in assessments
            ),
            "client_server_surface_mismatch_count": sum(
                item["client_server_surface_mismatch_count"] for item in assessments
            ),
            "backend_internal_mismatch_report_count": sum(
                item["backend_internal_mismatch"] for item in assessments
            ),
            "mismatch_report_count": mismatch_report_count,
            "boss_encounter_exact_name_match_count": sum(
                item["boss_encounter_match_count"] for item in assessments
            ),
            "boss_encounter_difficulty_mismatch_count": sum(
                item["boss_encounter_mismatch_count"] for item in assessments
            ),
            "boss_encounter_ambiguous_count": sum(
                item["boss_encounter_ambiguous_count"] for item in assessments
            ),
            "basis": (
                "private_exact_report_scope_plus_exact_scalar_equality_plus_optional_"
                "private_exact_boss_name_join"
            ),
        },
        "cross_report_candidate": {
            "all_reports_client_server_corroborated": all_corroborated,
            "stable_client_difficulty_index_equal_across_reports": index_equal,
            "stable_client_difficulty_name_equal_across_reports": name_equal,
            "difficulty_equivalence_candidate": cross_report_candidate,
        },
        "verification": {
            "runtime_client_server_value_binding_verified": all_corroborated,
            "cross_report_client_difficulty_equality_observed": cross_report_candidate,
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
            "encounter_ids_included": False,
            "boss_names_included": False,
            "character_ids_included": False,
            "character_names_included": False,
            "difficulty_values_included": False,
            "instance_names_included": False,
            "map_values_included": False,
            "raw_payloads_included": False,
            "raw_paths_included": False,
            "request_urls_included": False,
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
        raise ValueError("difficulty value binding requires at least two persisted reports")
    return result


def _load_scoped_payloads(
    database_path: Path,
    raw_root: Path,
    *,
    endpoint_code: str,
    target_report_ids: set[str],
) -> dict[str, tuple[Mapping[str, Any], ...]]:
    if endpoint_code not in _SCOPED_ENDPOINTS:
        raise ValueError("endpoint is not a reviewed report-scoped difficulty source")
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


def _load_public_payloads(database_path: Path, raw_root: Path) -> tuple[Mapping[str, Any], ...]:
    import duckdb

    with duckdb.connect(str(database_path), read_only=True) as connection:
        rows = connection.execute(
            """
            SELECT DISTINCT sc.raw_id, ro.storage_path
            FROM source_capture AS sc
            JOIN raw_object AS ro ON ro.raw_id = sc.raw_id
            WHERE sc.endpoint_code = ?
              AND sc.http_status BETWEEN 200 AND 299
            ORDER BY sc.raw_id
            """,
            [_PUBLIC_ENDPOINT],
        ).fetchall()
    return tuple(_read_raw_payload(raw_root, storage_path, raw_id) for raw_id, storage_path in rows)


def build_difficulty_value_binding_review(
    database_path: Path,
    raw_root: Path,
) -> dict[str, Any]:
    report_ids = _target_report_ids(database_path)
    return build_difficulty_value_binding_review_from_inputs(
        report_ids=report_ids,
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
        roster_payloads=_load_scoped_payloads(
            database_path,
            raw_root,
            endpoint_code="report_combatants_roster_api",
            target_report_ids=report_ids,
        ),
        public_report_payloads=_load_public_payloads(database_path, raw_root),
    )


__all__ = [
    "DIFFICULTY_VALUE_BINDING_VERSION",
    "build_difficulty_value_binding_review",
    "build_difficulty_value_binding_review_from_inputs",
]
