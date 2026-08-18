from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_SUMMARY_SCHEMA_VERSION = 1
_MAPPING_REVIEW_KIND = "report_discovery_mapping_review"
_STRUCTURAL_REVIEW_KIND = "report_discovery_structural_review"


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


def _direct_child_name(parent: str, child: str) -> str | None:
    prefix = parent.rstrip("/") + "/"
    if not child.startswith(prefix):
        return None
    remainder = child[len(prefix) :]
    return remainder if remainder and "/" not in remainder else None


def _safe_type_counts(value: object) -> dict[str, int]:
    if not isinstance(value, dict):
        return {}
    result: dict[str, int] = {}
    for key, count in value.items():
        if isinstance(key, str) and isinstance(count, int) and not isinstance(count, bool):
            result[key] = count
    return dict(sorted(result.items()))


def _collection_score(candidate: dict[str, Any], entity: str) -> float:
    scores = candidate.get("entity_scores")
    if not isinstance(scores, dict):
        return 0.0
    value = scores.get(entity, 0)
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else 0.0


def summarize_report_discovery_mapping_review(
    mapping_review_path: Path,
    structural_review_path: Path,
) -> dict[str, Any]:
    """Create a scalar-free, PowerShell-safe summary of one exact report review packet."""
    mapping = _load_object(mapping_review_path, label="mapping review")
    structural = _load_object(structural_review_path, label="structural review")

    if mapping.get("review_kind") != _MAPPING_REVIEW_KIND:
        raise ValueError("unsupported report mapping review kind")
    if structural.get("review_kind") != _STRUCTURAL_REVIEW_KIND:
        raise ValueError("unsupported report structural review kind")

    mapping_payload = _required_object(mapping.get("payload"), "mapping.payload")
    mapping_summary = _required_object(mapping.get("summary"), "mapping.summary")
    structural_response = _required_object(structural.get("response"), "structural.response")
    structural_summary = _required_object(structural.get("summary"), "structural.summary")

    payload_hash = _required_string(mapping_payload.get("payload_hash"), "mapping.payload_hash")
    fingerprint = _required_string(
        mapping_payload.get("schema_fingerprint"),
        "mapping.schema_fingerprint",
    )
    if structural_response.get("payload_hash") != payload_hash:
        raise ValueError("mapping and structural payload hashes do not match")
    if structural_response.get("schema_fingerprint") != fingerprint:
        raise ValueError("mapping and structural schema fingerprints do not match")
    if mapping_summary.get("contains_source_scalar_values") is not False:
        raise ValueError("mapping review privacy gate is not satisfied")
    if structural_summary.get("contains_source_scalar_values") is not False:
        raise ValueError("structural review privacy gate is not satisfied")

    raw_shapes = _required_list(mapping_payload.get("field_shapes"), "mapping.field_shapes")
    shapes = [item for item in raw_shapes if isinstance(item, dict)]
    if len(shapes) != len(raw_shapes):
        raise ValueError("mapping field_shapes contains a non-object entry")
    shapes_by_path = {
        str(item["path"]): item
        for item in shapes
        if isinstance(item.get("path"), str) and item.get("path")
    }

    raw_candidates = _required_list(
        structural_response.get("candidate_collections"),
        "structural.candidate_collections",
    )
    candidates = [item for item in raw_candidates if isinstance(item, dict)]
    if len(candidates) != len(raw_candidates):
        raise ValueError("candidate_collections contains a non-object entry")

    candidate_rows: list[dict[str, Any]] = []
    report_like: list[dict[str, Any]] = []
    for candidate in candidates:
        path = candidate.get("path")
        if not isinstance(path, str) or not path:
            continue
        row = {
            "path": path,
            "item_count": candidate.get("item_count"),
            "object_item_count": candidate.get("object_item_count"),
            "observed_keys": candidate.get("observed_keys", []),
            "report_score": _collection_score(candidate, "report"),
            "encounter_score": _collection_score(candidate, "encounter"),
            "actor_score": _collection_score(candidate, "actor"),
            "aura_event_score": _collection_score(candidate, "aura_event"),
        }
        candidate_rows.append(row)
        if row["report_score"] > 0 and isinstance(row["object_item_count"], int) and row["object_item_count"] > 0:
            report_like.append(row)

    report_collection_path = report_like[0]["path"] if len(report_like) == 1 else None
    report_item_path = (
        report_collection_path.rstrip("/") + "/*" if report_collection_path is not None else None
    )

    item_shape = shapes_by_path.get(report_item_path or "", {})
    fixed_fields = item_shape.get("object", {}).get("fixed_fields", {}) if isinstance(item_shape, dict) else {}
    observed_keys = fixed_fields.get("observed_keys", []) if isinstance(fixed_fields, dict) else []
    required_keys = fixed_fields.get("required_keys", []) if isinstance(fixed_fields, dict) else []
    observed_key_set = {str(value) for value in observed_keys if isinstance(value, str)}
    required_key_set = {str(value) for value in required_keys if isinstance(value, str)}

    report_fields: list[dict[str, Any]] = []
    if report_item_path is not None:
        for path in sorted(shapes_by_path):
            name = _direct_child_name(report_item_path, path)
            if name is None:
                continue
            shape = shapes_by_path[path]
            report_fields.append(
                {
                    "name": name,
                    "path": path,
                    "occurrence_count": shape.get("occurrence_count"),
                    "type_counts": _safe_type_counts(shape.get("type_counts")),
                    "types": sorted(_safe_type_counts(shape.get("type_counts"))),
                    "nullable": shape.get("nullable") is True,
                    "observed_on_all_items": name in required_key_set,
                }
            )

    arrays: list[dict[str, Any]] = []
    nullable_paths: list[dict[str, Any]] = []
    for shape in shapes:
        path = shape.get("path")
        if not isinstance(path, str):
            continue
        array = shape.get("array")
        if isinstance(array, dict):
            arrays.append(
                {
                    "path": path,
                    "occurrence_count": array.get("occurrence_count"),
                    "total_items": array.get("total_items"),
                    "min_length": array.get("min_length"),
                    "max_length": array.get("max_length"),
                    "item_type_counts": _safe_type_counts(array.get("item_type_counts")),
                }
            )
        if shape.get("nullable") is True:
            nullable_paths.append(
                {
                    "path": path,
                    "occurrence_count": shape.get("occurrence_count"),
                    "type_counts": _safe_type_counts(shape.get("type_counts")),
                }
            )

    return {
        "schema_version": _SUMMARY_SCHEMA_VERSION,
        "summary_kind": "report_discovery_mapping_summary",
        "generated_at": _generated_at(),
        "source_mapping_review_name": mapping_review_path.name,
        "source_structural_review_name": structural_review_path.name,
        "payload": {
            "payload_hash": payload_hash,
            "schema_fingerprint": fingerprint,
            "top_level_kind": mapping_payload.get("top_level_kind"),
            "top_level_keys": mapping_payload.get("top_level_keys", []),
            "review_status": mapping_payload.get("review_status"),
        },
        "candidate_decision": {
            "status": "candidate",
            "report_like_collection_count": len(report_like),
            "unique_report_like_collection": len(report_like) == 1,
            "report_collection_path": report_collection_path,
            "report_item_selector": report_item_path,
            "can_promote": False,
            "semantic_verification_required": True,
            "category_semantics_verified": False,
            "pagination_policy_verified": False,
        },
        "report_item_shape": {
            "path": report_item_path,
            "occurrence_count": item_shape.get("occurrence_count") if isinstance(item_shape, dict) else None,
            "observed_keys": sorted(observed_key_set),
            "required_keys": sorted(required_key_set),
            "fields": report_fields,
        },
        "candidate_collections": candidate_rows,
        "array_paths": arrays,
        "nullable_paths": nullable_paths,
        "summary": {
            "archive_verified": mapping_summary.get("archive_verified"),
            "field_path_count": mapping_summary.get("field_path_count"),
            "node_occurrence_count": mapping_summary.get("node_occurrence_count"),
            "numeric_map_path_count": mapping_summary.get("numeric_map_path_count"),
            "candidate_collection_count": len(candidate_rows),
            "array_path_count": len(arrays),
            "nullable_path_count": len(nullable_paths),
            "report_field_count": len(report_fields),
            "contains_source_scalar_values": False,
            "ready_for_manual_mapping_review": True,
        },
    }
