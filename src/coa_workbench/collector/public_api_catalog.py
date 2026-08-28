from __future__ import annotations

import gzip
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

PUBLIC_API_CATALOG_REVIEW_VERSION = "public-api-catalog-v1"


@dataclass(frozen=True, slots=True)
class PhaseCatalogRecord:
    phase_number: int
    is_active: bool
    end_date: str | None
    location_count: int
    main_location_count: int
    progression_location_count: int
    world_boss_location_count: int


@dataclass(frozen=True, slots=True)
class BossCatalogRecord:
    boss_id: int
    has_location: bool
    has_display_order: bool
    has_instance_type: bool


def _mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    return value


def _integer(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{label} must be an integer")
    return value


def _boolean(value: Any, label: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{label} must be a boolean")
    return value


def _nullable_string(value: Any, label: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{label} must be a string or null")
    return value


def load_latest_public_api_payload(
    raw_root: Path,
    *,
    source_code: str,
    endpoint_code: str,
) -> Mapping[str, Any]:
    pattern = (
        f"source={source_code}/year=*/month=*/endpoint={endpoint_code}/observations/*.json"
    )
    candidates: list[tuple[str, str, Path]] = []
    for manifest_path in raw_root.glob(pattern):
        manifest = _mapping(
            json.loads(manifest_path.read_text(encoding="utf-8")),
            "raw observation manifest",
        )
        fetched_at = str(manifest.get("fetched_at") or "")
        content_manifest_path = manifest.get("content_manifest_path")
        if not fetched_at or not isinstance(content_manifest_path, str):
            continue
        candidates.append((fetched_at, manifest_path.as_posix(), Path(content_manifest_path)))
    if not candidates:
        raise FileNotFoundError(
            f"no archived observation for source={source_code!r}, endpoint={endpoint_code!r}"
        )

    _fetched_at, _manifest_name, relative_content_manifest = max(candidates)
    content_manifest = _mapping(
        json.loads((raw_root / relative_content_manifest).read_text(encoding="utf-8")),
        "raw content manifest",
    )
    payload_path = content_manifest.get("payload_path")
    if not isinstance(payload_path, str) or not payload_path:
        raise ValueError("raw content manifest is missing payload_path")
    with gzip.open(raw_root / payload_path, "rb") as stream:
        payload = json.loads(stream.read())
    return _mapping(payload, "archived public API payload")


def parse_public_api_phases(payload: Mapping[str, Any]) -> tuple[PhaseCatalogRecord, ...]:
    if payload.get("success") is not True:
        raise ValueError("public API phases response was not successful")
    raw_phases = payload.get("phases")
    if not isinstance(raw_phases, list):
        raise ValueError("public API phases response must contain a phases array")

    result: list[PhaseCatalogRecord] = []
    for index, raw_phase in enumerate(raw_phases):
        phase = _mapping(raw_phase, f"phases[{index}]")
        phase_number = _integer(phase.get("phase_number"), f"phases[{index}].phase_number")
        is_active = _boolean(phase.get("is_active"), f"phases[{index}].is_active")
        if "end_date" not in phase:
            raise ValueError(f"phases[{index}].end_date is required for current-phase review")
        end_date = _nullable_string(phase.get("end_date"), f"phases[{index}].end_date")

        raw_locations = phase.get("locations", [])
        if not isinstance(raw_locations, list):
            raise ValueError(f"phases[{index}].locations must be an array")
        main_count = 0
        progression_count = 0
        world_boss_count = 0
        for location_index, raw_location in enumerate(raw_locations):
            location = _mapping(
                raw_location,
                f"phases[{index}].locations[{location_index}]",
            )
            if not isinstance(location.get("location"), str):
                raise ValueError(
                    f"phases[{index}].locations[{location_index}].location must be a string"
                )
            main_count += _boolean(
                location.get("is_main"),
                f"phases[{index}].locations[{location_index}].is_main",
            )
            progression_count += _boolean(
                location.get("track_progression"),
                f"phases[{index}].locations[{location_index}].track_progression",
            )
            world_boss_count += _boolean(
                location.get("is_world_boss"),
                f"phases[{index}].locations[{location_index}].is_world_boss",
            )

        result.append(
            PhaseCatalogRecord(
                phase_number=phase_number,
                is_active=is_active,
                end_date=end_date,
                location_count=len(raw_locations),
                main_location_count=main_count,
                progression_location_count=progression_count,
                world_boss_location_count=world_boss_count,
            )
        )
    return tuple(result)


def parse_public_api_bosses(payload: Mapping[str, Any]) -> tuple[BossCatalogRecord, ...]:
    if payload.get("success") is not True:
        raise ValueError("public API bosses response was not successful")
    raw_bosses = payload.get("bosses")
    if not isinstance(raw_bosses, list):
        raise ValueError("public API bosses response must contain a bosses array")
    count = payload.get("count")
    if count is not None and _integer(count, "bosses.count") != len(raw_bosses):
        raise ValueError("public API bosses count does not match bosses array length")

    result: list[BossCatalogRecord] = []
    for index, raw_boss in enumerate(raw_bosses):
        boss = _mapping(raw_boss, f"bosses[{index}]")
        boss_id = _integer(boss.get("boss_id"), f"bosses[{index}].boss_id")
        name = boss.get("name")
        if not isinstance(name, str) or not name:
            raise ValueError(f"bosses[{index}].name must be a non-empty string")
        _nullable_string(boss.get("location"), f"bosses[{index}].location")
        display_order = boss.get("display_order")
        if display_order is not None:
            _integer(display_order, f"bosses[{index}].display_order")
        _nullable_string(boss.get("instance_type"), f"bosses[{index}].instance_type")
        result.append(
            BossCatalogRecord(
                boss_id=boss_id,
                has_location=boss.get("location") is not None,
                has_display_order=display_order is not None,
                has_instance_type=boss.get("instance_type") is not None,
            )
        )
    return tuple(result)


def select_current_phase_number(phases: tuple[PhaseCatalogRecord, ...]) -> int:
    candidates = [phase for phase in phases if phase.is_active and phase.end_date is None]
    if len(candidates) != 1:
        raise ValueError(
            "current phase selection requires exactly one phase with is_active=true and end_date=null"
        )
    return candidates[0].phase_number


def build_public_api_catalog_review(
    phases_payload: Mapping[str, Any],
    bosses_payload: Mapping[str, Any],
) -> dict[str, Any]:
    phases = parse_public_api_phases(phases_payload)
    bosses = parse_public_api_bosses(bosses_payload)
    active = [phase for phase in phases if phase.is_active]
    current_by_end = [phase for phase in phases if phase.end_date is None]
    active_current = [phase for phase in phases if phase.is_active and phase.end_date is None]
    phase_numbers = [phase.phase_number for phase in phases]
    boss_ids = [boss.boss_id for boss in bosses]

    return {
        "review_version": PUBLIC_API_CATALOG_REVIEW_VERSION,
        "phase_catalog": {
            "phase_count": len(phases),
            "unique_phase_number_count": len(set(phase_numbers)),
            "duplicate_phase_number_count": len(phase_numbers) - len(set(phase_numbers)),
            "active_phase_count": len(active),
            "current_by_null_end_date_count": len(current_by_end),
            "active_current_candidate_count": len(active_current),
            "active_current_candidate_has_locations": bool(
                len(active_current) == 1 and active_current[0].location_count > 0
            ),
            "phase_with_main_location_count": sum(phase.main_location_count > 0 for phase in phases),
            "phase_with_progression_location_count": sum(
                phase.progression_location_count > 0 for phase in phases
            ),
            "phase_with_world_boss_location_count": sum(
                phase.world_boss_location_count > 0 for phase in phases
            ),
        },
        "boss_catalog": {
            "boss_count": len(bosses),
            "unique_stable_boss_id_count": len(set(boss_ids)),
            "duplicate_stable_boss_id_count": len(boss_ids) - len(set(boss_ids)),
            "boss_with_location_count": sum(boss.has_location for boss in bosses),
            "boss_with_display_order_count": sum(boss.has_display_order for boss in bosses),
            "boss_with_instance_type_count": sum(boss.has_instance_type for boss in bosses),
        },
        "selection": {
            "current_phase_selectable": len(active_current) == 1,
            "selector": "unique_is_active_true_and_end_date_null",
            "phase_value_included": False,
        },
        "verification": {
            "openapi_end_date_current_semantics_used": True,
            "boss_id_stable_index_semantics_used": True,
            "real_payload_shapes_reviewed": True,
            "statistics_payload_reviewed": False,
            "planner_scoring_allowed": False,
        },
        "privacy": {
            "phase_numbers_included": False,
            "phase_names_included": False,
            "location_names_included": False,
            "boss_ids_included": False,
            "boss_names_included": False,
            "raw_paths_included": False,
            "raw_payloads_included": False,
        },
        "public_release_safe": True,
    }


__all__ = [
    "PUBLIC_API_CATALOG_REVIEW_VERSION",
    "BossCatalogRecord",
    "PhaseCatalogRecord",
    "build_public_api_catalog_review",
    "load_latest_public_api_payload",
    "parse_public_api_bosses",
    "parse_public_api_phases",
    "select_current_phase_number",
]
