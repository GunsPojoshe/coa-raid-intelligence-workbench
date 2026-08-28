from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Iterable

INSPECTOR_VERSION = "schema-inspector-v1"

ENTITY_HINTS: dict[str, frozenset[str]] = {
    "report": frozenset({"report_id", "reportid", "code", "title", "created_at", "start_time"}),
    "encounter": frozenset({"encounter_id", "encounterid", "boss", "boss_id", "duration", "success", "raid_size"}),
    "actor": frozenset({"actor_id", "source_id", "guid", "name", "nickname", "class", "spec", "type"}),
    "aura_event": frozenset({"timestamp", "timestamp_ms", "event_type", "type", "source", "target", "spell_id", "ability", "stacks"}),
}


def _pointer(path: tuple[str, ...]) -> str:
    if not path:
        return "/"
    return "/" + "/".join(part.replace("~", "~0").replace("/", "~1") for part in path)


def structural_shape(value: Any, *, sample_limit: int = 25) -> Any:
    if isinstance(value, dict):
        return {key: structural_shape(value[key], sample_limit=sample_limit) for key in sorted(value)}
    if isinstance(value, list):
        shapes: list[Any] = []
        for item in value[:sample_limit]:
            candidate = structural_shape(item, sample_limit=sample_limit)
            if candidate not in shapes:
                shapes.append(candidate)
        return {"list": shapes}
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, int):
        return "int"
    if isinstance(value, float):
        return "float"
    return "str"


def structure_fingerprint(value: Any) -> str:
    encoded = json.dumps(structural_shape(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class CollectionCandidate:
    path: str
    item_count: int
    object_item_count: int
    observed_keys: tuple[str, ...]
    entity_scores: dict[str, float]
    matched_hints: dict[str, tuple[str, ...]]


@dataclass(frozen=True, slots=True)
class SchemaInspection:
    inspector_version: str
    schema_fingerprint: str
    root_type: str
    collection_count: int
    candidates: tuple[CollectionCandidate, ...]
    warnings: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _walk_collections(value: Any, path: tuple[str, ...] = ()) -> Iterable[tuple[tuple[str, ...], list[Any]]]:
    if isinstance(value, list):
        yield path, value
        for index, item in enumerate(value[:25]):
            yield from _walk_collections(item, (*path, str(index)))
    elif isinstance(value, dict):
        for key, child in value.items():
            yield from _walk_collections(child, (*path, key))


def inspect_payload(payload: Any) -> SchemaInspection:
    candidates: list[CollectionCandidate] = []
    warnings: list[str] = []
    for path, collection in _walk_collections(payload):
        object_items = [item for item in collection[:100] if isinstance(item, dict)]
        keys = sorted({str(key) for item in object_items for key in item})
        folded = {key.casefold() for key in keys}
        scores: dict[str, float] = {}
        matched: dict[str, tuple[str, ...]] = {}
        for entity, hints in ENTITY_HINTS.items():
            hits = tuple(sorted(folded & hints))
            matched[entity] = hits
            denominator = max(1, min(len(hints), 5))
            scores[entity] = round(len(hits) / denominator, 3)
        candidates.append(
            CollectionCandidate(
                path=_pointer(path),
                item_count=len(collection),
                object_item_count=len(object_items),
                observed_keys=tuple(keys),
                entity_scores=scores,
                matched_hints=matched,
            )
        )
    candidates.sort(
        key=lambda item: (
            -max(item.entity_scores.values(), default=0.0),
            -item.object_item_count,
            item.path,
        )
    )
    if not candidates:
        warnings.append("payload contains no arrays; no collection mapping can be proposed")
    if isinstance(payload, list):
        warnings.append("root payload is an array; a report envelope cannot be inferred automatically")
    return SchemaInspection(
        inspector_version=INSPECTOR_VERSION,
        schema_fingerprint=structure_fingerprint(payload),
        root_type=type(payload).__name__,
        collection_count=len(candidates),
        candidates=tuple(candidates),
        warnings=tuple(warnings),
    )
