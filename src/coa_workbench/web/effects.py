from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from typing import Any, Iterable, Mapping

from coa_workbench.web.catalog import CLASS_SPECS, CLASS_SPEC_BY_CODE, ClassSpec

PRIORITY_WEIGHTS = {"Критично": 100, "Важно": 10, "Опционально": 1}
DEFAULT_EFFECTS_TABLE = (
    Path(__file__).resolve().parents[3]
    / "baseline"
    / "tables"
    / "EffectsReferenceTable.csv"
)


@dataclass(frozen=True, slots=True)
class EffectProvider:
    class_code: str
    class_name: str
    spec_code: str
    spec_name: str
    role: str

    @property
    def pair(self) -> tuple[str, str]:
        return self.class_code, self.spec_code


@dataclass(frozen=True, slots=True)
class EffectDefinition:
    code: str
    name: str
    category: str
    priority: str
    database_key: str
    roles: tuple[str, ...]
    providers: tuple[EffectProvider, ...]

    @property
    def weight(self) -> int:
        return PRIORITY_WEIGHTS[self.priority]

    @property
    def provider_pairs(self) -> frozenset[tuple[str, str]]:
        return frozenset(provider.pair for provider in self.providers)


def _slug(value: str) -> str:
    prepared = value.casefold().replace("%", " percent ").replace("&", " and ")
    prepared = re.sub(r"[^a-z0-9]+", "-", prepared).strip("-")
    return prepared


@cache
def load_effects(path: Path = DEFAULT_EFFECTS_TABLE) -> tuple[EffectDefinition, ...]:
    if not path.is_file():
        raise FileNotFoundError(f"Effect migration fixture not found: {path}")

    by_display_name = {
        (entry.class_name, entry.spec_name): entry for entry in CLASS_SPECS
    }
    effects: list[EffectDefinition] = []
    used_codes: set[str] = set()

    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        for index, row in enumerate(csv.DictReader(stream), start=1):
            providers: list[EffectProvider] = []
            unresolved: list[str] = []
            for raw_provider in filter(None, (part.strip() for part in row["Все источники"].split(";"))):
                parts = raw_provider.split(" — ", maxsplit=1)
                if len(parts) != 2:
                    unresolved.append(raw_provider)
                    continue
                entry = by_display_name.get((parts[0].strip(), parts[1].strip()))
                if entry is None:
                    unresolved.append(raw_provider)
                    continue
                providers.append(
                    EffectProvider(
                        class_code=entry.class_code,
                        class_name=entry.class_name,
                        spec_code=entry.spec_code,
                        spec_name=entry.spec_name,
                        role=entry.role,
                    )
                )
            if unresolved:
                raise ValueError(
                    f"Unresolved providers for effect {row['Эффект']!r}: {unresolved}"
                )

            database_key = row["Ключ базы"].strip()
            code = _slug(database_key) or f"effect-{index:02d}"
            if code in used_codes:
                code = f"{code}-{index:02d}"
            used_codes.add(code)
            priority = row["Приоритет"].strip()
            if priority not in PRIORITY_WEIGHTS:
                raise ValueError(f"Unknown effect priority: {priority!r}")

            effects.append(
                EffectDefinition(
                    code=code,
                    name=row["Эффект"].strip(),
                    category=row["Категория"].strip(),
                    priority=priority,
                    database_key=database_key,
                    roles=tuple(
                        part.strip()
                        for part in row["Роли"].split(",")
                        if part.strip()
                    ),
                    providers=tuple(providers),
                )
            )

    if len(effects) != 45:
        raise ValueError(f"Expected 45 legacy effects, got {len(effects)}")
    return tuple(effects)


EFFECTS = load_effects()
EFFECT_BY_CODE = {effect.code: effect for effect in EFFECTS}
EFFECT_CODES_BY_PAIR: dict[tuple[str, str], frozenset[str]] = {
    (entry.class_code, entry.spec_code): frozenset(
        effect.code
        for effect in EFFECTS
        if (entry.class_code, entry.spec_code) in effect.provider_pairs
    )
    for entry in CLASS_SPECS
}


def effects_catalog_payload() -> dict[str, Any]:
    categories: dict[str, int] = {}
    priority_counts: dict[str, int] = {}
    payload: list[dict[str, Any]] = []
    for effect in EFFECTS:
        categories[effect.category] = categories.get(effect.category, 0) + 1
        priority_counts[effect.priority] = priority_counts.get(effect.priority, 0) + 1
        payload.append(
            {
                "code": effect.code,
                "name": effect.name,
                "category": effect.category,
                "priority": effect.priority,
                "database_key": effect.database_key,
                "roles": list(effect.roles),
                "provider_count": len(effect.providers),
                "providers": [
                    {
                        "class_code": provider.class_code,
                        "class_name": provider.class_name,
                        "spec_code": provider.spec_code,
                        "spec_name": provider.spec_name,
                        "role": provider.role,
                    }
                    for provider in effect.providers
                ],
            }
        )
    return {
        "schema_version": 1,
        "source": "baseline/tables/EffectsReferenceTable.csv",
        "effect_count": len(EFFECTS),
        "provider_link_count": sum(len(effect.providers) for effect in EFFECTS),
        "categories": categories,
        "priorities": priority_counts,
        "effects": payload,
    }


