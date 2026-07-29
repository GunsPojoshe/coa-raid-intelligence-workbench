from __future__ import annotations

import gzip
import hashlib
import json
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .armory_structural_review import review_armory_capture_manifest

_MAPPING_REVIEW_SCHEMA_VERSION = 1
_DEFAULT_MAX_NODES = 100_000
_DEFAULT_SCOPES = {
    "character": ("/success", "/capture", "/ci_resolved", "/stats_summary"),
    "talent_grid": ("/success", "/class_name", "/trees"),
}


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


def _decode_pointer_segment(value: str) -> str:
    return value.replace("~1", "/").replace("~0", "~")


def _pointer_get(value: Any, pointer: str) -> Any:
    if pointer in {"", "/"}:
        return value
    current = value
    raw = pointer[1:] if pointer.startswith("/") else pointer
    for segment in raw.split("/"):
        key = _decode_pointer_segment(segment)
        if isinstance(current, list):
            current = current[int(key)]
        elif isinstance(current, dict):
            current = current[key]
        else:
            raise KeyError(pointer)
    return current


@dataclass(slots=True)
class _ShapeAccumulator:
    occurrence_count: int = 0
    type_counts: Counter[str] = field(default_factory=Counter)
    object_keys: set[str] = field(default_factory=set)
    required_object_keys: set[str] | None = None
    object_count: int = 0
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
            self.object_count += 1
            self.object_keys.update(keys)
            if self.required_object_keys is None:
                self.required_object_keys = set(keys)
            else:
                self.required_object_keys.intersection_update(keys)
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
            result["object"] = {
                "occurrence_count": self.object_count,
                "observed_keys": sorted(self.object_keys),
                "required_keys": sorted(self.required_object_keys or ()),
            }
        if self.array_count:
            result["array"] = {
                "occurrence_count": self.array_count,
                "total_items": self.array_total_items,
                "min_length": self.array_min_length,
                "max_length": self.array_max_length,
                "item_type_counts": dict(sorted(self.array_item_type_counts.items())),
            }
        return result


def _profile_scopes(
    payload: Any,
    scopes: tuple[str, ...],
    *,
    max_nodes: int,
) -> tuple[list[dict[str, Any]], int]:
    accumulators: dict[str, _ShapeAccumulator] = {}
    visited = 0

    def walk(value: Any, path: str) -> None:
        nonlocal visited
        visited += 1
        if visited > max_nodes:
            raise ValueError(f"Armory mapping review exceeded max_nodes={max_nodes}")
        accumulator = accumulators.setdefault(path, _ShapeAccumulator())
        accumulator.observe(value)
        if isinstance(value, dict):
            for key in sorted(value):
                child_path = f"{path}/{_escape_pointer_segment(str(key))}"
                walk(value[key], child_path)
        elif isinstance(value, list):
            child_path = f"{path}/*"
            for child in value:
                walk(child, child_path)

    for scope in scopes:
        try:
            value = _pointer_get(payload, scope)
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise ValueError(f"required Armory review scope is missing: {scope}") from exc
        walk(value, scope)

    fields = [accumulators[path].to_dict(path) for path in sorted(accumulators)]
    return fields, visited


def _load_verified_payload(
    endpoint: dict[str, Any],
    *,
    raw_root: Path,
) -> Any:
    root = raw_root.resolve()
    path = (root / str(endpoint["payload_path"])).resolve()
    if not path.is_relative_to(root) or not path.is_file() or not path.name.endswith(".json.gz"):
        raise ValueError("Armory payload path must be a gzip JSON archive below raw-root")
    body = gzip.decompress(path.read_bytes())
    actual_hash = hashlib.sha256(body).hexdigest()
    if actual_hash != endpoint["payload_hash"]:
        raise ValueError("Armory payload hash changed after structural review")
    return json.loads(body)


def build_armory_mapping_review(
    manifest_path: Path,
    *,
    raw_root: Path,
    max_nodes: int = _DEFAULT_MAX_NODES,
) -> dict[str, Any]:
    """Build a compact type-only Armory review packet without source scalar values."""
    if max_nodes < 1:
        raise ValueError("max_nodes must be positive")
    structural = review_armory_capture_manifest(manifest_path, raw_root=raw_root)
    endpoints: list[dict[str, Any]] = []
    total_paths = 0
    total_nodes = 0

    for endpoint in structural["endpoints"]:
        endpoint_kind = str(endpoint["endpoint_kind"])
        scopes = _DEFAULT_SCOPES.get(endpoint_kind)
        if scopes is None:
            raise ValueError(f"unsupported Armory endpoint kind for mapping review: {endpoint_kind}")
        payload = _load_verified_payload(endpoint, raw_root=raw_root)
        fields, visited = _profile_scopes(payload, scopes, max_nodes=max_nodes)
        total_paths += len(fields)
        total_nodes += visited
        endpoints.append(
            {
                "endpoint_kind": endpoint_kind,
                "payload_hash": endpoint["payload_hash"],
                "schema_fingerprint": endpoint["schema_fingerprint"],
                "review_status": "candidate",
                "provenance_type": "upstream_derived",
                "scopes": list(scopes),
                "field_shapes": fields,
                "summary": {
                    "field_path_count": len(fields),
                    "node_occurrence_count": visited,
                },
            }
        )

    return {
        "schema_version": _MAPPING_REVIEW_SCHEMA_VERSION,
        "review_kind": "armory_mapping_review",
        "generated_at": _generated_at(),
        "source_manifest_name": manifest_path.name,
        "http_profile_version": structural["http_profile_version"],
        "subject": structural["subject"],
        "endpoint_order": structural["endpoint_order"],
        "endpoints": endpoints,
        "summary": {
            "endpoint_count": len(endpoints),
            "archive_verified": structural["summary"]["archive_verified"],
            "field_path_count": total_paths,
            "node_occurrence_count": total_nodes,
            "contains_source_scalar_values": False,
            "ready_for_manual_mapping_review": True,
        },
    }
