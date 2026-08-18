from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Mapping, Sequence

SCHEMA_PATH_NORMALIZATION = "numeric-object-key-wildcard-v1"
DYNAMIC_INTEGER_KEY_SEGMENT = "{integer-key}"
_INTEGER_KEY = re.compile(r"^[0-9]+$")


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def structural_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def normalize_object_key(key: object) -> str:
    text = str(key)
    return DYNAMIC_INTEGER_KEY_SEGMENT if _INTEGER_KEY.fullmatch(text) else text


def normalize_pointer_path(path: str) -> str:
    if path in {"", "/"}:
        return "/"
    prefix = "/" if path.startswith("/") else ""
    segments = path[1:].split("/") if prefix else path.split("/")
    return prefix + "/".join(normalize_object_key(segment) for segment in segments)


def normalize_path_types(path_types: Mapping[str, Sequence[str]]) -> dict[str, tuple[str, ...]]:
    merged: dict[str, set[str]] = {}
    for path, type_names in path_types.items():
        normalized = normalize_pointer_path(str(path))
        merged.setdefault(normalized, set()).update(str(value) for value in type_names)
    return {
        path: tuple(sorted(type_names))
        for path, type_names in sorted(merged.items())
    }


def json_structure_shape(value: Any, *, max_array_items: int = 100) -> Any:
    """Return a scalar-free structural shape with numeric object keys wildcarded."""
    if max_array_items < 1:
        raise ValueError("max_array_items must be positive")
    if isinstance(value, dict):
        fixed: dict[str, Any] = {}
        dynamic_shapes: dict[str, Any] = {}
        for key in sorted(value, key=str):
            child_shape = json_structure_shape(value[key], max_array_items=max_array_items)
            normalized = normalize_object_key(key)
            if normalized == DYNAMIC_INTEGER_KEY_SEGMENT:
                dynamic_shapes.setdefault(canonical_json(child_shape), child_shape)
            else:
                fixed[str(key)] = child_shape
        if dynamic_shapes:
            fixed[DYNAMIC_INTEGER_KEY_SEGMENT] = {
                "variants": [dynamic_shapes[key] for key in sorted(dynamic_shapes)]
            }
        return fixed
    if isinstance(value, list):
        unique: dict[str, Any] = {}
        for child in value[:max_array_items]:
            child_shape = json_structure_shape(child, max_array_items=max_array_items)
            unique.setdefault(canonical_json(child_shape), child_shape)
        return {"list": [unique[key] for key in sorted(unique)]}
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, int):
        return "int"
    if isinstance(value, float):
        return "float"
    return "str"


def json_structure_fingerprint(value: Any, *, max_array_items: int = 100) -> str:
    return structural_sha256(json_structure_shape(value, max_array_items=max_array_items))


__all__ = [
    "DYNAMIC_INTEGER_KEY_SEGMENT",
    "SCHEMA_PATH_NORMALIZATION",
    "canonical_json",
    "json_structure_fingerprint",
    "json_structure_shape",
    "normalize_object_key",
    "normalize_path_types",
    "normalize_pointer_path",
    "structural_sha256",
]
