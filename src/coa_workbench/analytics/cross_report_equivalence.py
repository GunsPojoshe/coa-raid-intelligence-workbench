from __future__ import annotations

import gzip
import json
from pathlib import Path
from typing import Any, Iterable, Mapping

from coa_workbench.analytics.cross_report_benchmark import (
    build_cross_report_structural_benchmark_from_models,
)
from coa_workbench.analytics.current_report_read_model import (
    build_current_report_comparison_read_model,
    list_current_report_comparison_reports,
)
from coa_workbench.storage.migrations import apply_migrations

CROSS_REPORT_EQUIVALENCE_REVIEW_VERSION = "cross-report-equivalence-review-v1"


def _mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    return value


def _list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"{label} must be an array")
    return value


def _identifier(value: Any, label: str) -> str:
    if value is None or isinstance(value, bool) or str(value) == "":
        raise ValueError(f"{label} must be a non-empty identifier")
    return str(value)


def _private_label(value: Any) -> str | None:
    if value is None or isinstance(value, bool):
        return None
    if not isinstance(value, (str, int)):
        return None
    prepared = str(value)
    return prepared if prepared else None


def _collect_detail_difficulties(
    payloads: Iterable[Mapping[str, Any]],
    report_ids: set[str],
) -> dict[str, set[str]]:
    result = {report_id: set() for report_id in report_ids}
    for index, payload_raw in enumerate(payloads):
        payload = _mapping(payload_raw, f"report_detail_payloads[{index}]")
        report = payload.get("report")
        if not isinstance(report, dict):
            continue
        report_id_raw = report.get("id")
        if report_id_raw is None or isinstance(report_id_raw, bool):
            continue
        report_id = str(report_id_raw)
        if report_id not in result:
            continue
        label = _private_label(report.get("difficulty"))
        if label is not None:
            result[report_id].add(label)
    return result


def _collect_public_difficulties(
    payloads: Iterable[Mapping[str, Any]],
    report_ids: set[str],
) -> dict[str, set[str]]:
    result = {report_id: set() for report_id in report_ids}
    for index, payload_raw in enumerate(payloads):
        payload = _mapping(payload_raw, f"public_report_payloads[{index}]")
        reports = payload.get("reports")
        if not isinstance(reports, list):
            continue
        for row_raw in reports:
            if not isinstance(row_raw, dict):
                continue
            report_id_raw = row_raw.get("id")
            if report_id_raw is None or isinstance(report_id_raw, bool):
                continue
            report_id = str(report_id_raw)
            if report_id not in result:
                continue
            label = _private_label(row_raw.get("highest_difficulty"))
            if label is not None:
                result[report_id].add(label)
    return result


def _report_encounter_index_from_rows(
    rows: Iterable[Mapping[str, Any]],
) -> dict[str, dict[str, set[str]]]:
    result: dict[str, dict[str, set[str]]] = {}
    for index, row_raw in enumerate(rows):
        row = _mapping(row_raw, f"encounter_rows[{index}]")
        report_id = _identifier(row.get("report_id"), "encounter.report_id")
        source_encounter_id = _identifier(
            row.get("source_encounter_id"),
            "encounter.source_encounter_id",
        )
        normalized = _mapping(row.get("normalized"), "encounter.normalized")
        encounter_name = _private_label(normalized.get("name"))
        if encounter_name is None:
            continue
        result.setdefault(report_id, {}).setdefault(encounter_name, set()).add(
            source_encounter_id
        )
    return result


