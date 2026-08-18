from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Mapping

CURRENT_ROSTER_PARSER_VERSION = "current-combatants-roster-v1"


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _object(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field} must be an object")
    return value


def _array(value: Any, field: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"{field} must be an array")
    return value


def _scalar_id(value: Any, field: str) -> str:
    if isinstance(value, bool) or not isinstance(value, (int, str)) or str(value) == "":
        raise ValueError(f"{field} must be an integer or non-empty string identifier")
    return str(value)


def _selected(source: Mapping[str, Any], fields: tuple[str, ...]) -> dict[str, Any]:
    return {field: source.get(field) for field in fields}


def _tree_entries(specialization: Mapping[str, Any]) -> list[dict[str, Any]]:
    talents = _object(specialization.get("talents"), "specialization.talents")
    trees = _object(talents.get("trees"), "specialization.talents.trees")
    rows: list[dict[str, Any]] = []
    for tree_key in sorted(trees, key=str):
        tree = _object(trees[tree_key], "specialization.talents.trees[]")
        for raw_entry in _array(tree.get("talents"), "specialization.talents.trees[].talents"):
            rows.append(_object(raw_entry, "specialization.talents.trees[].talents[]"))
    return rows


def _entry_map(
    rows: list[dict[str, Any]],
    *,
    id_field: str,
    scope: str,
) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        key = _scalar_id(row.get(id_field), f"{scope}.{id_field}")
        if key in result:
            raise ValueError(f"{scope} has duplicate {id_field}: {key}")
        result[key] = row
    return result


def _hero_entries(specialization: Mapping[str, Any]) -> list[dict[str, Any]]:
    hero = _object(specialization.get("hero_build"), "specialization.hero_build")
    return [_object(hero[key], "specialization.hero_build[]") for key in sorted(hero, key=str)]


@dataclass(frozen=True, slots=True)
class CurrentRosterParseResult:
    characters: tuple[dict[str, Any], ...]
    snapshots: tuple[dict[str, Any], ...]
    talent_entries: tuple[dict[str, Any], ...]
    gear_entries: tuple[dict[str, Any], ...]
    exact_talent_alignment_snapshot_count: int

    def public_summary(self) -> dict[str, Any]:
        bisbeard_count = sum(
            isinstance(row.get("resolved_bisbeard"), dict) for row in self.gear_entries
        )
        resolved_item_count = sum(
            isinstance(row.get("resolved_item"), dict) for row in self.gear_entries
        )
        return {
            "parser_version": CURRENT_ROSTER_PARSER_VERSION,
            "character_count": len(self.characters),
            "snapshot_count": len(self.snapshots),
            "talent_entry_count": len(self.talent_entries),
            "gear_slot_observation_count": len(self.gear_entries),
            "resolved_item_observation_count": resolved_item_count,
            "resolved_bisbeard_observation_count": bisbeard_count,
            "exact_talent_alignment_snapshot_count": self.exact_talent_alignment_snapshot_count,
            "talent_alignment_complete": (
                self.exact_talent_alignment_snapshot_count == len(self.snapshots)
            ),
            "contains_source_scalar_values": False,
            "planner_scoring_allowed": False,
        }


