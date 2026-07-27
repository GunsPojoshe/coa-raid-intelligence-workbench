from __future__ import annotations

import gzip
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .aura_state import reconstruct_aura_intervals
from .canonical import CanonicalAuraEvent, stable_id
from .schema_inspector import structure_fingerprint


@dataclass(frozen=True, slots=True)
class AuraTimelineContract:
    mapping_id: str
    source_code: str
    mapping_version: str
    status: str
    schema_fingerprints: tuple[str, ...]
    event_type_map: dict[str, str]
    required_top_level: tuple[str, ...]
    required_event_fields: tuple[str, ...]

    @property
    def production_ready(self) -> bool:
        return self.status == "verified"

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "AuraTimelineContract":
        return cls(
            mapping_id=str(payload["mapping_id"]),
            source_code=str(payload["source_code"]),
            mapping_version=str(payload["mapping_version"]),
            status=str(payload["status"]),
            schema_fingerprints=tuple(str(value) for value in payload["schema_fingerprints"]),
            event_type_map={
                str(key): str(value) for key, value in payload.get("event_type_map", {}).items()
            },
            required_top_level=tuple(str(value) for value in payload.get("required_top_level", ())),
            required_event_fields=tuple(
                str(value) for value in payload.get("required_event_fields", ())
            ),
        )

    @classmethod
    def from_path(cls, path: Path) -> "AuraTimelineContract":
        return cls.from_dict(json.loads(path.read_text(encoding="utf-8")))


def _resolve_archived_path(value: str, *, raw_root: Path) -> Path:
    root = raw_root.resolve()
    candidate = Path(value)
    if candidate.is_absolute():
        path = candidate.resolve()
    elif len(value) == 64 and all(char in "0123456789abcdefABCDEF" for char in value):
        matches = sorted(root.glob(f"**/{value.casefold()}.json.gz"))
        if not matches:
            raise FileNotFoundError("archived JSON payload hash not found")
        path = matches[0].resolve()
    else:
        path = (root / candidate).resolve()
    if not path.is_relative_to(root) or not path.is_file() or not path.name.endswith(".json.gz"):
        raise ValueError("payload must be a gzip JSON archive below raw-root")
    return path


def load_archived_json(value: str, *, raw_root: Path) -> tuple[bytes, Any, str]:
    path = _resolve_archived_path(value, raw_root=raw_root)
    body = gzip.decompress(path.read_bytes())
    payload = json.loads(body)
    return body, payload, path.relative_to(raw_root.resolve()).as_posix()


def _required_object(payload: Any, field: str) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("aura timeline payload must be an object")
    value = payload.get(field)
    if not isinstance(value, dict):
        raise ValueError(f"aura timeline field {field!r} must be an object")
    return value


def _required_list(payload: Any, field: str) -> list[Any]:
    if not isinstance(payload, dict):
        raise ValueError("aura timeline payload must be an object")
    value = payload.get(field)
    if not isinstance(value, list):
        raise ValueError(f"aura timeline field {field!r} must be an array")
    return value


def _canonical_actor_id(source_code: str, source_actor_id: Any) -> str:
    return stable_id("actor", source_code, str(source_actor_id))