def build_cross_report_equivalence_review_from_inputs(
    *,
    models: Iterable[Mapping[str, Any]],
    report_detail_payloads: Iterable[Mapping[str, Any]],
    public_report_payloads: Iterable[Mapping[str, Any]],
    encounter_index: Mapping[str, Mapping[str, set[str]]],
) -> dict[str, Any]:
    prepared = tuple(models)
    structural = build_cross_report_structural_benchmark_from_models(prepared)

    source_to_canonical: dict[str, str] = {}
    source_report_ids: set[str] = set()
    for index, model_raw in enumerate(prepared):
        model = _mapping(model_raw, f"models[{index}]")
        report = _mapping(model.get("report"), f"models[{index}].report")
        source_report_id = _identifier(
            report.get("source_report_id"),
            "report.source_report_id",
        )
        canonical_report_id = _identifier(report.get("report_id"), "report.report_id")
        if source_report_id in source_to_canonical:
            raise ValueError("duplicate source report ID in equivalence review")
        source_to_canonical[source_report_id] = canonical_report_id
        source_report_ids.add(source_report_id)

    detail = _collect_detail_difficulties(report_detail_payloads, source_report_ids)
    public = _collect_public_difficulties(public_report_payloads, source_report_ids)

    verified_labels: dict[str, str] = {}
    detail_observed_count = 0
    public_observed_count = 0
    cross_surface_match_count = 0
    cross_surface_mismatch_count = 0
    ambiguous_report_count = 0

    for source_report_id in sorted(source_report_ids):
        detail_values = detail[source_report_id]
        public_values = public[source_report_id]
        if len(detail_values) == 1:
            detail_observed_count += 1
        if len(public_values) == 1:
            public_observed_count += 1
        if len(detail_values) > 1 or len(public_values) > 1:
            ambiguous_report_count += 1
            continue
        if len(detail_values) == 1 and len(public_values) == 1:
            detail_value = next(iter(detail_values))
            public_value = next(iter(public_values))
            if detail_value == public_value:
                cross_surface_match_count += 1
                verified_labels[source_report_id] = detail_value
            else:
                cross_surface_mismatch_count += 1

    eligible_cohorts = [
        _mapping(item, "structural.cohorts[]")
        for item in _list(structural.get("cohorts"), "structural.cohorts")
        if _mapping(item, "structural.cohorts[]").get("status")
        == "eligible_structural_peer"
    ]

    difficulty_verified_cohort_count = 0
    encounter_verified_cohort_count = 0
    encounter_non_unique_cohort_count = 0

    for cohort in eligible_cohorts:
        encounter_name = _identifier(
            cohort.get("encounter_name"),
            "cohort.encounter_name",
        )
        profiles = [
            _mapping(item, "cohort.profiles[]")
            for item in _list(cohort.get("profiles"), "cohort.profiles")
        ]
        labels: list[str] = []
        difficulty_complete = True
        encounter_unique = True

        for profile in profiles:
            source_report_id = _identifier(
                profile.get("source_report_id"),
                "profile.source_report_id",
            )
            canonical_report_id = source_to_canonical.get(source_report_id)
            if canonical_report_id is None:
                raise ValueError("structural cohort references unknown report")
            label = verified_labels.get(source_report_id)
            if label is None:
                difficulty_complete = False
            else:
                labels.append(label)

            source_encounter_id = _identifier(
                profile.get("source_encounter_id"),
                "profile.source_encounter_id",
            )
            matching_ids = set(
                encounter_index.get(canonical_report_id, {}).get(encounter_name, set())
            )
            if matching_ids != {source_encounter_id}:
                encounter_unique = False

        difficulty_verified = (
            difficulty_complete
            and len(labels) == len(profiles)
            and len(set(labels)) == 1
        )
        if difficulty_verified:
            difficulty_verified_cohort_count += 1

        if not encounter_unique:
            encounter_non_unique_cohort_count += 1
        if difficulty_verified and encounter_unique:
            encounter_verified_cohort_count += 1

    eligible_count = len(eligible_cohorts)
    all_difficulty_verified = (
        eligible_count > 0 and difficulty_verified_cohort_count == eligible_count
    )
    all_encounter_verified = (
        eligible_count > 0 and encounter_verified_cohort_count == eligible_count
    )

    return {
        "review_version": CROSS_REPORT_EQUIVALENCE_REVIEW_VERSION,
        "status": (
            "verified"
            if all_difficulty_verified and all_encounter_verified
            else "insufficient_evidence"
        ),
        "report_count": len(source_report_ids),
        "difficulty_evidence": {
            "report_detail_difficulty_observed_count": detail_observed_count,
            "public_highest_difficulty_observed_count": public_observed_count,
            "cross_surface_match_count": cross_surface_match_count,
            "cross_surface_mismatch_count": cross_surface_mismatch_count,
            "ambiguous_report_count": ambiguous_report_count,
            "verified_report_count": len(verified_labels),
            "distinct_verified_private_label_count": len(set(verified_labels.values())),
            "corroboration_basis": (
                "exact_report_id_link_plus_exact_report_detail_difficulty_"
                "equals_public_highest_difficulty"
            ),
        },
        "cohort_evidence": {
            "eligible_structural_peer_cohort_count": eligible_count,
            "difficulty_verified_cohort_count": difficulty_verified_cohort_count,
            "encounter_equivalence_verified_cohort_count": encounter_verified_cohort_count,
            "encounter_non_unique_cohort_count": encounter_non_unique_cohort_count,
            "encounter_identity_basis": (
                "exact_zone_plus_exact_encounter_name_plus_unique_encounter_per_report_"
                "plus_corroborated_equal_difficulty"
            ),
        },
        "verification": {
            "all_eligible_cohorts_difficulty_equivalence_verified": all_difficulty_verified,
            "all_eligible_cohorts_encounter_equivalence_verified": all_encounter_verified,
            "cross_report_player_identity_verified": False,
            "fight_duration_comparison_unit_verified": False,
            "numeric_cross_report_scoring_allowed": False,
            "mechanic_semantics_verified": False,
            "planner_scoring_allowed": False,
        },
        "privacy": {
            "report_ids_included": False,
            "encounter_ids_included": False,
            "zone_values_included": False,
            "encounter_names_included": False,
            "difficulty_values_included": False,
            "character_ids_included": False,
            "character_names_included": False,
            "raw_payloads_included": False,
            "raw_paths_included": False,
            "private_hashes_included": False,
        },
        "public_release_safe": True,
    }