def parse_current_combatants_roster(payload: Mapping[str, Any]) -> CurrentRosterParseResult:
    """Parse the current browser-observed combatants-roster response without mechanic inference.

    The private result preserves source scalar values for later evidence-backed persistence. The
    public summary exposes counts only. Talent rows are joined only when the three independently
    present current structures agree on the same entry-id set: resolved_ca_talent_ranks,
    hero_build values, and talents.trees[].talents[].
    """
    root = _object(payload, "payload")
    roster = _array(root.get("roster"), "roster")

    characters: list[dict[str, Any]] = []
    snapshots_out: list[dict[str, Any]] = []
    talent_entries: list[dict[str, Any]] = []
    gear_entries: list[dict[str, Any]] = []
    exact_alignment = 0

    for character_index, raw_character in enumerate(roster):
        character = _object(raw_character, f"roster[{character_index}]")
        source_character_id = _scalar_id(
            character.get("character_id"),
            f"roster[{character_index}].character_id",
        )
        snapshots = _array(character.get("snapshots"), f"roster[{character_index}].snapshots")
        characters.append(
            {
                "source_character_id": source_character_id,
                "name": character.get("name"),
                "class": character.get("class"),
                "role": character.get("role"),
                "specs": character.get("specs"),
                "primary_stats": character.get("primary_stats"),
                "potions": character.get("potions"),
                "healthstones": character.get("healthstones"),
                "snapshot_count": len(snapshots),
            }
        )

        for snapshot_index, raw_snapshot in enumerate(snapshots):
            snapshot = _object(
                raw_snapshot,
                f"roster[{character_index}].snapshots[{snapshot_index}]",
            )
            snapshot_hash = _sha256(snapshot)
            player = _object(snapshot.get("player"), "snapshot.player")
            guild = _object(snapshot.get("guild"), "snapshot.guild")
            instance = _object(snapshot.get("instance"), "snapshot.instance")
            specialization = _object(snapshot.get("specialization"), "snapshot.specialization")
            gear = _object(snapshot.get("gear"), "snapshot.gear")
            talents = _object(specialization.get("talents"), "snapshot.specialization.talents")

            resolved_rows = [
                _object(row, "specialization.resolved_ca_talent_ranks[]")
                for row in _array(
                    specialization.get("resolved_ca_talent_ranks"),
                    "specialization.resolved_ca_talent_ranks",
                )
            ]
            hero_rows = _hero_entries(specialization)
            tree_rows = _tree_entries(specialization)
            resolved = _entry_map(
                resolved_rows,
                id_field="cao_id",
                scope="specialization.resolved_ca_talent_ranks",
            )
            hero = _entry_map(
                hero_rows,
                id_field="entry_id",
                scope="specialization.hero_build",
            )
            tree = _entry_map(
                tree_rows,
                id_field="entry_id",
                scope="specialization.talents.trees[].talents",
            )
            aligned_ids = set(resolved)
            if aligned_ids != set(hero) or aligned_ids != set(tree):
                raise ValueError(
                    "current roster talent structures disagree on entry-id membership; "
                    "refusing a lossy joined parser observation"
                )
            exact_alignment += 1

            snapshots_out.append(
                {
                    "source_character_id": source_character_id,
                    "snapshot_hash": snapshot_hash,
                    "snapshot_index": snapshot_index,
                    "captured_at": snapshot.get("captured_at"),
                    "captured_for_boss": snapshot.get("captured_for_boss"),
                    "captured_for_pull_id": snapshot.get("captured_for_pull_id"),
                    "source": snapshot.get("source"),
                    "outer_character": _selected(
                        character,
                        ("name", "class", "role", "specs", "primary_stats"),
                    ),
                    "player": _selected(
                        player,
                        ("class", "gender", "guid", "level", "name", "race", "realm"),
                    ),
                    "guild": _selected(guild, ("name", "rank_index", "rank_name")),
                    "instance": _selected(
                        instance,
                        (
                            "difficulty_index",
                            "difficulty_name",
                            "instance_type",
                            "is_dynamic",
                            "map_id",
                            "max_players",
                            "name",
                            "player_difficulty",
                        ),
                    ),
                    "specialization": _selected(
                        specialization,
                        (
                            "active_spec_idx",
                            "active_spec_name",
                            "active_spec_role",
                            "active_spec_slot",
                        ),
                    ),
                    "talent_container": _selected(
                        talents,
                        ("class_label", "class_slug", "tree_order"),
                    ),
                }
            )

            for entry_id in sorted(
                aligned_ids,
                key=lambda value: int(value) if value.isdigit() else value,
            ):
                resolved_row = resolved[entry_id]
                hero_row = hero[entry_id]
                tree_row = tree[entry_id]
                talent_entries.append(
                    {
                        "source_character_id": source_character_id,
                        "snapshot_hash": snapshot_hash,
                        "entry_id": entry_id,
                        "resolved_rank": _selected(
                            resolved_row,
                            ("bisbeard_tree", "cao_id", "icon", "name", "rank"),
                        ),
                        "hero_build": _selected(hero_row, ("entry_id", "rank")),
                        "talent_grid": _selected(
                            tree_row,
                            (
                                "talent_id",
                                "entry_id",
                                "rank",
                                "max_ranks",
                                "grid_col",
                                "grid_row",
                                "name",
                                "icon",
                                "tree_slug",
                                "tree_label",
                                "category_label",
                                "per_rank_text",
                            ),
                        ),
                    }
                )

            for gear_key in sorted(
                gear,
                key=lambda value: int(value) if str(value).isdigit() else str(value),
            ):
                gear_row = _object(gear[gear_key], "snapshot.gear[]")
                gear_entries.append(
                    {
                        "source_character_id": source_character_id,
                        "snapshot_hash": snapshot_hash,
                        "slot_key": str(gear_key),
                        **_selected(
                            gear_row,
                            ("enchant", "item_id", "slot", "suffix", "unique"),
                        ),
                        "resolved_item": gear_row.get("resolved_item"),
                        "resolved_bisbeard": gear_row.get("resolved_bisbeard"),
                        "resolved_enchant": gear_row.get("resolved_enchant"),
                        "resolved_set": gear_row.get("resolved_set"),
                        "resolved_gems": gear_row.get("resolved_gems"),
                    }
                )

    return CurrentRosterParseResult(
        characters=tuple(characters),
        snapshots=tuple(snapshots_out),
        talent_entries=tuple(talent_entries),
        gear_entries=tuple(gear_entries),
        exact_talent_alignment_snapshot_count=exact_alignment,
    )


__all__ = [
    "CURRENT_ROSTER_PARSER_VERSION",
    "CurrentRosterParseResult",
    "parse_current_combatants_roster",
]
