from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence

NORMALIZER_VERSION = "canonical-normalizer-v1"
CANONICAL_AURA_EVENT_TYPES = {"APPLIED", "REFRESH", "REMOVED", "STACK_CHANGE"}
_MISSING = object()


def stable_id(entity: str, *parts: Any) -> str:
    material = "\0".join([entity, *(str(part) for part in parts)])
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def _decode_pointer_segment(segment: str) -> str:
    return segment.replace("~1", "/").replace("~0", "~")


def pointer_get(value: Any, pointer: str, default: Any = _MISSING) -> Any:
    if pointer in {"", "/", "@item"}:
        return value
    current = value
    raw = pointer[1:] if pointer.startswith("/") else pointer
    for segment in raw.split("/"):
        key = _decode_pointer_segment(segment)
        try:
            if isinstance(current, Sequence) and not isinstance(current, (str, bytes, bytearray)):
                current = current[int(key)]
            else:
                current = current[key]
        except (KeyError, IndexError, TypeError, ValueError):
            if default is _MISSING:
                raise KeyError(pointer) from None
            return default
    return current


@dataclass(frozen=True, slots=True)
class Match:
    value: Any
    path: str
    ancestors: tuple[Any, ...]
    index: int | None


def find_matches(root: Any, pattern: str) -> tuple[Match, ...]:
    segments = [_decode_pointer_segment(part) for part in pattern.strip("/").split("/") if part]
    matches: list[Match] = []

    def walk(current: Any, offset: int, path: list[str], ancestors: list[Any], index: int | None) -> None:
        if offset == len(segments):
            matches.append(Match(current, "/" + "/".join(path), tuple(ancestors), index))
            return
        segment = segments[offset]
        if segment == "*":
            if isinstance(current, list):
                for child_index, child in enumerate(current):
                    walk(child, offset + 1, [*path, str(child_index)], [*ancestors, current], child_index)
            elif isinstance(current, dict):
                for key, child in current.items():
                    walk(child, offset + 1, [*path, str(key)], [*ancestors, current], None)
            return
        try:
            child = pointer_get(current, "/" + segment)
        except KeyError:
            return
        walk(child, offset + 1, [*path, segment], [*ancestors, current], None)

    if not segments:
        return (Match(root, "/", (), None),)
    walk(root, 0, [], [], None)
    return tuple(matches)


def select(match: Match, root: Any, expression: Any, default: Any = _MISSING) -> Any:
    if isinstance(expression, dict) and "const" in expression:
        return expression["const"]
    if not isinstance(expression, str):
        return expression
    if expression == "@index":
        return match.index
    if expression.startswith("@root"):
        pointer = expression.removeprefix("@root") or "/"
        return pointer_get(root, pointer, default)
    if expression.startswith("@ancestor["):
        close = expression.find("]")
        distance = int(expression[len("@ancestor[") : close])
        pointer = expression[close + 1 :] or "/"
        position = len(match.ancestors) - 1 - distance
        if position < 0:
            if default is _MISSING:
                raise KeyError(expression)
            return default
        return pointer_get(match.ancestors[position], pointer, default)
    if expression.startswith("@item"):
        pointer = expression.removeprefix("@item") or "/"
        return pointer_get(match.value, pointer, default)
    return pointer_get(match.value, expression, default)


@dataclass(frozen=True, slots=True)
class EntityMapping:
    collection: str
    fields: dict[str, Any]
    required: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class NormalizationMapping:
    mapping_id: str
    source_code: str
    schema_fingerprint: str
    mapping_version: str
    status: str
    entities: dict[str, EntityMapping]
    event_type_map: dict[str, str]

    @property
    def production_ready(self) -> bool:
        return self.status == "verified"

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "NormalizationMapping":
        entities = {
            name: EntityMapping(
                collection=str(spec["collection"]),
                fields=dict(spec.get("fields", {})),
                required=tuple(spec.get("required", ())),
            )
            for name, spec in payload.get("entities", {}).items()
        }
        mapping = cls(
            mapping_id=str(payload["mapping_id"]),
            source_code=str(payload["source_code"]),
            schema_fingerprint=str(payload["schema_fingerprint"]),
            mapping_version=str(payload["mapping_version"]),
            status=str(payload["status"]),
            entities=entities,
            event_type_map={str(key): str(value) for key, value in payload.get("event_type_map", {}).items()},
        )
        invalid = set(mapping.event_type_map.values()) - CANONICAL_AURA_EVENT_TYPES
        if invalid:
            raise ValueError(f"unsupported canonical aura event types: {sorted(invalid)}")
        return mapping

    @classmethod
    def from_path(cls, path: Path) -> "NormalizationMapping":
        return cls.from_dict(json.loads(path.read_text(encoding="utf-8")))


@dataclass(frozen=True, slots=True)
class CanonicalAuraEvent:
    encounter_id: str
    timestamp_ms: int
    event_type: str
    source_actor_id: str | None
    target_actor_id: str | None
    spell_id: str
    stacks: int | None
    event_ordinal: int
    raw_event_type: str
    raw_path: str


@dataclass(slots=True)
class CanonicalBatch:
    source_code: str
    mapping_id: str
    mapping_version: str
    normalizer_version: str = NORMALIZER_VERSION
    reports: list[dict[str, Any]] = field(default_factory=list)
    encounters: list[dict[str, Any]] = field(default_factory=list)
    actors: list[dict[str, Any]] = field(default_factory=list)
    participants: list[dict[str, Any]] = field(default_factory=list)
    aura_events: list[CanonicalAuraEvent] = field(default_factory=list)
    rejects: list[dict[str, Any]] = field(default_factory=list)

    def counts(self) -> dict[str, int]:
        return {
            "reports": len(self.reports),
            "encounters": len(self.encounters),
            "actors": len(self.actors),
            "participants": len(self.participants),
            "aura_events": len(self.aura_events),
            "rejects": len(self.rejects),
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_code": self.source_code,
            "mapping_id": self.mapping_id,
            "mapping_version": self.mapping_version,
            "normalizer_version": self.normalizer_version,
            "counts": self.counts(),
            "reports": self.reports,
            "encounters": self.encounters,
            "actors": self.actors,
            "participants": self.participants,
            "aura_events": [asdict(item) for item in self.aura_events],
            "rejects": self.rejects,
        }


