from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from coa_workbench.collector.guild_report_collection_contract import (
    build_guild_report_collection_contract,
)


def _root() -> Path:
    return Path(__file__).resolve().parents[2]


def _write(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_builds_bounded_argentum_collection_contract() -> None:
    root = _root()
    contract = build_guild_report_collection_contract(
        root / "config" / "mappings" / "coa_public_report_discovery_v1.json",
        root / "evidence" / "real-data" / "observed-combatants-info-persistence.json",
        guild_label="Argentum",
    )

    assert contract["contract_kind"] == "guild_wide_report_collection_contract"
    assert contract["target"] == {
        "guild_label": "Argentum",
        "guild_identity_status": "operator_named_target_unresolved",
        "verified_source_guild_id": False,
        "verified_source_guild_name": False,
        "minimum_candidate_characters": 30,
        "preferred_candidate_characters": 40,
        "final_roster_size": 25,
    }
    assert contract["verified_foundation"]["persisted_parser_observations"] == 1343
    assert contract["verified_foundation"]["persisted_actor_build_observations"] == 1339
    assert contract["verified_foundation"]["exact_payload_linked_actors"] == 11
    assert contract["summary"]["collection_phase_count"] == 7
    assert contract["summary"]["open_phase_count"] == 1
    assert contract["summary"]["blocked_phase_count"] == 6
    assert contract["decision_boundary"]["ready_for_bounded_pagination_capture"] is True
    assert contract["decision_boundary"]["ready_for_full_guild_crawl"] is False
    assert contract["decision_boundary"]["ready_for_bis25_scoring"] is False
    assert contract["decision_boundary"]["planner_scoring_allowed"] is False
    assert contract["decision_boundary"]["contains_source_scalar_values"] is False


def test_rejects_tampered_discovery_mapping(tmp_path: Path) -> None:
    root = _root()
    mapping = json.loads(
        (root / "config" / "mappings" / "coa_public_report_discovery_v1.json").read_text(
            encoding="utf-8"
        )
    )
    mapping["deferred_scopes"].remove("/pagination")
    mapping_path = tmp_path / "mapping.json"
    _write(mapping_path, mapping)

    with pytest.raises(ValueError, match="deferred scope set changed"):
        build_guild_report_collection_contract(
            mapping_path,
            root / "evidence" / "real-data" / "observed-combatants-info-persistence.json",
            guild_label="Argentum",
        )


def test_rejects_persistence_that_enables_scoring(tmp_path: Path) -> None:
    root = _root()
    persistence = json.loads(
        (
            root
            / "evidence"
            / "real-data"
            / "observed-combatants-info-persistence.json"
        ).read_text(encoding="utf-8")
    )
    tampered = deepcopy(persistence)
    tampered["summary"]["planner_scoring_allowed"] = True
    persistence_path = tmp_path / "persistence.json"
    _write(persistence_path, tampered)

    with pytest.raises(ValueError, match="planner_scoring_allowed"):
        build_guild_report_collection_contract(
            root / "config" / "mappings" / "coa_public_report_discovery_v1.json",
            persistence_path,
            guild_label="Argentum",
        )


@pytest.mark.parametrize(
    ("minimum", "preferred", "roster", "message"),
    [
        (24, 40, 25, "minimum candidate"),
        (30, 29, 25, "preferred candidate"),
        (30, 40, 0, "final roster size"),
    ],
)
def test_rejects_invalid_roster_bounds(
    minimum: int,
    preferred: int,
    roster: int,
    message: str,
) -> None:
    root = _root()
    with pytest.raises(ValueError, match=message):
        build_guild_report_collection_contract(
            root / "config" / "mappings" / "coa_public_report_discovery_v1.json",
            root / "evidence" / "real-data" / "observed-combatants-info-persistence.json",
            guild_label="Argentum",
            minimum_candidate_characters=minimum,
            preferred_candidate_characters=preferred,
            final_roster_size=roster,
        )