def normalize_single_encounter_aura_timeline(
    payload: Any,
    *,
    source_encounter_id: str,
    contract: AuraTimelineContract,
) -> dict[str, Any]:
    if not contract.production_ready:
        raise ValueError(f"aura timeline mapping {contract.mapping_id!r} is not verified")
    if not isinstance(payload, dict):
        raise ValueError("aura timeline payload must be an object")
    missing_top_level = [field for field in contract.required_top_level if field not in payload]
    if missing_top_level:
        raise ValueError(f"aura timeline payload is missing fields: {missing_top_level}")
    fingerprint = structure_fingerprint(payload)
    if fingerprint not in contract.schema_fingerprints:
        raise ValueError(
            "schema fingerprint mismatch: "
            f"allowed={sorted(contract.schema_fingerprints)} payload={fingerprint}"
        )

    report_id = str(payload["report_id"])
    encounter_id = stable_id("encounter", contract.source_code, report_id, source_encounter_id)
    duration_ms = int(payload["encounter_duration_ms"])
    spell = _required_object(payload, "spell")
    spell_id = str(spell["id"])
    rows = _required_list(payload, "series")
    events: list[CanonicalAuraEvent] = []
    ignored: list[dict[str, Any]] = []
    rejects: list[dict[str, Any]] = []

    for ordinal, row in enumerate(rows):
        path = f"/series/{ordinal}"
        if not isinstance(row, dict):
            rejects.append({"path": path, "reason": "item_not_object"})
            continue
        raw_event_type = row.get("event_type")
        if (
            raw_event_type is None
            and row.get("source_id") is None
            and row.get("target_id") is None
        ):
            ignored.append({"path": path, "reason": "timeline_baseline"})
            continue
        missing = [field for field in contract.required_event_fields if row.get(field) is None]
        if missing:
            rejects.append({"path": path, "reason": "missing_required", "fields": missing})
            continue
        canonical_type = contract.event_type_map.get(str(raw_event_type))
        if canonical_type is None:
            rejects.append(
                {
                    "path": path,
                    "reason": "unmapped_event_type",
                    "value": str(raw_event_type),
                }
            )
            continue
        source_actor_id = _canonical_actor_id(contract.source_code, row["source_id"])
        target_actor_id = _canonical_actor_id(contract.source_code, row["target_id"])
        stacks = row.get("event_stacks")
        events.append(
            CanonicalAuraEvent(
                encounter_id=encounter_id,
                timestamp_ms=int(row["ms"]),
                event_type=canonical_type,
                source_actor_id=source_actor_id,
                target_actor_id=target_actor_id,
                spell_id=spell_id,
                stacks=int(stacks) if stacks is not None else None,
                event_ordinal=ordinal,
                raw_event_type=str(raw_event_type),
                raw_path=path,
            )
        )

    events.sort(key=lambda item: (item.timestamp_ms, item.event_ordinal))
    return {
        "mapping_id": contract.mapping_id,
        "mapping_version": contract.mapping_version,
        "source_code": contract.source_code,
        "schema_fingerprint": fingerprint,
        "source_report_id": report_id,
        "source_encounter_id": str(source_encounter_id),
        "encounter_id": encounter_id,
        "duration_ms": duration_ms,
        "spell_id": spell_id,
        "events": events,
        "ignored": ignored,
        "rejects": rejects,
    }


def _reference_intervals(
    payload: Any,
    *,
    source_code: str,
    expected_report_id: str,
    expected_spell_id: str,
) -> list[dict[str, Any]]:
    if not isinstance(payload, dict) or not isinstance(payload.get("sources"), list):
        raise ValueError("reference payload must be a debuff_sources object")
    if str(payload.get("report_id")) != expected_report_id:
        raise ValueError("reference report_id does not match timeline report_id")
    if str(payload.get("spell_id")) != expected_spell_id:
        raise ValueError("reference spell_id does not match timeline spell_id")
    target_source_id = payload.get("target_id")
    if target_source_id is None:
        raise ValueError("reference payload has no target_id")
    target_actor_id = _canonical_actor_id(source_code, target_source_id)
    intervals: list[dict[str, Any]] = []
    for source_index, source in enumerate(payload["sources"]):
        if not isinstance(source, dict) or source.get("source_id") is None:
            raise ValueError(f"reference source {source_index} is invalid")
        source_actor_id = _canonical_actor_id(source_code, source["source_id"])
        source_intervals = source.get("intervals")
        if not isinstance(source_intervals, list):
            raise ValueError(f"reference source {source_index} has no intervals array")
        for interval_index, interval in enumerate(source_intervals):
            if not isinstance(interval, dict):
                raise ValueError(
                    f"reference interval {source_index}/{interval_index} is not an object"
                )
            intervals.append(
                {
                    "source_actor_id": source_actor_id,
                    "target_actor_id": target_actor_id,
                    "spell_id": expected_spell_id,
                    "started_at_ms": int(interval["start_ms"]),
                    "ended_at_ms": int(interval["end_ms"]),
                    "max_stack_count": int(interval["max_stacks"]),
                }
            )
    intervals.sort(
        key=lambda item: (
            item["source_actor_id"],
            item["target_actor_id"],
            item["started_at_ms"],
            item["ended_at_ms"],
        )
    )
    return intervals


