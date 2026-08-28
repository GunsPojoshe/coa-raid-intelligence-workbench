from __future__ import annotations

import gzip
import hashlib
import json
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .report_discovery_review import review_report_discovery_capture

_MAPPING_REVIEW_SCHEMA_VERSION = 1
_DEFAULT_MAX_NODES = 100_000


def _generated_at() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


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
    raise TypeError(f"unsupported JSON value type: {type(value).__name__}")


def _escape_pointer_segment(value: str) -> str:
    return value.replace("~", "~0").replace("/", "~1")


def _object_key_mode(value: dict[Any, Any]) -> str:
    keys = [str(key) for key in value]
    if not keys:
        return "empty"
    if all(key.isdecimal() for key in keys):
        return "numeric_map"
    return "fixed_fields"


def _child_path(parent: str, segment: str) -> str:
    return f"/{segment}" if parent == "/" else f"{parent}/{segment}"


@dataclass(slots=True)
class _ShapeAccumulator:
    occurrence_count: int = 0
    type_counts: Counter[str] = field(default_factory=Counter)
    object_count: int = 0
    object_key_mode_counts: Counter[str] = field(default_factory=Counter)
    fixed_object_count: int = 0
    fixed_object_keys: set[str] = field(default_factory=set)
    required_fixed_object_keys: set[str] | None = None
    numeric_map_count: int = 0
    numeric_map_total_entries: int = 0
    numeric_map_min_entries: int | None = None
    numeric_map_max_entries: int | None = None
    array_count: int = 0
    array_total_items: int = 0
    array_min_length: int | None = None
    array_max_length: int | None = None
    array_item_type_counts: Counter[str] = field(default_factory=Counter)

    def observe(self, value: Any) -> None:
        value_type = _json_type(value)
        self.occurrence_count += 1
        self.type_counts[value_type] += 1
        if isinstance(value, dict):
            keys = {str(key) for key in value}
            key_mode = _object_key_mode(value)
            self.object_count += 1
            self.object_key_mode_counts[key_mode] += 1
            if key_mode == "fixed_fields":
                self.fixed_object_count += 1
                self.fixed_object_keys.update(keys)
                if self.required_fixed_object_keys is None:
                    self.required_fixed_object_keys = set(keys)
                else:
                    self.required_fixed_object_keys.intersection_update(keys)
            elif key_mode == "numeric_map":
                entry_count = len(keys)
                self.numeric_map_count += 1
                self.numeric_map_total_entries += entry_count
                self.numeric_map_min_entries = (
                    entry_count
                    if self.numeric_map_min_entries is None
                    else min(self.numeric_map_min_entries, entry_count)
                )
                self.numeric_map_max_entries = (
                    entry_count
                    if self.numeric_map_max_entries is None
                    else max(self.numeric_map_max_entries, entry_count)
                )
        elif isinstance(value, list):
            length = len(value)
            self.array_count += 1
            self.array_total_items += length
            self.array_min_length = (
                length if self.array_min_length is None else min(self.array_min_length, length)
            )
            self.array_max_length = (
                length if self.array_max_length is None else max(self.array_max_length, length)
            )
            self.array_item_type_counts.update(_json_type(item) for item in value)

    def to_dict(self, path: str) -> dict[str, Any]:
        result: dict[str, Any] = {
            "path": path,
            "occurrence_count": self.occurrence_count,
            "type_counts": dict(sorted(self.type_counts.items())),
            "nullable": self.type_counts.get("null", 0) > 0,
        }
        if self.object_count:
            object_shape: dict[str, Any] = {
                "occurrence_count": self.object_count,
                "key_mode_counts": dict(sorted(self.object_key_mode_counts.items())),
            }
            if self.fixed_object_count:
                object_shape["fixed_fields"] = {
                    "occurrence_count": self.fixed_object_count,
                    "observed_keys": sorted(self.fixed_object_keys),
                    "required_keys": sorted(self.required_fixed_object_keys or ()),
                }
            if self.numeric_map_count:
                object_shape["numeric_map"] = {
                    "occurrence_count": self.numeric_map_count,
                    "total_entries": self.numeric_map_total_entries,
                    "min_entries": self.numeric_map_min_entries,
                    "max_entries": self.numeric_map_max_entries,
                }
            result["object"] = object_shape
        if self.array_count:
            result["array"] = {
                "occurrence_count": self.array_count,
                "total_items": self.array_total_items,
                "min_length": self.array_min_length,
                "max_length": self.array_max_length,
                "item_type_counts": dict(sorted(self.array_item_type_counts.items())),
            }
        return result


