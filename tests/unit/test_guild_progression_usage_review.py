from __future__ import annotations

import json
from pathlib import Path

import pytest

from coa_workbench.collector.guild_progression_usage_review import (
    review_guild_progression_usage_context,
)


def _write(path: Path, payload: object) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _inputs(tmp_path: Path) -> tuple[Path, Path]:
    root = Path(__file__).resolve().parents[2]
    inventory = json.loads(
        (
            root / "evidence/real-data/argentum-guild-progression-usage-context.json"
        ).read_text(encoding="utf-8")
    )
    recovery = json.loads(
        (
            root / "evidence/real-data/argentum-guild-asset-profiled-recovery.json"
        ).read_text(encoding="utf-8")
    )
    inventory_path = tmp_path / "inventory.json"
    recovery_path = tmp_path / "argentum-guild-asset-profiled-recovery.json"
    _write(inventory_path, inventory)
    _write(recovery_path, recovery)
    return inventory_path, recovery_path


def _review(tmp_path: Path, inventory_path: Path, recovery_path: Path) -> dict[str, object]:
    return review_guild_progression_usage_context(
        inventory_path=inventory_path,
        profiled_recovery_path=recovery_path,
        receipt_output_path=tmp_path / "review.json",
    )


def test_literal_reference_review_keeps_probe_blocked(tmp_path: Path) -> None:
    inventory_path, recovery_path = _inputs(tmp_path)

    receipt = _review(tmp_path, inventory_path, recovery_path)

    usage = receipt["usage_review"]
    summary = receipt["summary"]
    boundary = receipt["decision_boundary"]
    assert usage["method_candidates"] == []
    assert usage["method_resolution_status"] == "unresolved"
    assert usage["literal_reference_only"] is True
    assert usage["blockers"] == [
        "http_method_unresolved",
        "literal_reference_without_call_site",
        "invocation_shape_unresolved",
    ]
    assert summary["guild_progression_usage_context_reviewed"] is True
    assert summary["ready_for_bounded_progression_route_probe"] is False
    assert boundary["status"] == "guild_progression_usage_reviewed_probe_blocked"
    assert boundary["guild_api_route_semantics_verified"] is False
    assert boundary["ready_for_full_guild_crawl"] is False
    assert boundary["planner_scoring_allowed"] is False


def test_unambiguous_fetch_get_can_only_authorize_bounded_probe(tmp_path: Path) -> None:
    inventory_path, recovery_path = _inputs(tmp_path)
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    inventory["cross_occurrence_evidence"].update(
        {
            "call_style_candidates": ["fetch_call"],
            "method_candidate_count": 1,
            "method_candidate_unambiguous": True,
            "method_candidates": ["GET"],
        }
    )
    inventory["usage_contexts"][0].update(
        {
            "call_styles": ["fetch_call"],
            "method_candidates": ["GET"],
        }
    )
    inventory["summary"].update(
        {
            "method_candidate_count": 1,
            "method_candidate_unambiguous": True,
        }
    )
    _write(inventory_path, inventory)

    receipt = _review(tmp_path, inventory_path, recovery_path)

    assert receipt["summary"]["ready_for_bounded_progression_route_probe"] is True
    assert receipt["decision_boundary"]["status"] == (
        "guild_progression_usage_reviewed_probe_ready"
    )
    assert receipt["decision_boundary"]["guild_progression_request_shape_verified"] is False
    assert receipt["decision_boundary"]["guild_api_route_semantics_verified"] is False
    assert receipt["decision_boundary"]["ready_for_full_guild_crawl"] is False


def test_profiled_recovery_hash_mismatch_blocks_review(tmp_path: Path) -> None:
    inventory_path, recovery_path = _inputs(tmp_path)
    recovery = json.loads(recovery_path.read_text(encoding="utf-8"))
    recovery["generated_at"] = "changed"
    _write(recovery_path, recovery)

    with pytest.raises(ValueError, match="profiled recovery SHA-256 mismatch"):
        _review(tmp_path, inventory_path, recovery_path)


def test_inventory_overclaim_blocks_review(tmp_path: Path) -> None:
    inventory_path, recovery_path = _inputs(tmp_path)
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    inventory["summary"]["ready_for_bounded_progression_route_probe"] = True
    _write(inventory_path, inventory)

    with pytest.raises(ValueError, match="usage inventory summary mismatch"):
        _review(tmp_path, inventory_path, recovery_path)


def test_aggregate_method_drift_blocks_review(tmp_path: Path) -> None:
    inventory_path, recovery_path = _inputs(tmp_path)
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    inventory["cross_occurrence_evidence"]["method_candidates"] = ["GET"]
    inventory["cross_occurrence_evidence"]["method_candidate_count"] = 1
    _write(inventory_path, inventory)

    with pytest.raises(ValueError, match="aggregate method candidates"):
        _review(tmp_path, inventory_path, recovery_path)
