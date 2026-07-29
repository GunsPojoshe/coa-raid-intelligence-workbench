from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_SCOPE_REVIEW_SCHEMA_VERSION = 1
_MAPPING_REVIEW_KIND = "observed_report_slice_mapping_review"
_MAPPING_SUMMARY_KIND = "observed_report_slice_mapping_summary"

_SCOPE_CANDIDATES: dict[str, tuple[tuple[str, str], ...]] = {
    "report_detail": (
        ("/report", "report_object_candidate"),
        ("/encounters/*", "encounter_list_item_candidate"),
    ),
    "encounter_detail": (
        ("/encounter", "encounter_object_candidate"),
        ("/character_stats/*", "participant_stats_item_candidate"),
    ),
    "combatants_info": (
        ("/combatants/*", "combatant_item_candidate"),
        ("/combatants/*/ci_resolved", "resolved_combatant_candidate"),
        (
            "/combatants/*/ci_resolved/specialization",
            "specialization_object_candidate",
        ),
    ),
}


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
        raise ValueError(
            f"{field_name} must be an integer greater than or equal to {minimum}"
        )
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


def _shape_index(values: object, *, endpoint_kind: str) -> dict[str, dict[str, Any]]:
    rows = _required_list(values, f"mapping field shapes {endpoint_kind}")
    result: dict[str, dict[str, Any]] = {}
    for raw in rows:
        row = _required_object(raw, f"mapping field shapes {endpoint_kind}[]")
        path = _required_string(row.get("path"), "field_shape.path")
        if path in result:
            raise ValueError(f"duplicate field shape path for {endpoint_kind}: {path}")
        result[path] = row
    return result


def _direct_child_name(parent: str, child: str) -> str | None:
    prefix = parent.rstrip("/") + "/"
    if not child.startswith(prefix):
        return None
    remainder = child[len(prefix) :]
    return remainder if remainder and "/" not in remainder else None


def _object_metadata(shape: dict[str, Any]) -> dict[str, Any] | None:
    raw_object = shape.get("object")
    if not isinstance(raw_object, dict):
        return None
    result: dict[str, Any] = {
        "occurrence_count": raw_object.get("occurrence_count"),
        "key_mode_counts": _safe_type_counts(raw_object.get("key_mode_counts")),
    }
    fixed_fields = raw_object.get("fixed_fields")
    if isinstance(fixed_fields, dict):
        result["fixed_fields"] = {
            "occurrence_count": fixed_fields.get("occurrence_count"),
            "observed_keys": _safe_string_list(fixed_fields.get("observed_keys")),
            "required_keys": _safe_string_list(fixed_fields.get("required_keys")),
        }
    numeric_map = raw_object.get("numeric_map")
    if isinstance(numeric_map, dict):
        result["numeric_map"] = {
            "occurrence_count": numeric_map.get("occurrence_count"),
            "total_entries": numeric_map.get("total_entries"),
            "min_entries": numeric_map.get("min_entries"),
            "max_entries": numeric_map.get("max_entries"),
        }
    return result


def _array_metadata(shape: dict[str, Any]) -> dict[str, Any] | None:
    raw_array = shape.get("array")
    if not isinstance(raw_array, dict):
        return None
    return {
        "occurrence_count": raw_array.get("occurrence_count"),
        "total_items": raw_array.get("total_items"),
        "min_length": raw_array.get("min_length"),
        "max_length": raw_array.get("max_length"),
        "item_type_counts": _safe_type_counts(raw_array.get("item_type_counts")),
    }


def _shape_row(shape: dict[str, Any]) -> dict[str, Any]:
    type_counts = _safe_type_counts(shape.get("type_counts"))
    result: dict[str, Any] = {
        "path": _required_string(shape.get("path"), "field_shape.path"),
        "occurrence_count": _required_integer(
            shape.get("occurrence_count"),
            "field_shape.occurrence_count",
            minimum=1,
        ),
        "types": sorted(type_counts),
        "type_counts": type_counts,
        "nullable": shape.get("nullable") is True,
        "is_array": isinstance(shape.get("array"), dict),
        "is_object": isinstance(shape.get("object"), dict),
    }
    array = _array_metadata(shape)
    if array is not None:
        result["array"] = array
    object_metadata = _object_metadata(shape)
    if object_metadata is not None:
        result["object"] = object_metadata
    return result