def validate_single_encounter_aura_capture(
    timeline_payload: Any,
    reference_payload: Any,
    *,
    source_encounter_id: str,
    contract: AuraTimelineContract,
) -> dict[str, Any]:
    normalized = normalize_single_encounter_aura_timeline(
        timeline_payload,
        source_encounter_id=source_encounter_id,
        contract=contract,
    )
    state = reconstruct_aura_intervals(
        normalized["events"],
        encounter_end_ms={normalized["encounter_id"]: normalized["duration_ms"]},
    )
    actual = [
        {
            "source_actor_id": interval.source_actor_id,
            "target_actor_id": interval.target_actor_id,
            "spell_id": interval.spell_id,
            "started_at_ms": interval.started_at_ms,
            "ended_at_ms": interval.ended_at_ms,
            "max_stack_count": interval.max_stack_count,
            "termination_reason": interval.termination_reason,
        }
        for interval in state.intervals
    ]
    actual.sort(
        key=lambda item: (
            item["source_actor_id"] or "",
            item["target_actor_id"],
            item["started_at_ms"],
            item["ended_at_ms"] if item["ended_at_ms"] is not None else -1,
        )
    )
    expected = _reference_intervals(
        reference_payload,
        source_code=contract.source_code,
        expected_report_id=normalized["source_report_id"],
        expected_spell_id=normalized["spell_id"],
    )
    comparable_actual = [
        {
            key: value
            for key, value in interval.items()
            if key != "termination_reason"
        }
        for interval in actual
    ]
    matched = comparable_actual == expected and not normalized["rejects"] and not state.anomalies
    return {
        "status": "matched" if matched else "mismatch",
        "mapping_id": normalized["mapping_id"],
        "mapping_version": normalized["mapping_version"],
        "schema_fingerprint": normalized["schema_fingerprint"],
        "source_report_id": normalized["source_report_id"],
        "source_encounter_id": normalized["source_encounter_id"],
        "encounter_id": normalized["encounter_id"],
        "spell_id": normalized["spell_id"],
        "duration_ms": normalized["duration_ms"],
        "event_count": len(normalized["events"]),
        "ignored": normalized["ignored"],
        "rejects": normalized["rejects"],
        "anomalies": list(state.anomalies),
        "actual_interval_count": len(actual),
        "expected_interval_count": len(expected),
        "actual_intervals": actual,
        "expected_intervals": expected,
    }


def validate_archived_aura_capture(
    timeline_value: str,
    reference_value: str,
    *,
    raw_root: Path,
    source_encounter_id: str,
    contract: AuraTimelineContract,
) -> dict[str, Any]:
    timeline_body, timeline_payload, timeline_path = load_archived_json(
        timeline_value, raw_root=raw_root
    )
    reference_body, reference_payload, reference_path = load_archived_json(
        reference_value, raw_root=raw_root
    )
    result = validate_single_encounter_aura_capture(
        timeline_payload,
        reference_payload,
        source_encounter_id=source_encounter_id,
        contract=contract,
    )
    result["provenance"] = {
        "timeline_payload_hash": hashlib.sha256(timeline_body).hexdigest(),
        "timeline_payload_path": timeline_path,
        "reference_payload_hash": hashlib.sha256(reference_body).hexdigest(),
        "reference_payload_path": reference_path,
    }
    return result
