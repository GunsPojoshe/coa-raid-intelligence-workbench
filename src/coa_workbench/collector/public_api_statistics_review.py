from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any, Mapping

PUBLIC_API_STATISTICS_REVIEW_VERSION = "public-api-statistics-shape-v1"
_DOCUMENTED_METRIC_FIELDS = (
    "avg",
    "median",
    "max",
    "min",
    "total_parses",
    "percentiles",
)


def _mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    return value


def _kind(value: Any) -> str:
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
    if isinstance(value, dict):
        return "object"
    if isinstance(value, list):
        return "array"
    return "other"


def _profile_tree(value: Any) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]], int]:
    depth_kind_counts: dict[int, Counter[str]] = defaultdict(Counter)
    object_child_counts: dict[int, list[int]] = defaultdict(list)
    array_lengths: dict[int, list[int]] = defaultdict(list)
    documented_field_counts: dict[str, int] = Counter()
    documented_field_kinds: dict[str, Counter[str]] = defaultdict(Counter)
    documented_object_depths: Counter[int] = Counter()
    max_depth = 0

    def visit(node: Any, depth: int) -> None:
        nonlocal max_depth
        max_depth = max(max_depth, depth)
        kind = _kind(node)
        depth_kind_counts[depth][kind] += 1

        if isinstance(node, dict):
            object_child_counts[depth].append(len(node))
            has_documented_field = False
            for key in _DOCUMENTED_METRIC_FIELDS:
                if key in node:
                    has_documented_field = True
                    documented_field_counts[key] += 1
                    documented_field_kinds[key][_kind(node[key])] += 1
            if has_documented_field:
                documented_object_depths[depth] += 1
            for child in node.values():
                visit(child, depth + 1)
        elif isinstance(node, list):
            array_lengths[depth].append(len(node))
            for child in node:
                visit(child, depth + 1)

    visit(value, 0)

    depth_profile: list[dict[str, Any]] = []
    for depth in sorted(depth_kind_counts):
        object_counts = object_child_counts.get(depth, [])
        list_counts = array_lengths.get(depth, [])
        depth_profile.append(
            {
                "depth": depth,
                "node_count": sum(depth_kind_counts[depth].values()),
                "kind_counts": dict(sorted(depth_kind_counts[depth].items())),
                "object_child_count_min": min(object_counts) if object_counts else None,
                "object_child_count_max": max(object_counts) if object_counts else None,
                "array_length_min": min(list_counts) if list_counts else None,
                "array_length_max": max(list_counts) if list_counts else None,
                "objects_with_documented_metric_fields": documented_object_depths.get(depth, 0),
            }
        )

    documented_fields = {
        field: {
            "occurrence_count": documented_field_counts.get(field, 0),
            "kind_counts": dict(sorted(documented_field_kinds.get(field, Counter()).items())),
        }
        for field in _DOCUMENTED_METRIC_FIELDS
    }
    return depth_profile, documented_fields, max_depth


def build_public_api_statistics_shape_review(payload: Mapping[str, Any]) -> dict[str, Any]:
    if payload.get("success") is not True:
        raise ValueError("public API statistics response was not successful")
    if "statistics" not in payload:
        raise ValueError("public API statistics response is missing statistics")

    statistics = payload["statistics"]
    if not isinstance(statistics, (dict, list)):
        raise ValueError("public API statistics must be an object or array")

    depth_profile, documented_fields, max_depth = _profile_tree(statistics)
    top_level_entry_count = len(statistics)
    documented_field_occurrence_count = sum(
        row["occurrence_count"] for row in documented_fields.values()
    )
    objects_with_documented_fields = sum(
        row["objects_with_documented_metric_fields"] for row in depth_profile
    )

    top_level_keys = tuple(sorted(str(key) for key in payload))
    return {
        "review_version": PUBLIC_API_STATISTICS_REVIEW_VERSION,
        "response": {
            "top_level_kind": "object",
            "top_level_keys": list(top_level_keys),
            "statistics_kind": _kind(statistics),
            "statistics_top_level_entry_count": top_level_entry_count,
            "statistics_max_observed_depth": max_depth,
            "depth_profile": depth_profile,
            "documented_metric_fields": documented_fields,
            "documented_metric_field_occurrence_count": documented_field_occurrence_count,
            "objects_with_documented_metric_fields": objects_with_documented_fields,
        },
        "verification": {
            "real_statistics_payload_shape_reviewed": True,
            "documented_metric_field_names_used_only_as_static_contract": True,
            "dynamic_class_spec_keys_interpreted": False,
            "statistics_normalization_ready": documented_field_occurrence_count > 0,
            "planner_scoring_allowed": False,
        },
        "privacy": {
            "query_values_included": False,
            "phase_values_included": False,
            "difficulty_values_included": False,
            "boss_ids_included": False,
            "location_values_included": False,
            "class_names_included": False,
            "spec_names_included": False,
            "dynamic_keys_included": False,
            "metric_scalar_values_included": False,
            "percentile_scalar_values_included": False,
            "raw_paths_included": False,
            "raw_payloads_included": False,
        },
        "public_release_safe": True,
    }


__all__ = [
    "PUBLIC_API_STATISTICS_REVIEW_VERSION",
    "build_public_api_statistics_shape_review",
]
