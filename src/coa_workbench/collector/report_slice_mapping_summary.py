from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_SUMMARY_SCHEMA_VERSION = 1
_MAPPING_REVIEW_KIND = "observed_report_slice_mapping_review"
_STRUCTURAL_REVIEW_KIND = "observed_report_slice_structural_review"
_ENTITIES = ("report", "encounter", "actor", "aura_event")


def _generated_at() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _load_object(path: Path, *, label: str) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{label} must contain a JSON object")
    return payload


def _required_object(value: object, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be an object")
    return value


def _required_list(value: object, field_name: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be an array")
    return value


def _required_string(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field_name} must be a non-empty string")
    return value


def _required_integer(value: object, field_name: str, *, minimum: int = 0) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < minimum:
        raise ValueError(f"{field_name} must be an integer greater than or equal to {minimum}")
    return value


def _safe_type_counts(value: object) -> dict[str, int]:
    if not isinstance(value, dict):
        return {}
    result: dict[str, int] = {}
    for key, count in value.items():
        if isinstance(key, str) and isinstance(count, int) and not isinstance(count, bool):
            result[key] = count
    return dict(sorted(result.items()))


def _safe_string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return sorted({item for item in value if isinstance(item, str)})


def _safe_score(value: object) -> float:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    return 0.0


def _normalize_collection_path(path: str) -> str:
    if path == "/":
        return path
    raw = path[1:] if path.startswith("/") else path
    segments = raw.split("/")
    normalized = ["*" if segment.isdecimal() else segment for segment in segments]
    return "/" + "/".join(normalized)


def _direct_root_child(path: str) -> str | None:
    if not path.startswith("/") or path == "/":
        return None
    remainder = path[1:]
    return remainder if remainder and "/" not in remainder else None


@dataclass(slots=True)
class _CandidateAggregate:
    path: str
    source_candidate_count: int = 0
    item_count_total: int = 0
    item_count_min: int | None = None
    item_count_max: int | None = None
    object_item_count_total: int = 0
    object_item_count_min: int | None = None
    object_item_count_max: int | None = None
    observed_keys: set[str] = field(default_factory=set)
    entity_scores: dict[str, float] = field(
        default_factory=lambda: {entity: 0.0 for entity in _ENTITIES}
    )
    matched_hints: dict[str, set[str]] = field(
        default_factory=lambda: {entity: set() for entity in _ENTITIES}
    )

    def observe(self, candidate: dict[str, Any]) -> None:
        item_count = _required_integer(candidate.get("item_count"), "candidate.item_count")
        object_count = _required_integer(
            candidate.get("object_item_count"),
            "candidate.object_item_count",
        )
        self.source_candidate_count += 1
        self.item_count_total += item_count
        self.item_count_min = (
            item_count if self.item_count_min is None else min(self.item_count_min, item_count)
        )
        self.item_count_max = (
            item_count if self.item_count_max is None else max(self.item_count_max, item_count)
        )
        self.object_item_count_total += object_count
        self.object_item_count_min = (
            object_count
            if self.object_item_count_min is None
            else min(self.object_item_count_min, object_count)
        )
        self.object_item_count_max = (
            object_count
            if self.object_item_count_max is None
            else max(self.object_item_count_max, object_count)
        )
        self.observed_keys.update(_safe_string_list(candidate.get("observed_keys")))

        raw_scores = candidate.get("entity_scores")
        if isinstance(raw_scores, dict):
            for entity in _ENTITIES:
                self.entity_scores[entity] = max(
                    self.entity_scores[entity],
                    _safe_score(raw_scores.get(entity)),
                )

        raw_hints = candidate.get("matched_hints")
        if isinstance(raw_hints, dict):
            for entity in _ENTITIES:
                self.matched_hints[entity].update(_safe_string_list(raw_hints.get(entity)))

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "source_candidate_count": self.source_candidate_count,
            "item_count_total": self.item_count_total,
            "item_count_min": self.item_count_min,
            "item_count_max": self.item_count_max,
            "object_item_count_total": self.object_item_count_total,
            "object_item_count_min": self.object_item_count_min,
            "object_item_count_max": self.object_item_count_max,
            "observed_keys": sorted(self.observed_keys),
            "entity_scores": {
                entity: self.entity_scores[entity] for entity in _ENTITIES
            },
            "matched_hints": {
                entity: sorted(self.matched_hints[entity]) for entity in _ENTITIES
            },
            "semantic_status": "unverified_candidate",
        }


def _endpoint_index(values: object, *, label: str) -> dict[str, dict[str, Any]]:
    rows = _required_list(values, label)
    result: dict[str, dict[str, Any]] = {}
    for raw in rows:
        row = _required_object(raw, f"{label}[]")
        endpoint_kind = _required_string(row.get("endpoint_kind"), "endpoint_kind")
        if endpoint_kind in result:
            raise ValueError(f"duplicate endpoint kind in {label}: {endpoint_kind}")
        result[endpoint_kind] = row
    return result


def _aggregate_candidates(values: object) -> list[dict[str, Any]]:
    rows = _required_list(values, "candidate_collections")
    aggregates: dict[str, _CandidateAggregate] = {}
    for raw in rows:
        candidate = _required_object(raw, "candidate_collections[]")
        source_path = _required_string(candidate.get("path"), "candidate.path")
        path = _normalize_collection_path(source_path)
        aggregates.setdefault(path, _CandidateAggregate(path=path)).observe(candidate)

    result = [aggregate.to_dict() for aggregate in aggregates.values()]
    result.sort(
        key=lambda row: (
            -max(row["entity_scores"].values(), default=0.0),
            -row["object_item_count_total"],
            row["path"],
        )
    )
    return result


def _candidate_shortlists(
    candidates: list[dict[str, Any]],
    *,
    limit: int,
) -> dict[str, list[dict[str, Any]]]:
    result: dict[str, list[dict[str, Any]]] = {}
    for entity in _ENTITIES:
        ranked = [
            candidate
            for candidate in candidates
            if candidate["entity_scores"][entity] > 0
            and candidate["object_item_count_total"] > 0
        ]
        ranked.sort(
            key=lambda row: (
                -row["entity_scores"][entity],
                -row["object_item_count_total"],
                row["path"],
            )
        )
        result[entity] = [
            {
                "rank": index,
                "path": row["path"],
                "score": row["entity_scores"][entity],
                "matched_hints": row["matched_hints"][entity],
                "source_candidate_count": row["source_candidate_count"],
                "item_count_total": row["item_count_total"],
                "object_item_count_total": row["object_item_count_total"],
                "observed_keys": row["observed_keys"],
                "semantic_status": "unverified_candidate",
            }
            for index, row in enumerate(ranked[:limit], start=1)
        ]
    return result


def _top_level_fields(values: object) -> list[dict[str, Any]]:
    rows = _required_list(values, "mapping.field_shapes")
    result: list[dict[str, Any]] = []
    for raw in rows:
        shape = _required_object(raw, "mapping.field_shapes[]")
        path = _required_string(shape.get("path"), "field_shape.path")
        name = _direct_root_child(path)
        if name is None:
            continue
        type_counts = _safe_type_counts(shape.get("type_counts"))
        result.append(
            {
                "name": name,
                "path": path,
                "occurrence_count": shape.get("occurrence_count"),
                "types": sorted(type_counts),
                "type_counts": type_counts,
                "nullable": shape.get("nullable") is True,
                "is_array": isinstance(shape.get("array"), dict),
                "is_object": isinstance(shape.get("object"), dict),
            }
        )
    return sorted(result, key=lambda row: row["path"])


def summarize_observed_report_slice_mapping_review(
    mapping_review_path: Path,
    structural_review_path: Path,
    *,
    max_candidates_per_entity: int = 8,
) -> dict[str, Any]:
    """Build a compact scalar-free scope-selection summary for exact report-slice reviews."""
    if max_candidates_per_entity < 1:
        raise ValueError("max_candidates_per_entity must be positive")

    mapping = _load_object(mapping_review_path, label="mapping review")
    structural = _load_object(structural_review_path, label="structural review")
    if mapping.get("review_kind") != _MAPPING_REVIEW_KIND:
        raise ValueError("unsupported report slice mapping review kind")
    if structural.get("review_kind") != _STRUCTURAL_REVIEW_KIND:
        raise ValueError("unsupported report slice structural review kind")

    mapping_summary = _required_object(mapping.get("summary"), "mapping.summary")
    structural_summary = _required_object(structural.get("summary"), "structural.summary")
    for label, summary in (("mapping", mapping_summary), ("structural", structural_summary)):
        if summary.get("contains_source_scalar_values") is not False:
            raise ValueError(f"{label} privacy gate is not satisfied")
        if summary.get("normalization_allowed") is not False:
            raise ValueError(f"{label} normalization gate is not satisfied")
    if mapping_summary.get("all_archives_consistent") is not True:
        raise ValueError("mapping archive consistency gate is not satisfied")
    if structural_summary.get("all_archives_consistent") is not True:
        raise ValueError("structural archive consistency gate is not satisfied")

    mapping_endpoints = _endpoint_index(mapping.get("endpoints"), label="mapping.endpoints")
    structural_endpoints = _endpoint_index(
        structural.get("endpoints"),
        label="structural.endpoints",
    )
    if set(mapping_endpoints) != set(structural_endpoints):
        raise ValueError("mapping and structural endpoint sets do not match")

    endpoints: list[dict[str, Any]] = []
    total_aggregated_candidates = 0
    total_shortlist_rows = 0
    for endpoint_kind in sorted(mapping_endpoints):
        mapping_endpoint = mapping_endpoints[endpoint_kind]
        structural_endpoint = structural_endpoints[endpoint_kind]
        for field_name in (
            "route_template",
            "payload_hash",
            "schema_fingerprint",
            "top_level_kind",
            "top_level_keys",
        ):
            if mapping_endpoint.get(field_name) != structural_endpoint.get(field_name):
                raise ValueError(
                    f"mapping and structural {field_name} do not match for {endpoint_kind}"
                )
        if mapping_endpoint.get("review_status") != "candidate":
            raise ValueError(f"endpoint {endpoint_kind} is not a candidate mapping review")

        mapping_endpoint_summary = _required_object(
            mapping_endpoint.get("summary"),
            f"mapping endpoint summary {endpoint_kind}",
        )
        source_candidate_count = len(
            _required_list(
                structural_endpoint.get("candidate_collections"),
                f"structural candidate collections {endpoint_kind}",
            )
        )
        if mapping_endpoint_summary.get("candidate_collection_count") != source_candidate_count:
            raise ValueError(f"candidate collection count mismatch for {endpoint_kind}")

        aggregated = _aggregate_candidates(structural_endpoint.get("candidate_collections"))
        shortlists = _candidate_shortlists(
            aggregated,
            limit=max_candidates_per_entity,
        )
        shortlist_count = sum(len(rows) for rows in shortlists.values())
        total_aggregated_candidates += len(aggregated)
        total_shortlist_rows += shortlist_count
        endpoints.append(
            {
                "endpoint_kind": endpoint_kind,
                "route_template": mapping_endpoint["route_template"],
                "payload_hash": mapping_endpoint["payload_hash"],
                "schema_fingerprint": mapping_endpoint["schema_fingerprint"],
                "top_level_kind": mapping_endpoint["top_level_kind"],
                "top_level_keys": mapping_endpoint["top_level_keys"],
                "review_status": "candidate",
                "scope": mapping_endpoint.get("scope"),
                "top_level_fields": _top_level_fields(mapping_endpoint.get("field_shapes")),
                "candidate_shortlists": shortlists,
                "aggregated_candidate_collections": aggregated,
                "summary": {
                    "field_path_count": mapping_endpoint_summary.get("field_path_count"),
                    "node_occurrence_count": mapping_endpoint_summary.get(
                        "node_occurrence_count"
                    ),
                    "numeric_map_path_count": mapping_endpoint_summary.get(
                        "numeric_map_path_count"
                    ),
                    "nullable_path_count": mapping_endpoint_summary.get("nullable_path_count"),
                    "array_path_count": mapping_endpoint_summary.get("array_path_count"),
                    "object_path_count": mapping_endpoint_summary.get("object_path_count"),
                    "source_candidate_collection_count": source_candidate_count,
                    "aggregated_candidate_path_count": len(aggregated),
                    "shortlist_row_count": shortlist_count,
                },
            }
        )

    source_candidate_count = _required_integer(
        mapping_summary.get("candidate_collection_count"),
        "mapping.summary.candidate_collection_count",
    )
    if source_candidate_count != structural_summary.get("candidate_collection_count"):
        raise ValueError("global candidate collection counts do not match")

    return {
        "schema_version": _SUMMARY_SCHEMA_VERSION,
        "summary_kind": "observed_report_slice_mapping_summary",
        "generated_at": _generated_at(),
        "source_mapping_review_name": mapping_review_path.name,
        "source_structural_review_name": structural_review_path.name,
        "max_candidates_per_entity": max_candidates_per_entity,
        "endpoints": endpoints,
        "decision_boundary": {
            "status": "candidate",
            "automatic_scope_selection": False,
            "can_promote": False,
            "semantic_verification_required": True,
            "normalization_allowed": False,
        },
        "summary": {
            "endpoint_count": len(endpoints),
            "field_path_count": mapping_summary.get("field_path_count"),
            "node_occurrence_count": mapping_summary.get("node_occurrence_count"),
            "source_candidate_collection_count": source_candidate_count,
            "aggregated_candidate_path_count": total_aggregated_candidates,
            "shortlist_row_count": total_shortlist_rows,
            "all_archives_consistent": True,
            "contains_source_scalar_values": False,
            "semantic_verification_required": True,
            "normalization_allowed": False,
            "ready_for_manual_scope_selection": True,
        },
    }