def _value(slot: Any, name: str, default: Any = "") -> Any:
    if isinstance(slot, Mapping):
        return slot.get(name, default)
    return getattr(slot, name, default)


def _effect_brief(effect: EffectDefinition) -> dict[str, str]:
    return {
        "code": effect.code,
        "name": effect.name,
        "category": effect.category,
        "priority": effect.priority,
    }


def analyze_composition(
    slots: Iterable[Any],
    *,
    top_n: int = 3,
) -> dict[str, Any]:
    active_slots: list[dict[str, Any]] = []
    for slot in slots:
        class_code = str(_value(slot, "class_code", "")).strip()
        spec_code = str(_value(slot, "spec_code", "")).strip()
        player_name = str(_value(slot, "player_name", "")).strip()
        if not _value(slot, "active", False) or not player_name:
            continue
        if (class_code, spec_code) not in CLASS_SPEC_BY_CODE:
            continue
        active_slots.append(
            {
                "slot_no": int(_value(slot, "slot_no", 0)),
                "player_name": player_name,
                "class_code": class_code,
                "spec_code": spec_code,
            }
        )

    covered: list[dict[str, Any]] = []
    missing: list[dict[str, str]] = []
    covered_codes: set[str] = set()
    category_stats: dict[str, dict[str, int]] = {}
    priority_stats: dict[str, dict[str, int]] = {
        priority: {"total": 0, "covered": 0, "missing": 0}
        for priority in PRIORITY_WEIGHTS
    }

    for effect in EFFECTS:
        category = category_stats.setdefault(
            effect.category, {"total": 0, "covered": 0, "missing": 0}
        )
        category["total"] += 1
        priority_stats[effect.priority]["total"] += 1
        providers = [
            {
                "slot_no": slot["slot_no"],
                "player_name": slot["player_name"],
                "class_code": slot["class_code"],
                "spec_code": slot["spec_code"],
            }
            for slot in active_slots
            if (slot["class_code"], slot["spec_code"]) in effect.provider_pairs
        ]
        if providers:
            covered_codes.add(effect.code)
            category["covered"] += 1
            priority_stats[effect.priority]["covered"] += 1
            covered.append(
                {
                    **_effect_brief(effect),
                    "provider_count": len(providers),
                    "providers": providers,
                }
            )
        else:
            category["missing"] += 1
            priority_stats[effect.priority]["missing"] += 1
            missing.append(_effect_brief(effect))

    missing_codes = set(EFFECT_BY_CODE) - covered_codes
    recommendations: list[dict[str, Any]] = []
    present_pairs = {
        (slot["class_code"], slot["spec_code"]) for slot in active_slots
    }
    for candidate in CLASS_SPECS:
        pair = (candidate.class_code, candidate.spec_code)
        new_codes = EFFECT_CODES_BY_PAIR[pair] & missing_codes
        if not new_codes:
            continue
        new_effects = [effect for effect in EFFECTS if effect.code in new_codes]
        critical = sum(effect.priority == "Критично" for effect in new_effects)
        important = sum(effect.priority == "Важно" for effect in new_effects)
        optional = sum(effect.priority == "Опционально" for effect in new_effects)
        score = sum(effect.weight for effect in new_effects)
        recommendations.append(
            {
                "class_code": candidate.class_code,
                "class_name": candidate.class_name,
                "spec_code": candidate.spec_code,
                "spec_name": candidate.spec_name,
                "role": candidate.role,
                "already_present": pair in present_pairs,
                "score": score,
                "new_effect_count": len(new_effects),
                "critical_new": critical,
                "important_new": important,
                "optional_new": optional,
                "new_effects": [_effect_brief(effect) for effect in new_effects],
                "explanation": (
                    f"Закрывает: критичных {critical}, важных {important}, "
                    f"опциональных {optional}"
                ),
            }
        )

    recommendations.sort(
        key=lambda item: (
            -item["score"],
            -item["critical_new"],
            -item["new_effect_count"],
            item["class_name"].casefold(),
            item["spec_name"].casefold(),
        )
    )
    total = len(EFFECTS)
    return {
        "coverage": {
            "total_effects": total,
            "covered_effects": len(covered),
            "missing_effects": len(missing),
            "coverage_percent": round(len(covered) * 100 / total, 1),
            "categories": category_stats,
            "priorities": priority_stats,
            "covered": covered,
            "missing": missing,
        },
        "recommendations": recommendations[: max(0, top_n)],
        "scoring": {
            "algorithm": "missing-effect-priority-v1",
            "weights": PRIORITY_WEIGHTS,
            "role_targets_used": False,
        },
    }