def _profile_payload(payload: Any, *, max_nodes: int) -> tuple[list[dict[str, Any]], int]:
    accumulators: dict[str, _ShapeAccumulator] = {}
    visited = 0

    def walk(value: Any, path: str) -> None:
        nonlocal visited
        visited += 1
        if visited > max_nodes:
            raise ValueError(f"report discovery mapping review exceeded max_nodes={max_nodes}")
        accumulators.setdefault(path, _ShapeAccumulator()).observe(value)
        if isinstance(value, dict):
            if _object_key_mode(value) == "numeric_map":
                child_path = _child_path(path, "*")
                for key in sorted(value, key=lambda item: int(str(item))):
                    walk(value[key], child_path)
            else:
                for key in sorted(value, key=str):
                    child_path = _child_path(path, _escape_pointer_segment(str(key)))
                    walk(value[key], child_path)
        elif isinstance(value, list):
            child_path = _child_path(path, "*")
            for child in value:
                walk(child, child_path)

    walk(payload, "/")
    return [accumulators[path].to_dict(path) for path in sorted(accumulators)], visited


def _load_verified_payload(structural: dict[str, Any], *, raw_root: Path) -> Any:
    root = raw_root.resolve()
    response = structural["response"]
    path = (root / str(response["payload_path"])).resolve()
    if not path.is_relative_to(root) or not path.is_file() or not path.name.endswith(".json.gz"):
        raise ValueError("report discovery payload must be a gzip JSON archive below raw-root")
    body = gzip.decompress(path.read_bytes())
    if hashlib.sha256(body).hexdigest() != response["payload_hash"]:
        raise ValueError("report discovery payload hash changed after structural review")
    return json.loads(body)


def build_report_discovery_mapping_review(
    capture_path: Path,
    *,
    raw_root: Path,
    max_nodes: int = _DEFAULT_MAX_NODES,
) -> dict[str, Any]:
    """Build a full-root type-only review packet without source scalar values."""
    if max_nodes < 1:
        raise ValueError("max_nodes must be positive")
    structural = review_report_discovery_capture(capture_path, raw_root=raw_root)
    payload = _load_verified_payload(structural, raw_root=raw_root)
    field_shapes, visited = _profile_payload(payload, max_nodes=max_nodes)
    numeric_map_paths = sum(
        1 for field_shape in field_shapes if field_shape.get("object", {}).get("numeric_map")
    )
    response = structural["response"]
    return {
        "schema_version": _MAPPING_REVIEW_SCHEMA_VERSION,
        "review_kind": "report_discovery_mapping_review",
        "generated_at": _generated_at(),
        "source_capture_name": capture_path.name,
        "local_category": structural["local_category"],
        "request": structural["request"],
        "payload": {
            "payload_hash": response["payload_hash"],
            "schema_fingerprint": response["schema_fingerprint"],
            "top_level_kind": response["top_level_kind"],
            "top_level_keys": response["top_level_keys"],
            "review_status": "candidate",
            "provenance_type": "upstream_derived",
            "scope": "/",
            "field_shapes": field_shapes,
        },
        "summary": {
            "archive_verified": structural["summary"]["archive_verified"],
            "field_path_count": len(field_shapes),
            "node_occurrence_count": visited,
            "numeric_map_path_count": numeric_map_paths,
            "candidate_collection_count": structural["summary"]["candidate_collection_count"],
            "contains_source_scalar_values": False,
            "category_semantics_verified": False,
            "pagination_policy_verified": False,
            "ready_for_manual_mapping_review": True,
        },
    }