def _extract_fields(match: Match, root: Any, spec: EntityMapping) -> tuple[dict[str, Any], list[str]]:
    record = {name: select(match, root, expression, None) for name, expression in spec.fields.items()}
    missing = [name for name in spec.required if record.get(name) in (None, "")]
    return record, missing


def normalize_payload(payload: Any, mapping: NormalizationMapping, *, schema_fingerprint: str) -> CanonicalBatch:
    if not mapping.production_ready:
        raise ValueError(f"normalization mapping {mapping.mapping_id!r} is not verified")
    if mapping.schema_fingerprint != schema_fingerprint:
        raise ValueError(
            f"schema fingerprint mismatch: mapping={mapping.schema_fingerprint} payload={schema_fingerprint}"
        )
    batch = CanonicalBatch(mapping.source_code, mapping.mapping_id, mapping.mapping_version)
    extracted: dict[str, list[tuple[Match, dict[str, Any]]]] = {}
    for entity_name, spec in mapping.entities.items():
        records: list[tuple[Match, dict[str, Any]]] = []
        for match in find_matches(payload, spec.collection):
            if not isinstance(match.value, dict):
                batch.rejects.append({"entity": entity_name, "path": match.path, "reason": "item_not_object"})
                continue
            record, missing = _extract_fields(match, payload, spec)
            if missing:
                batch.rejects.append(
                    {"entity": entity_name, "path": match.path, "reason": "missing_required", "fields": missing}
                )
                continue
            records.append((match, record))
        extracted[entity_name] = records

    report_ids: dict[str, str] = {}
    for _match, record in extracted.get("reports", []):
        source_report_id = str(record["source_report_id"])
        report_id = stable_id("report", mapping.source_code, source_report_id)
        report_ids[source_report_id] = report_id
        batch.reports.append({"report_id": report_id, **record})

    encounter_ids: dict[str, str] = {}
    for _match, record in extracted.get("encounters", []):
        source_encounter_id = str(record["source_encounter_id"])
        source_report_id = str(record.get("source_report_id") or "")
        if source_report_id and source_report_id not in report_ids:
            batch.rejects.append({"entity": "encounters", "reason": "unknown_report", "source_report_id": source_report_id})
            continue
        encounter_id = stable_id("encounter", mapping.source_code, source_report_id, source_encounter_id)
        encounter_ids[source_encounter_id] = encounter_id
        batch.encounters.append(
            {"encounter_id": encounter_id, "report_id": report_ids.get(source_report_id), **record}
        )

    actor_ids: dict[str, str] = {}
    for _match, record in extracted.get("actors", []):
        source_actor_id = str(record["source_actor_id"])
        actor_id = stable_id("actor", mapping.source_code, source_actor_id)
        actor_ids[source_actor_id] = actor_id
        batch.actors.append({"actor_id": actor_id, **record})

    for _match, record in extracted.get("participants", []):
        source_encounter_id = str(record["source_encounter_id"])
        source_actor_id = str(record["source_actor_id"])
        if source_encounter_id not in encounter_ids or source_actor_id not in actor_ids:
            batch.rejects.append(
                {
                    "entity": "participants",
                    "reason": "unknown_reference",
                    "source_encounter_id": source_encounter_id,
                    "source_actor_id": source_actor_id,
                }
            )
            continue
        batch.participants.append(
            {
                "encounter_id": encounter_ids[source_encounter_id],
                "actor_id": actor_ids[source_actor_id],
                **record,
            }
        )

    for sequence, (match, record) in enumerate(extracted.get("aura_events", []), start=1):
        source_encounter_id = str(record["source_encounter_id"])
        if source_encounter_id not in encounter_ids:
            batch.rejects.append(
                {"entity": "aura_events", "path": match.path, "reason": "unknown_encounter", "value": source_encounter_id}
            )
            continue
        raw_event_type = str(record["event_type"])
        canonical_type = mapping.event_type_map.get(raw_event_type)
        if canonical_type is None:
            batch.rejects.append(
                {"entity": "aura_events", "path": match.path, "reason": "unmapped_event_type", "value": raw_event_type}
            )
            continue
        source_actor = record.get("source_actor_id")
        target_actor = record.get("target_actor_id")
        ordinal = record.get("event_ordinal")
        batch.aura_events.append(
            CanonicalAuraEvent(
                encounter_id=encounter_ids[source_encounter_id],
                timestamp_ms=int(record["timestamp_ms"]),
                event_type=canonical_type,
                source_actor_id=actor_ids.get(str(source_actor)) if source_actor not in (None, "") else None,
                target_actor_id=actor_ids.get(str(target_actor)) if target_actor not in (None, "") else None,
                spell_id=str(record["spell_id"]),
                stacks=int(record["stacks"]) if record.get("stacks") not in (None, "") else None,
                event_ordinal=int(ordinal) if ordinal not in (None, "") else sequence,
                raw_event_type=raw_event_type,
                raw_path=match.path,
            )
        )
    batch.aura_events.sort(key=lambda item: (item.encounter_id, item.timestamp_ms, item.event_ordinal))
    return batch
