from __future__ import annotations

import pytest

from coa_workbench.collector.current_combatants_roster import (
    parse_current_combatants_roster,
)


def _payload(*, mismatch: bool = False) -> dict[str, object]:
    talent_id = 7
    hero_id = 8 if mismatch else talent_id
    return {
        "success": True,
        "roster": [
            {
                "character_id": 101,
                "name": "Example",
                "class": "ExampleClass",
                "role": "damage",
                "specs": ["ExampleSpec"],
                "primary_stats": [],
                "potions": {"total": 0, "items": []},
                "healthstones": {"total": 0, "items": []},
                "snapshots": [
                    {
                        "captured_at": 123456,
                        "captured_for_boss": "Example Boss",
                        "captured_for_pull_id": 55,
                        "source": "addon",
                        "player": {
                            "class": "ExampleClass",
                            "gender": 0,
                            "guid": "Player-Example",
                            "level": 60,
                            "name": "Example",
                            "race": "Human",
                            "realm": "ExampleRealm",
                        },
                        "guild": {
                            "name": "Example Guild",
                            "rank_index": 1,
                            "rank_name": "Member",
                        },
                        "instance": {
                            "difficulty_index": 1,
                            "difficulty_name": "Example",
                            "instance_type": "raid",
                            "is_dynamic": False,
                            "map_id": 1,
                            "max_players": 25,
                            "name": "Example Raid",
                            "player_difficulty": 1,
                        },
                        "specialization": {
                            "active_spec_idx": 1,
                            "active_spec_name": "Example Spec",
                            "active_spec_role": "damage",
                            "active_spec_slot": 1,
                            "resolved_ca_talent_ranks": [
                                {
                                    "bisbeard_tree": "example",
                                    "cao_id": talent_id,
                                    "icon": "icon",
                                    "name": "Talent",
                                    "rank": 1,
                                }
                            ],
                            "hero_build": {
                                "1": {"entry_id": hero_id, "rank": 1},
                            },
                            "talents": {
                                "class_label": "ExampleClass",
                                "class_slug": "example",
                                "tree_order": ["example"],
                                "trees": {
                                    "1": {
                                        "label": "Example",
                                        "points": 1,
                                        "slug": "example",
                                        "spec_icon": None,
                                        "talents": [
                                            {
                                                "talent_id": "talent",
                                                "entry_id": talent_id,
                                                "rank": 1,
                                                "max_ranks": 1,
                                                "grid_col": 1,
                                                "grid_row": 1,
                                                "name": "Talent",
                                                "icon": "icon",
                                                "tree_slug": "example",
                                                "tree_label": "Example",
                                                "category_label": None,
                                                "per_rank_text": [],
                                            }
                                        ],
                                    }
                                },
                            },
                        },
                        "gear": {
                            "1": {
                                "enchant": 0,
                                "item_id": 123,
                                "slot": 1,
                                "suffix": 0,
                                "unique": 0,
                                "resolved_item": {"id": 123, "name": "Item"},
                                "resolved_bisbeard": {"version": "v1"},
                                "resolved_enchant": None,
                                "resolved_set": None,
                                "resolved_gems": [],
                            }
                        },
                    }
                ],
            }
        ],
    }


def test_current_roster_parser_preserves_build_evidence_without_semantic_promotion() -> None:
    result = parse_current_combatants_roster(_payload())
    summary = result.public_summary()

    assert summary == {
        "parser_version": "current-combatants-roster-v1",
        "character_count": 1,
        "snapshot_count": 1,
        "talent_entry_count": 1,
        "gear_slot_observation_count": 1,
        "resolved_item_observation_count": 1,
        "resolved_bisbeard_observation_count": 1,
        "exact_talent_alignment_snapshot_count": 1,
        "talent_alignment_complete": True,
        "contains_source_scalar_values": False,
        "planner_scoring_allowed": False,
    }
    assert result.talent_entries[0]["resolved_rank"]["cao_id"] == 7
    assert result.talent_entries[0]["hero_build"]["entry_id"] == 7
    assert result.talent_entries[0]["talent_grid"]["entry_id"] == 7


def test_current_roster_parser_fails_closed_on_talent_membership_mismatch() -> None:
    with pytest.raises(ValueError, match="disagree on entry-id membership"):
        parse_current_combatants_roster(_payload(mismatch=True))
