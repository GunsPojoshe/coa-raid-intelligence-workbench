from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from typing import Iterable

from .canonical import CanonicalAuraEvent

RECONSTRUCTION_VERSION = "aura-state-v1"


@dataclass(slots=True)
class AuraInterval:
    interval_id: str
    encounter_id: str
    spell_id: str
    source_actor_id: str | None
    target_actor_id: str
    started_at_ms: int
    ended_at_ms: int | None
    stack_count: int | None
    max_stack_count: int | None
    application_ordinal: int
    removal_ordinal: int | None
    refresh_count: int
    termination_reason: str
    reconstruction_version: str = RECONSTRUCTION_VERSION

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class AuraStateResult:
    intervals: tuple[AuraInterval, ...]
    anomalies: tuple[dict[str, object], ...]


def _interval_id(event: CanonicalAuraEvent) -> str:
    material = "\0".join(
        [
            event.encounter_id,
            event.spell_id,
            event.source_actor_id or "",
            event.target_actor_id or "",
            str(event.timestamp_ms),
            str(event.event_ordinal),
            RECONSTRUCTION_VERSION,
        ]
    )
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def reconstruct_aura_intervals(
    events: Iterable[CanonicalAuraEvent],
    *,
    encounter_end_ms: dict[str, int] | None = None,
) -> AuraStateResult:
    active: dict[tuple[str, str, str | None, str], AuraInterval] = {}
    completed: list[AuraInterval] = []
    anomalies: list[dict[str, object]] = []
    ordered = sorted(events, key=lambda item: (item.encounter_id, item.timestamp_ms, item.event_ordinal))
    for event in ordered:
        if not event.target_actor_id:
            anomalies.append({"reason": "missing_target", "event_ordinal": event.event_ordinal, "path": event.raw_path})
            continue
        key = (event.encounter_id, event.spell_id, event.source_actor_id, event.target_actor_id)
        current = active.get(key)
        if event.event_type == "APPLIED":
            if current is not None:
                current.ended_at_ms = event.timestamp_ms
                current.removal_ordinal = event.event_ordinal
                current.termination_reason = "reapplied"
                completed.append(current)
            stacks = event.stacks if event.stacks is not None else 1
            active[key] = AuraInterval(
                interval_id=_interval_id(event),
                encounter_id=event.encounter_id,
                spell_id=event.spell_id,
                source_actor_id=event.source_actor_id,
                target_actor_id=event.target_actor_id,
                started_at_ms=event.timestamp_ms,
                ended_at_ms=None,
                stack_count=stacks,
                max_stack_count=stacks,
                application_ordinal=event.event_ordinal,
                removal_ordinal=None,
                refresh_count=0,
                termination_reason="active",
            )
        elif event.event_type == "REFRESH":
            if current is None:
                anomalies.append({"reason": "refresh_without_apply", "event_ordinal": event.event_ordinal, "path": event.raw_path})
                continue
            current.refresh_count += 1
            if event.stacks is not None:
                current.stack_count = event.stacks
                current.max_stack_count = max(current.max_stack_count or event.stacks, event.stacks)
        elif event.event_type == "STACK_CHANGE":
            if current is None:
                anomalies.append({"reason": "stack_without_apply", "event_ordinal": event.event_ordinal, "path": event.raw_path})
                continue
            current.stack_count = event.stacks
            if event.stacks is not None:
                current.max_stack_count = max(current.max_stack_count or event.stacks, event.stacks)
        elif event.event_type == "REMOVED":
            if current is None:
                anomalies.append({"reason": "remove_without_apply", "event_ordinal": event.event_ordinal, "path": event.raw_path})
                continue
            current.ended_at_ms = event.timestamp_ms
            current.removal_ordinal = event.event_ordinal
            current.termination_reason = "removed"
            completed.append(current)
            del active[key]
        else:
            anomalies.append({"reason": "unsupported_event_type", "event_ordinal": event.event_ordinal, "value": event.event_type})
    ends = encounter_end_ms or {}
    for current in active.values():
        if current.encounter_id in ends:
            current.ended_at_ms = ends[current.encounter_id]
            current.termination_reason = "encounter_end"
        else:
            current.termination_reason = "open"
        completed.append(current)
    completed.sort(key=lambda item: (item.encounter_id, item.started_at_ms, item.application_ordinal))
    return AuraStateResult(tuple(completed), tuple(anomalies))