def _load_json_payloads(
    database_path: Path,
    raw_root: Path,
    *,
    endpoint_code: str,
) -> list[dict[str, Any]]:
    import duckdb

    with duckdb.connect(str(database_path), read_only=True) as connection:
        rows = connection.execute(
            """
            SELECT DISTINCT ro.raw_id, ro.storage_path
            FROM source_capture AS sc
            JOIN raw_object AS ro ON ro.raw_id = sc.raw_id
            WHERE sc.endpoint_code = ?
              AND sc.http_status BETWEEN 200 AND 299
            ORDER BY ro.raw_id
            """,
            [endpoint_code],
        ).fetchall()

    root = raw_root.resolve()
    payloads: list[dict[str, Any]] = []
    for raw_id, storage_path_raw in rows:
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
        if isinstance(payload, dict):
            payloads.append(payload)
    return payloads


def _load_encounter_rows(database_path: Path) -> list[dict[str, Any]]:
    import duckdb

    with duckdb.connect(str(database_path), read_only=True) as connection:
        rows = connection.execute(
            """
            SELECT entity_json
            FROM canonical_entity_observation
            WHERE entity_type = 'current_encounter_observation'
              AND trust_status = 'observed'
            ORDER BY observation_id
            """
        ).fetchall()
    return [
        _mapping(json.loads(str(row[0])), "current_encounter_observation")
        for row in rows
    ]


def build_cross_report_equivalence_review(
    database_path: Path,
    migrations_dir: Path,
    raw_root: Path,
) -> dict[str, Any]:
    apply_migrations(database_path, migrations_dir)
    catalog = list_current_report_comparison_reports(database_path, migrations_dir)
    reports = _list(catalog.get("reports"), "catalog.reports")
    if len(reports) < 2:
        raise ValueError("cross-report equivalence review requires at least two persisted reports")

    models = [
        build_current_report_comparison_read_model(
            database_path,
            migrations_dir,
            report_id=_identifier(
                _mapping(item, "catalog.reports[]").get("report_id"),
                "catalog.report_id",
            ),
        )
        for item in reports
    ]
    detail_payloads = _load_json_payloads(
        database_path,
        raw_root,
        endpoint_code="report_detail_api",
    )
    public_payloads = _load_json_payloads(
        database_path,
        raw_root,
        endpoint_code="reports_public_api",
    )
    encounter_index = _report_encounter_index_from_rows(_load_encounter_rows(database_path))
    return build_cross_report_equivalence_review_from_inputs(
        models=models,
        report_detail_payloads=detail_payloads,
        public_report_payloads=public_payloads,
        encounter_index=encounter_index,
    )


__all__ = [
    "CROSS_REPORT_EQUIVALENCE_REVIEW_VERSION",
    "build_cross_report_equivalence_review",
    "build_cross_report_equivalence_review_from_inputs",
]
