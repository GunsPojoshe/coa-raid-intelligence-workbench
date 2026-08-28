from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, Mapping

from coa_workbench.analytics.current_report_read_model import (
    CURRENT_REPORT_COMPARISON_READ_MODEL_VERSION,
    build_current_report_comparison_read_model,
    list_current_report_comparison_reports,
)

CROSS_REPORT_BENCHMARK_VERSION = "cross-report-structural-benchmark-v1"


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


def _text(value: Any) -> str | None:
    if value is None:
        return None
    result = str(value)
    return result if result else None


def build_cross_report_structural_benchmark_from_models(
    models: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    """Group exact report profiles into structural cross-report peer cohorts.

    This layer intentionally does not calculate cross-report player scores, percentiles, or grades.
    A peer cohort is keyed only by exact observed zone, encounter name, metric and perspective.
    Difficulty equivalence and cross-report player identity remain unverified boundaries.
    """
    prepared = tuple(models)
    if len(prepared) < 2:
        raise ValueError("cross-report structural benchmark requires at least two reports")

    groups: dict[tuple[str, str, str, str | None], list[dict[str, Any]]] = {}
    report_ids: set[str] = set()
    total_profile_count = 0
    profiles_without_zone = 0
    profiles_without_encounter_name = 0

    for model_index, model_raw in enumerate(prepared):
        model = _mapping(model_raw, f"models[{model_index}]")
        if model.get("read_model_version") != CURRENT_REPORT_COMPARISON_READ_MODEL_VERSION:
            raise ValueError("unexpected current-report comparison read-model version")
        if model.get("local_private_payload") is not True:
            raise ValueError("cross-report input must be explicitly local/private")
        if model.get("public_release_safe") is not False:
            raise ValueError("cross-report input must not claim public-release safety")
        interpretation = _mapping(model.get("interpretation"), "interpretation")
        if interpretation.get("planner_scoring_allowed") is not False:
            raise ValueError("cross-report input unexpectedly allows planner scoring")
        if interpretation.get("mechanic_semantics_verified") is not False:
            raise ValueError("cross-report input unexpectedly promotes mechanic semantics")

        report = _mapping(model.get("report"), "report")
        report_id = _identifier(report.get("report_id"), "report.report_id")
        source_report_id = _identifier(
            report.get("source_report_id"),
            "report.source_report_id",
        )
        if report_id in report_ids:
            raise ValueError("cross-report input contains duplicate canonical report IDs")
        report_ids.add(report_id)
        zone = _text(report.get("zone"))

        profiles = _list(model.get("throughput_profiles"), "throughput_profiles")
        total_profile_count += len(profiles)
        for profile_index, profile_raw in enumerate(profiles):
            profile = _mapping(
                profile_raw,
                f"models[{model_index}].throughput_profiles[{profile_index}]",
            )
            if profile.get("planner_scoring_allowed") is not False:
                raise ValueError("throughput profile unexpectedly allows planner scoring")
            if zone is None:
                profiles_without_zone += 1
                continue
            encounter_name = _text(profile.get("encounter_name"))
            if encounter_name is None:
                profiles_without_encounter_name += 1
                continue
            metric = _identifier(profile.get("metric"), "throughput.metric")
            perspective = _text(profile.get("perspective"))
            source_encounter_id = _identifier(
                profile.get("source_encounter_id"),
                "throughput.source_encounter_id",
            )
            rows = _list(profile.get("rows"), "throughput.rows")
            key = (zone, encounter_name, metric, perspective)
            groups.setdefault(key, []).append(
                {
                    "report_id": report_id,
                    "source_report_id": source_report_id,
                    "source_encounter_id": source_encounter_id,
                    "request_index": int(profile["request_index"]),
                    "rows": rows,
                }
            )

    cohorts: list[dict[str, Any]] = []
    single_report_group_count = 0
    ambiguous_group_count = 0
    eligible_group_count = 0
    eligible_profile_count = 0
    eligible_ranked_row_count = 0

    for key in sorted(groups, key=lambda item: (item[0], item[1], item[2], item[3] or "")):
        zone, encounter_name, metric, perspective = key
        profiles = groups[key]
        by_report: dict[str, list[dict[str, Any]]] = {}
        for profile in profiles:
            by_report.setdefault(str(profile["report_id"]), []).append(profile)
        distinct_report_count = len(by_report)
        if distinct_report_count < 2:
            single_report_group_count += 1
            continue

        repeated_report_profile = any(len(items) != 1 for items in by_report.values())
        if repeated_report_profile:
            status = "ambiguous_repeated_profile_per_report"
            ambiguous_group_count += 1
        else:
            status = "eligible_structural_peer"
            eligible_group_count += 1
            eligible_profile_count += len(profiles)
            eligible_ranked_row_count += sum(len(profile["rows"]) for profile in profiles)

        cohorts.append(
            {
                "zone": zone,
                "encounter_name": encounter_name,
                "metric": metric,
                "perspective": perspective,
                "status": status,
                "distinct_report_count": distinct_report_count,
                "profile_count": len(profiles),
                "ranked_player_row_count": sum(len(profile["rows"]) for profile in profiles),
                "profiles": sorted(
                    profiles,
                    key=lambda item: (
                        str(item["report_id"]),
                        str(item["source_encounter_id"]),
                        int(item["request_index"]),
                    ),
                ),
                "encounter_identity_basis": "exact_zone_plus_exact_encounter_name",
                "profile_identity_basis": "exact_metric_plus_exact_perspective",
                "difficulty_equivalence_verified": False,
                "cross_report_player_identity_verified": False,
                "numeric_cross_report_scoring_allowed": False,
                "planner_scoring_allowed": False,
            }
        )

    return {
        "benchmark_version": CROSS_REPORT_BENCHMARK_VERSION,
        "report_count": len(report_ids),
        "input_profile_count": total_profile_count,
        "candidate_peer_cohort_count": len(cohorts),
        "eligible_peer_cohort_count": eligible_group_count,
        "ambiguous_peer_cohort_count": ambiguous_group_count,
        "single_report_profile_group_count": single_report_group_count,
        "eligible_profile_count": eligible_profile_count,
        "eligible_ranked_player_row_count": eligible_ranked_row_count,
        "profiles_without_zone": profiles_without_zone,
        "profiles_without_encounter_name": profiles_without_encounter_name,
        "cohorts": cohorts,
        "interpretation": {
            "structural_peer_alignment_only": True,
            "difficulty_equivalence_verified": False,
            "cross_report_player_identity_verified": False,
            "numeric_cross_report_scoring_allowed": False,
            "mechanic_semantics_verified": False,
            "planner_scoring_allowed": False,
        },
        "local_private_payload": True,
        "public_release_safe": False,
    }


def build_cross_report_structural_benchmark(
    database_path: Path,
    migrations_dir: Path,
) -> dict[str, Any]:
    catalog = list_current_report_comparison_reports(database_path, migrations_dir)
    reports = _list(catalog.get("reports"), "catalog.reports")
    if len(reports) < 2:
        raise ValueError("cross-report structural benchmark requires at least two persisted reports")
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
    return build_cross_report_structural_benchmark_from_models(models)


__all__ = [
    "CROSS_REPORT_BENCHMARK_VERSION",
    "build_cross_report_structural_benchmark",
    "build_cross_report_structural_benchmark_from_models",
]
