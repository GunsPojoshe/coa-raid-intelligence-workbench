from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Mapping

PUBLIC_API_STATISTICS_NORMALIZER_VERSION = "public-api-statistics-normalizer-v1"

_DIFFICULTIES = {"normal", "heroic", "mythic", "ascended", "all"}
_METRICS = {"avg_dps", "avg_hps", "avg_dtps"}
_DAMAGE_MODES = {"standard", "boss-only", "trash"}
_ROLES = {"tank", "dps", "tanks-and-dps", "support"}
_REQUIRED_METRIC_FIELDS = frozenset(
    {"avg", "median", "max", "min", "total_parses", "percentiles"}
)
_DOCUMENTED_QUERY_KEYS = frozenset(
    {
        "phase",
        "difficulty",
        "metric",
        "bracket",
        "location",
        "bossId",
        "damageMode",
        "role",
        "class",
        "spec",
        "weekNumber",
        "realm",
    }
)
_QUERY_RESPONSE_FIELDS = {
    "phase": "phase",
    "difficulty": "difficulty",
    "metric": "metric",
    "bracket": "bracket",
    "location": "location",
    "bossId": "boss_id",
    "damageMode": "damage_mode",
    "weekNumber": "week_number",
}


@dataclass(frozen=True, slots=True)
class PublicApiStatisticsDimensions:
    phase: int
    difficulty: str
    metric: str
    bracket: str | None
    location: str | None
    boss_id: int | None
    damage_mode: str | None
    role: str | None
    class_filter: str | None
    spec_filter: str | None
    week_number: int | None
    realm: str | None
    day_number: int | None


@dataclass(frozen=True, slots=True)
class PublicApiClassSummary:
    class_name: str
    total_parses: int


@dataclass(frozen=True, slots=True)
class PublicApiStatisticRecord:
    class_name: str
    spec_name: str
    avg: float
    median: float
    maximum: float
    minimum: float
    total_parses: int
    percentiles: tuple[tuple[str, float], ...]


@dataclass(frozen=True, slots=True)
class PublicApiStatisticsBatch:
    dimensions: PublicApiStatisticsDimensions
    class_summaries: tuple[PublicApiClassSummary, ...]
    records: tuple[PublicApiStatisticRecord, ...]

    @property
    def percentile_value_count(self) -> int:
        return sum(len(record.percentiles) for record in self.records)


def _mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    return value


def _integer(value: Any, label: str, *, minimum: int | None = None) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{label} must be an integer")
    if minimum is not None and value < minimum:
        raise ValueError(f"{label} must be at least {minimum}")
    return value


def _nullable_integer(value: Any, label: str, *, minimum: int | None = None) -> int | None:
    if value is None:
        return None
    return _integer(value, label, minimum=minimum)


