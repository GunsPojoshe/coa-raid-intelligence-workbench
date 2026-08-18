from __future__ import annotations

import gzip
import json
from pathlib import Path
from typing import Any, Iterable, Mapping

from coa_workbench.analytics.current_report_read_model import (
    list_current_report_comparison_reports,
)
from coa_workbench.storage.migrations import apply_migrations

CROSS_REPORT_SOURCE_STRUCTURE_VERSION = "cross-report-source-structure-v1"


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


def _json_type(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return "unknown"


def _merge_direct_field_types(
    target: dict[str, set[str]],
    value: Mapping[str, Any],
) -> None:
    for key, child in value.items():
        target.setdefault(str(key), set()).add(_json_type(child))


def _render_field_types(value: Mapping[str, set[str]]) -> dict[str, list[str]]:
    return {key: sorted(types) for key, types in sorted(value.items())}


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
        dict(_mapping(json.loads(str(row[0])), "current_encounter_observation"))
        for row in rows
    ]


def build_cross_report_source_structure_review_from_inputs(
    *,
    source_to_canonical: Mapping[str, str],
    report_detail_payloads: Iterable[Mapping[str, Any]],
    public_report_payloads: Iterable[Mapping[str, Any]],
    encounter_rows: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    source_report_ids = set(source_to_canonical)
    canonical_report_ids = set(source_to_canonical.values())

    detail_types: dict[str, set[str]] = {}
    detail_matching_ids: set[str] = set()
    for index, payload_raw in enumerate(report_detail_payloads):
        payload = _mapping(payload_raw, f"report_detail_payloads[{index}]")
        report = payload.get("report")
        if not isinstance(report, dict):
            continue
        report_id_raw = report.get("id")
        if report_id_raw is None or isinstance(report_id_raw, bool):
            continue
        report_id = str(report_id_raw)
        if report_id not in source_report_ids:
            continue
        detail_matching_ids.add(report_id)
        _merge_direct_field_types(detail_types, report)

    public_types: dict[str, set[str]] = {}
    public_matching_ids: set[str] = set()
    public_row_count = 0
    for index, payload_raw in enumerate(public_report_payloads):
        payload = _mapping(payload_raw, f"public_report_payloads[{index}]")
        reports = payload.get("reports")
        if not isinstance(reports, list):
            continue
        for row_raw in reports:
            if not isinstance(row_raw, dict):
                continue
            public_row_count += 1
            _merge_direct_field_types(public_types, row_raw)
            report_id_raw = row_raw.get("id")
            if report_id_raw is None or isinstance(report_id_raw, bool):
                continue
            report_id = str(report_id_raw)
            if report_id in source_report_ids:
                public_matching_ids.add(report_id)

    encounter_types: dict[str, set[str]] = {}
    encounter_report_ids: set[str] = set()
    encounter_row_count = 0
    for index, row_raw in enumerate(encounter_rows):
        row = _mapping(row_raw, f"encounter_rows[{index}]")
        report_id = _identifier(row.get("report_id"), "encounter.report_id")
        if report_id not in canonical_report_ids:
            continue
        catalog = row.get("catalog_observation")
        if not isinstance(catalog, dict):
            continue
        encounter_report_ids.add(report_id)
        encounter_row_count += 1
        _merge_direct_field_types(encounter_types, catalog)

    rendered_detail = _render_field_types(detail_types)
    rendered_public = _render_field_types(public_types)
    rendered_encounter = _render_field_types(encounter_types)

    return {
        "structure_review_version": CROSS_REPORT_SOURCE_STRUCTURE_VERSION,
        "report_count": len(source_report_ids),
        "report_detail": {
            "matching_report_count": len(detail_matching_ids),
            "direct_field_types": rendered_detail,
        },
        "encounter_catalog": {
            "report_count": len(encounter_report_ids),
            "row_count": encounter_row_count,
            "direct_field_types": rendered_encounter,
        },
        "public_report_catalog": {
            "observed_row_count": public_row_count,
            "matching_report_count": len(public_matching_ids),
            "direct_field_types": rendered_public,
        },
        "difficulty_structure": {
            "report_detail_named_fields": sorted(
                key for key in rendered_detail if "difficulty" in key.casefold()
            ),
            "encounter_catalog_named_fields": sorted(
                key for key in rendered_encounter if "difficulty" in key.casefold()
            ),
            "public_report_named_fields": sorted(
                key for key in rendered_public if "difficulty" in key.casefold()
            ),
            "semantic_equivalence_verified": False,
            "numeric_cross_report_scoring_allowed": False,
            "planner_scoring_allowed": False,
        },
        "privacy": {
            "report_ids_included": False,
            "encounter_ids_included": False,
            "report_titles_included": False,
            "encounter_names_included": False,
            "difficulty_values_included": False,
            "field_names_included": True,
            "json_types_included": True,
            "raw_payloads_included": False,
            "raw_paths_included": False,
            "private_hashes_included": False,
        },
        "public_release_safe": True,
    }


def build_cross_report_source_structure_review(
    database_path: Path,
    migrations_dir: Path,
    raw_root: Path,
) -> dict[str, Any]:
    apply_migrations(database_path, migrations_dir)
    catalog = list_current_report_comparison_reports(database_path, migrations_dir)
    reports = _list(catalog.get("reports"), "catalog.reports")
    if len(reports) < 2:
        raise ValueError("cross-report source structure review requires at least two persisted reports")

    source_to_canonical: dict[str, str] = {}
    for index, item_raw in enumerate(reports):
        item = _mapping(item_raw, f"catalog.reports[{index}]")
        source_report_id = _identifier(item.get("source_report_id"), "catalog.source_report_id")
        report_id = _identifier(item.get("report_id"), "catalog.report_id")
        if source_report_id in source_to_canonical:
            raise ValueError("duplicate source report ID in comparison catalog")
        source_to_canonical[source_report_id] = report_id

    return build_cross_report_source_structure_review_from_inputs(
        source_to_canonical=source_to_canonical,
        report_detail_payloads=_load_json_payloads(
            database_path,
            raw_root,
            endpoint_code="report_detail_api",
        ),
        public_report_payloads=_load_json_payloads(
            database_path,
            raw_root,
            endpoint_code="reports_public_api",
        ),
        encounter_rows=_load_encounter_rows(database_path),
    )


__all__ = [
    "CROSS_REPORT_SOURCE_STRUCTURE_VERSION",
    "build_cross_report_source_structure_review",
    "build_cross_report_source_structure_review_from_inputs",
]
