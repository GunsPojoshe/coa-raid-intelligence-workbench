from __future__ import annotations

from typing import Any, Mapping


def _required_object(value: object, field_name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{field_name} must be an object")
    return value


def _required_list(value: object, field_name: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be an array")
    return value


def _text(value: object) -> str:
    if value is True:
        return "true"
    if value is False:
        return "false"
    if value is None:
        return "null"
    if isinstance(value, list):
        return ", ".join(str(item) for item in value)
    return str(value)


def _counts(value: object) -> str:
    if not isinstance(value, Mapping):
        return ""
    return ", ".join(f"{key}={value[key]}" for key in sorted(value, key=str))


def render_report_discovery_mapping_summary_text(summary: Mapping[str, Any]) -> str:
    """Render a scalar-free mapping summary without shell-side object traversal."""
    payload = _required_object(summary.get("payload"), "summary.payload")
    decision = _required_object(
        summary.get("candidate_decision"),
        "summary.candidate_decision",
    )
    report_shape = _required_object(
        summary.get("report_item_shape"),
        "summary.report_item_shape",
    )
    totals = _required_object(summary.get("summary"), "summary.summary")
    fields = _required_list(report_shape.get("fields"), "summary.report_item_shape.fields")
    arrays = _required_list(summary.get("array_paths"), "summary.array_paths")
    nullable_paths = _required_list(summary.get("nullable_paths"), "summary.nullable_paths")

    lines = [
        "REPORT_MAPPING_SUMMARY",
        f"schema_version={_text(summary.get('schema_version'))}",
        f"summary_kind={_text(summary.get('summary_kind'))}",
        f"review_status={_text(payload.get('review_status'))}",
        f"payload_hash={_text(payload.get('payload_hash'))}",
        f"schema_fingerprint={_text(payload.get('schema_fingerprint'))}",
        f"top_level_kind={_text(payload.get('top_level_kind'))}",
        f"top_level_keys={_text(payload.get('top_level_keys'))}",
        f"field_path_count={_text(totals.get('field_path_count'))}",
        f"node_occurrence_count={_text(totals.get('node_occurrence_count'))}",
        f"numeric_map_path_count={_text(totals.get('numeric_map_path_count'))}",
        f"candidate_collection_count={_text(totals.get('candidate_collection_count'))}",
        f"array_path_count={_text(totals.get('array_path_count'))}",
        f"nullable_path_count={_text(totals.get('nullable_path_count'))}",
        f"report_field_count={_text(totals.get('report_field_count'))}",
        f"contains_source_scalar_values={_text(totals.get('contains_source_scalar_values'))}",
        "",
        "CANDIDATE_DECISION",
        f"status={_text(decision.get('status'))}",
        f"unique_report_like_collection={_text(decision.get('unique_report_like_collection'))}",
        f"report_collection_path={_text(decision.get('report_collection_path'))}",
        f"report_item_selector={_text(decision.get('report_item_selector'))}",
        f"can_promote={_text(decision.get('can_promote'))}",
        f"semantic_verification_required={_text(decision.get('semantic_verification_required'))}",
        f"category_semantics_verified={_text(decision.get('category_semantics_verified'))}",
        f"pagination_policy_verified={_text(decision.get('pagination_policy_verified'))}",
        "",
        "REPORT_ITEM_SHAPE",
        f"path={_text(report_shape.get('path'))}",
        f"occurrence_count={_text(report_shape.get('occurrence_count'))}",
        f"observed_keys={_text(report_shape.get('observed_keys'))}",
        f"required_keys={_text(report_shape.get('required_keys'))}",
        "",
        "REPORT_FIELDS",
    ]

    if fields:
        for entry in fields:
            field = _required_object(entry, "summary.report_item_shape.fields[]")
            lines.append(
                " | ".join(
                    [
                        f"name={_text(field.get('name'))}",
                        f"path={_text(field.get('path'))}",
                        f"types={_text(field.get('types'))}",
                        f"nullable={_text(field.get('nullable'))}",
                        f"observed_on_all_items={_text(field.get('observed_on_all_items'))}",
                        f"occurrence_count={_text(field.get('occurrence_count'))}",
                    ]
                )
            )
    else:
        lines.append("<none>")

    lines.extend(["", "ARRAY_PATHS"])
    if arrays:
        for entry in arrays:
            array = _required_object(entry, "summary.array_paths[]")
            lines.append(
                " | ".join(
                    [
                        f"path={_text(array.get('path'))}",
                        f"occurrence_count={_text(array.get('occurrence_count'))}",
                        f"total_items={_text(array.get('total_items'))}",
                        f"min_length={_text(array.get('min_length'))}",
                        f"max_length={_text(array.get('max_length'))}",
                        f"item_type_counts={_counts(array.get('item_type_counts'))}",
                    ]
                )
            )
    else:
        lines.append("<none>")

    lines.extend(["", "NULLABLE_PATHS"])
    if nullable_paths:
        for entry in nullable_paths:
            nullable = _required_object(entry, "summary.nullable_paths[]")
            lines.append(
                " | ".join(
                    [
                        f"path={_text(nullable.get('path'))}",
                        f"occurrence_count={_text(nullable.get('occurrence_count'))}",
                        f"type_counts={_counts(nullable.get('type_counts'))}",
                    ]
                )
            )
    else:
        lines.append("<none>")

    return "\n".join(lines) + "\n"