def _scope_review(
    *,
    endpoint_kind: str,
    route_template: str,
    payload_hash: str,
    schema_fingerprint: str,
    scope: str,
    review_label: str,
    shapes: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    scope_shape = shapes.get(scope)
    if scope_shape is None:
        raise ValueError(f"required scope is missing for {endpoint_kind}: {scope}")
    scope_row = _shape_row(scope_shape)
    scope_occurrences = scope_row["occurrence_count"]
    direct_fields: list[dict[str, Any]] = []
    for path in sorted(shapes):
        name = _direct_child_name(scope, path)
        if name is None:
            continue
        field = _shape_row(shapes[path])
        field["name"] = name
        field["observed_on_all_scope_occurrences"] = (
            field["occurrence_count"] == scope_occurrences
        )
        direct_fields.append(field)

    return {
        "endpoint_kind": endpoint_kind,
        "route_template": route_template,
        "payload_hash": payload_hash,
        "schema_fingerprint": schema_fingerprint,
        "scope": scope,
        "review_label": review_label,
        "review_status": "candidate",
        "semantic_status": "unverified_candidate",
        "manual_decision_required": True,
        "scope_shape": scope_row,
        "direct_fields": direct_fields,
        "summary": {
            "scope_occurrence_count": scope_occurrences,
            "direct_field_count": len(direct_fields),
            "nullable_direct_field_count": sum(
                1 for field in direct_fields if field["nullable"]
            ),
            "array_direct_field_count": sum(
                1 for field in direct_fields if field["is_array"]
            ),
            "object_direct_field_count": sum(
                1 for field in direct_fields if field["is_object"]
            ),
            "fields_observed_on_all_scope_occurrences": sum(
                1
                for field in direct_fields
                if field["observed_on_all_scope_occurrences"]
            ),
        },
    }


def build_observed_report_slice_scope_review(
    mapping_review_path: Path,
    mapping_summary_path: Path,
) -> dict[str, Any]:
    """Build a scalar-free direct-field packet for explicit candidate scopes."""
    mapping = _load_object(mapping_review_path, label="mapping review")
    summary = _load_object(mapping_summary_path, label="mapping summary")
    if mapping.get("review_kind") != _MAPPING_REVIEW_KIND:
        raise ValueError("unsupported report slice mapping review kind")
    if summary.get("summary_kind") != _MAPPING_SUMMARY_KIND:
        raise ValueError("unsupported report slice mapping summary kind")

    mapping_totals = _required_object(mapping.get("summary"), "mapping.summary")
    summary_totals = _required_object(summary.get("summary"), "summary.summary")
    decision = _required_object(summary.get("decision_boundary"), "decision_boundary")
    for label, totals in (("mapping", mapping_totals), ("summary", summary_totals)):
        if totals.get("contains_source_scalar_values") is not False:
            raise ValueError(f"{label} privacy gate is not satisfied")
        if totals.get("normalization_allowed") is not False:
            raise ValueError(f"{label} normalization gate is not satisfied")
    if mapping_totals.get("all_archives_consistent") is not True:
        raise ValueError("mapping archive consistency gate is not satisfied")
    if summary_totals.get("all_archives_consistent") is not True:
        raise ValueError("summary archive consistency gate is not satisfied")
    if decision.get("automatic_scope_selection") is not False:
        raise ValueError("automatic scope selection must remain disabled")
    if decision.get("can_promote") is not False:
        raise ValueError("automatic promotion must remain disabled")
    if decision.get("normalization_allowed") is not False:
        raise ValueError("normalization must remain disabled")

    mapping_endpoints = _endpoint_index(mapping.get("endpoints"), label="mapping.endpoints")
    summary_endpoints = _endpoint_index(summary.get("endpoints"), label="summary.endpoints")
    if set(mapping_endpoints) != set(_SCOPE_CANDIDATES):
        raise ValueError("mapping endpoint set does not match bounded scope review")
    if set(summary_endpoints) != set(mapping_endpoints):
        raise ValueError("mapping and summary endpoint sets do not match")

    scopes: list[dict[str, Any]] = []
    total_direct_fields = 0
    for endpoint_kind in sorted(mapping_endpoints):
        mapping_endpoint = mapping_endpoints[endpoint_kind]
        summary_endpoint = summary_endpoints[endpoint_kind]
        for field_name in (
            "route_template",
            "payload_hash",
            "schema_fingerprint",
            "top_level_kind",
            "top_level_keys",
            "review_status",
            "scope",
        ):
            if mapping_endpoint.get(field_name) != summary_endpoint.get(field_name):
                raise ValueError(
                    f"mapping and summary {field_name} do not match for {endpoint_kind}"
                )
        if mapping_endpoint.get("review_status") != "candidate":
            raise ValueError(f"endpoint {endpoint_kind} is not a candidate review")
        shapes = _shape_index(
            mapping_endpoint.get("field_shapes"),
            endpoint_kind=endpoint_kind,
        )
        for scope, review_label in _SCOPE_CANDIDATES[endpoint_kind]:
            scope_packet = _scope_review(
                endpoint_kind=endpoint_kind,
                route_template=_required_string(
                    mapping_endpoint.get("route_template"),
                    "route_template",
                ),
                payload_hash=_required_string(
                    mapping_endpoint.get("payload_hash"),
                    "payload_hash",
                ),
                schema_fingerprint=_required_string(
                    mapping_endpoint.get("schema_fingerprint"),
                    "schema_fingerprint",
                ),
                scope=scope,
                review_label=review_label,
                shapes=shapes,
            )
            total_direct_fields += scope_packet["summary"]["direct_field_count"]
            scopes.append(scope_packet)

    return {
        "schema_version": _SCOPE_REVIEW_SCHEMA_VERSION,
        "review_kind": "observed_report_slice_scope_review",
        "generated_at": _generated_at(),
        "source_mapping_review_name": mapping_review_path.name,
        "source_mapping_summary_name": mapping_summary_path.name,
        "scopes": scopes,
        "decision_boundary": {
            "status": "candidate",
            "automatic_scope_selection": False,
            "automatic_field_selection": False,
            "can_promote": False,
            "semantic_verification_required": True,
            "normalization_allowed": False,
        },
        "summary": {
            "endpoint_count": len(mapping_endpoints),
            "scope_candidate_count": len(scopes),
            "direct_field_count": total_direct_fields,
            "all_archives_consistent": True,
            "contains_source_scalar_values": False,
            "semantic_verification_required": True,
            "normalization_allowed": False,
            "ready_for_manual_field_selection": True,
        },
    }
