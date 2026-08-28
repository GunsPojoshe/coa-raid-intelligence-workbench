from __future__ import annotations

from typing import Any, Mapping

from coa_workbench.analytics.cross_report_benchmark import CROSS_REPORT_BENCHMARK_VERSION

CROSS_REPORT_REVIEW_VERSION = "cross-report-structural-review-v1"


def _int(value: Any, label: str) -> int:
    if isinstance(value, bool):
        raise ValueError(f"{label} must be an integer")
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be an integer") from exc


def _list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"{label} must be an array")
    return value


def _mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    return value


def build_public_cross_report_review(
    model: Mapping[str, Any],
    *,
    deterministic_requery_equal: bool,
) -> dict[str, Any]:
    """Return only scalar-safe evidence about the private cross-report structural model."""
    if model.get("benchmark_version") != CROSS_REPORT_BENCHMARK_VERSION:
        raise ValueError("unexpected cross-report benchmark version")
    if model.get("local_private_payload") is not True:
        raise ValueError("cross-report benchmark must be explicitly local/private")
    if model.get("public_release_safe") is not False:
        raise ValueError("cross-report benchmark must not claim public-release safety")

    interpretation = _mapping(model.get("interpretation"), "interpretation")
    if interpretation.get("structural_peer_alignment_only") is not True:
        raise ValueError("cross-report benchmark must remain structural-only")
    if interpretation.get("difficulty_equivalence_verified") is not False:
        raise ValueError("difficulty equivalence was unexpectedly promoted")
    if interpretation.get("cross_report_player_identity_verified") is not False:
        raise ValueError("cross-report player identity was unexpectedly promoted")
    if interpretation.get("numeric_cross_report_scoring_allowed") is not False:
        raise ValueError("numeric cross-report scoring was unexpectedly enabled")
    if interpretation.get("mechanic_semantics_verified") is not False:
        raise ValueError("mechanic semantics were unexpectedly promoted")
    if interpretation.get("planner_scoring_allowed") is not False:
        raise ValueError("planner scoring was unexpectedly enabled")

    cohorts = _list(model.get("cohorts"), "cohorts")
    eligible_count = 0
    ambiguous_count = 0
    cohort_profile_count = 0
    cohort_ranked_row_count = 0
    all_structural_only = True
    for index, raw_cohort in enumerate(cohorts):
        cohort = _mapping(raw_cohort, f"cohorts[{index}]")
        if _int(cohort.get("distinct_report_count"), "distinct_report_count") < 2:
            raise ValueError("cross-report cohort has fewer than two distinct reports")
        status = str(cohort.get("status") or "")
        if status == "eligible_structural_peer":
            eligible_count += 1
        elif status == "ambiguous_repeated_profile_per_report":
            ambiguous_count += 1
        else:
            raise ValueError(f"unexpected cross-report cohort status: {status!r}")
        if cohort.get("difficulty_equivalence_verified") is not False:
            all_structural_only = False
        if cohort.get("cross_report_player_identity_verified") is not False:
            all_structural_only = False
        if cohort.get("numeric_cross_report_scoring_allowed") is not False:
            all_structural_only = False
        if cohort.get("planner_scoring_allowed") is not False:
            all_structural_only = False
        profiles = _list(cohort.get("profiles"), "cohort.profiles")
        cohort_profile_count += len(profiles)
        cohort_ranked_row_count += _int(
            cohort.get("ranked_player_row_count"),
            "cohort.ranked_player_row_count",
        )

    if eligible_count != _int(model.get("eligible_peer_cohort_count"), "eligible count"):
        raise ValueError("eligible cohort count disagrees with model summary")
    if ambiguous_count != _int(model.get("ambiguous_peer_cohort_count"), "ambiguous count"):
        raise ValueError("ambiguous cohort count disagrees with model summary")
    if cohort_profile_count < _int(model.get("eligible_profile_count"), "eligible profiles"):
        raise ValueError("eligible profile count exceeds candidate cohort profiles")
    if cohort_ranked_row_count < _int(
        model.get("eligible_ranked_player_row_count"),
        "eligible ranked rows",
    ):
        raise ValueError("eligible ranked row count exceeds candidate cohort rows")

    return {
        "schema_version": 1,
        "review_version": CROSS_REPORT_REVIEW_VERSION,
        "benchmark_version": CROSS_REPORT_BENCHMARK_VERSION,
        "status": "completed",
        "report_count": _int(model.get("report_count"), "report_count"),
        "input_profile_count": _int(model.get("input_profile_count"), "input_profile_count"),
        "candidate_peer_cohort_count": len(cohorts),
        "eligible_peer_cohort_count": eligible_count,
        "ambiguous_peer_cohort_count": ambiguous_count,
        "single_report_profile_group_count": _int(
            model.get("single_report_profile_group_count"),
            "single_report_profile_group_count",
        ),
        "eligible_profile_count": _int(
            model.get("eligible_profile_count"),
            "eligible_profile_count",
        ),
        "eligible_ranked_player_row_count": _int(
            model.get("eligible_ranked_player_row_count"),
            "eligible_ranked_player_row_count",
        ),
        "profiles_without_zone": _int(model.get("profiles_without_zone"), "profiles_without_zone"),
        "profiles_without_encounter_name": _int(
            model.get("profiles_without_encounter_name"),
            "profiles_without_encounter_name",
        ),
        "verification": {
            "deterministic_requery_equal": bool(deterministic_requery_equal),
            "all_candidate_cohorts_have_multiple_reports": True,
            "all_cohorts_remain_structural_only": all_structural_only,
            "difficulty_equivalence_verified": False,
            "cross_report_player_identity_verified": False,
            "numeric_cross_report_scoring_allowed": False,
            "mechanic_semantics_verified": False,
            "planner_scoring_allowed": False,
        },
        "privacy": {
            "local_private_model_included": False,
            "report_ids_included": False,
            "encounter_ids_included": False,
            "character_ids_included": False,
            "character_names_included": False,
            "zone_values_included": False,
            "encounter_names_included": False,
            "metric_values_included": False,
            "perspective_values_included": False,
            "numeric_player_totals_included": False,
            "private_fingerprints_included": False,
        },
    }


__all__ = ["CROSS_REPORT_REVIEW_VERSION", "build_public_cross_report_review"]