def _number(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be a finite number")
    rendered = float(value)
    if not math.isfinite(rendered):
        raise ValueError(f"{label} must be a finite number")
    return rendered


def _string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be a non-empty string")
    return value


def _nullable_string(value: Any, label: str) -> str | None:
    if value is None:
        return None
    return _string(value, label)


def _nullable_scalar_text(value: Any, label: str) -> str | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        raise ValueError(f"{label} must be a scalar or null")
    rendered = str(value)
    if not rendered:
        raise ValueError(f"{label} cannot be empty")
    return rendered


def _render_query_scalar(value: Any, label: str) -> str:
    if value is None or isinstance(value, bool) or not isinstance(value, (str, int, float)):
        raise ValueError(f"{label} cannot be reconstructed from the response")
    rendered = str(value)
    if not rendered:
        raise ValueError(f"{label} cannot be reconstructed from an empty value")
    return rendered


def _resolved_query_values(
    payload: Mapping[str, Any],
    *,
    query_keys: tuple[str, ...],
    query_values: Mapping[str, str] | None,
) -> dict[str, str]:
    unknown = sorted(set(query_keys) - _DOCUMENTED_QUERY_KEYS)
    if unknown:
        raise ValueError(f"unreviewed public API query keys in archived capture: {unknown}")

    provided = dict(query_values or {})
    extra_values = sorted(set(provided) - set(query_keys))
    if extra_values:
        raise ValueError(f"archived query values have keys absent from query_keys: {extra_values}")

    resolved: dict[str, str] = {}
    missing: list[str] = []
    for key in query_keys:
        if key in provided:
            value = _string(provided[key], f"query_values[{key!r}]")
        else:
            response_field = _QUERY_RESPONSE_FIELDS.get(key)
            if response_field is None or payload.get(response_field) is None:
                missing.append(key)
                continue
            value = _render_query_scalar(payload[response_field], f"response.{response_field}")
        response_field = _QUERY_RESPONSE_FIELDS.get(key)
        if response_field is not None and payload.get(response_field) is not None:
            echoed = _render_query_scalar(payload[response_field], f"response.{response_field}")
            if echoed != value:
                raise ValueError(
                    f"archived query value for {key!r} conflicts with echoed response field"
                )
        resolved[key] = value

    if missing:
        names = ", ".join(sorted(missing))
        raise ValueError(
            "archived statistics capture lacks private values for non-echoed query dimensions: "
            f"{names}; bounded recapture is required"
        )
    return resolved


def _metric_object(value: Any, label: str) -> Mapping[str, Any]:
    metric = _mapping(value, label)
    keys = frozenset(str(key) for key in metric)
    if keys != _REQUIRED_METRIC_FIELDS:
        missing = sorted(_REQUIRED_METRIC_FIELDS - keys)
        extra = sorted(keys - _REQUIRED_METRIC_FIELDS)
        raise ValueError(
            f"{label} must contain the exact documented metric fields; missing={missing}, extra={extra}"
        )
    return metric


def _looks_like_metric_object(value: Any) -> bool:
    return isinstance(value, dict) and frozenset(str(key) for key in value) == _REQUIRED_METRIC_FIELDS


def _parse_metric(
    value: Any,
    *,
    class_name: str,
    spec_name: str,
    label: str,
) -> PublicApiStatisticRecord:
    metric = _metric_object(value, label)
    percentiles = _mapping(metric["percentiles"], f"{label}.percentiles")
    percentile_rows: list[tuple[str, float]] = []
    for percentile_key in sorted(percentiles):
        key = _string(str(percentile_key), f"{label}.percentiles key")
        percentile_rows.append(
            (key, _number(percentiles[percentile_key], f"{label}.percentiles[{key!r}]"))
        )
    return PublicApiStatisticRecord(
        class_name=class_name,
        spec_name=spec_name,
        avg=_number(metric["avg"], f"{label}.avg"),
        median=_number(metric["median"], f"{label}.median"),
        maximum=_number(metric["max"], f"{label}.max"),
        minimum=_number(metric["min"], f"{label}.min"),
        total_parses=_integer(metric["total_parses"], f"{label}.total_parses", minimum=0),
        percentiles=tuple(percentile_rows),
    )


def _spec_container(class_payload: Mapping[str, Any], label: str) -> Mapping[str, Any]:
    candidates: list[Mapping[str, Any]] = []
    candidate_keys: list[str] = []
    for key, value in class_payload.items():
        if not isinstance(value, dict) or not value:
            continue
        if all(_looks_like_metric_object(child) for child in value.values()):
            candidates.append(value)
            candidate_keys.append(str(key))
    if len(candidates) != 1:
        raise ValueError(
            f"{label} must contain exactly one observed spec-to-metric object; "
            f"found {len(candidates)}"
        )
    selected_key = candidate_keys[0]
    for key, value in class_payload.items():
        if str(key) == selected_key:
            continue
        if isinstance(value, (dict, list)):
            raise ValueError(f"{label}.{key} is an unreviewed nested structure")
    return candidates[0]


def parse_public_api_statistics(
    payload: Mapping[str, Any],
    *,
    query_keys: tuple[str, ...] = (),
    query_values: Mapping[str, str] | None = None,
) -> PublicApiStatisticsBatch:
    """Parse the reviewed StatisticsResponse shape without inferring gameplay semantics."""
    if payload.get("success") is not True:
        raise ValueError("public API statistics response was not successful")
    statistics = _mapping(payload.get("statistics"), "statistics")
    if not statistics:
        raise ValueError("statistics must contain at least one class entry")

    resolved_query = _resolved_query_values(
        payload,
        query_keys=query_keys,
        query_values=query_values,
    )

    phase = _integer(payload.get("phase"), "phase", minimum=1)
    difficulty = _string(payload.get("difficulty"), "difficulty")
    metric_code = _string(payload.get("metric"), "metric")
    if difficulty not in _DIFFICULTIES:
        raise ValueError("difficulty is outside the documented enum")
    if metric_code not in _METRICS:
        raise ValueError("metric is outside the documented enum")

    damage_mode = resolved_query.get("damageMode") or _nullable_string(
        payload.get("damage_mode"), "damage_mode"
    )
    if damage_mode is not None and damage_mode not in _DAMAGE_MODES:
        raise ValueError("damage_mode is outside the documented enum")
    role = resolved_query.get("role")
    if role is not None and role not in _ROLES:
        raise ValueError("role is outside the documented enum")

    bracket = resolved_query.get("bracket") or _nullable_scalar_text(
        payload.get("bracket"), "bracket"
    )
    location = resolved_query.get("location") or _nullable_string(
        payload.get("location"), "location"
    )
    boss_id = (
        int(resolved_query["bossId"])
        if "bossId" in resolved_query
        else _nullable_integer(payload.get("boss_id"), "boss_id")
    )
    week_number = (
        int(resolved_query["weekNumber"])
        if "weekNumber" in resolved_query
        else _nullable_integer(payload.get("week_number"), "week_number")
    )
    day_number = _nullable_integer(payload.get("day_number"), "day_number")

    dimensions = PublicApiStatisticsDimensions(
        phase=phase,
        difficulty=difficulty,
        metric=metric_code,
        bracket=bracket,
        location=location,
        boss_id=boss_id,
        damage_mode=damage_mode,
        role=role,
        class_filter=resolved_query.get("class"),
        spec_filter=resolved_query.get("spec"),
        week_number=week_number,
        realm=resolved_query.get("realm"),
        day_number=day_number,
    )

    class_summaries: list[PublicApiClassSummary] = []
    records: list[PublicApiStatisticRecord] = []
    for raw_class_name in sorted(statistics):
        class_name = _string(str(raw_class_name), "statistics class key")
        class_payload = _mapping(statistics[raw_class_name], f"statistics[{class_name!r}]")
        class_total_parses = _integer(
            class_payload.get("total_parses"),
            f"statistics[{class_name!r}].total_parses",
            minimum=0,
        )
        class_summaries.append(
            PublicApiClassSummary(class_name=class_name, total_parses=class_total_parses)
        )
        specs = _spec_container(class_payload, f"statistics[{class_name!r}]")
        for raw_spec_name in sorted(specs):
            spec_name = _string(str(raw_spec_name), f"statistics[{class_name!r}] spec key")
            records.append(
                _parse_metric(
                    specs[raw_spec_name],
                    class_name=class_name,
                    spec_name=spec_name,
                    label=f"statistics[{class_name!r}][specs][{spec_name!r}]",
                )
            )

    if not records:
        raise ValueError("statistics contained no reviewed spec metric records")
    return PublicApiStatisticsBatch(
        dimensions=dimensions,
        class_summaries=tuple(class_summaries),
        records=tuple(records),
    )


__all__ = [
    "PUBLIC_API_STATISTICS_NORMALIZER_VERSION",
    "PublicApiClassSummary",
    "PublicApiStatisticRecord",
    "PublicApiStatisticsBatch",
    "PublicApiStatisticsDimensions",
    "parse_public_api_statistics",
]
