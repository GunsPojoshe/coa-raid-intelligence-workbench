from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from coa_workbench.collector.guild_progression_callsite_review import (
    review_guild_progression_helper_callsite,
)


def _write(path: Path, payload: object) -> bytes:
    body = (json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()
    path.write_bytes(body)
    return body


def _inputs(tmp_path: Path) -> tuple[Path, Path, Path]:
    root = Path(__file__).resolve().parents[2]
    inventory = json.loads(
        (
            root / "evidence/real-data/argentum-guild-progression-callsite.json"
        ).read_text(encoding="utf-8")
    )
    usage = {
        "schema_version": 1,
        "review_kind": "guild_progression_usage_context_review",
        "review_version": "guild-progression-usage-context-review-v1",
        "integrity_checks": {f"check_{index}": True for index in range(30)},
        "summary": {
            "all_integrity_checks_passed": True,
            "integrity_check_count": 30,
            "guild_progression_usage_context_reviewed": True,
            "ready_for_bounded_progression_route_probe": False,
            "guild_api_route_semantics_verified": False,
            "pagination_semantics_verified": False,
            "termination_semantics_verified": False,
            "completeness_verified": False,
            "ready_for_full_guild_crawl": False,
            "planner_scoring_allowed": False,
            "contains_raw_context": False,
            "contains_source_scalar_values": False,
        },
    }
    recovery = {
        "schema_version": 1,
        "recovery_kind": "guild_identity_asset_profiled_recovery",
        "recovery_version": "guild-identity-asset-profiled-recovery-v1",
        "integrity_checks": {f"check_{index}": True for index in range(15)},
        "summary": {
            "all_integrity_checks_passed": True,
            "integrity_check_count": 15,
            "asset_download_completed": True,
            "contains_source_scalar_values": False,
        },
    }
    usage_path = tmp_path / "argentum-guild-progression-usage-review.json"
    recovery_path = tmp_path / "argentum-guild-asset-profiled-recovery.json"
    inventory_path = tmp_path / "inventory.json"
    usage_body = _write(usage_path, usage)
    recovery_body = _write(recovery_path, recovery)
    inventory["source_usage_review_name"] = usage_path.name
    inventory["source_usage_review_sha256"] = hashlib.sha256(usage_body).hexdigest()
    inventory["source_public_recovery_name"] = recovery_path.name
    inventory["source_public_recovery_sha256"] = hashlib.sha256(recovery_body).hexdigest()
    _write(inventory_path, inventory)
    return inventory_path, usage_path, recovery_path


def _review(tmp_path: Path, inventory: Path, usage: Path, recovery: Path) -> dict[str, object]:
    return review_guild_progression_helper_callsite(
        inventory_path=inventory,
        usage_review_path=usage,
        profiled_recovery_path=recovery,
        receipt_output_path=tmp_path / "review.json",
    )


def test_exact_generic_helper_review_keeps_probe_blocked(tmp_path: Path) -> None:
    inventory, usage, recovery = _inputs(tmp_path)
    receipt = _review(tmp_path, inventory, usage, recovery)
    callsite = receipt["callsite_review"]
    assert callsite["method_candidates"] == ["POST"]
    assert callsite["generic_helper_only"] is True
    assert callsite["structural_envelope_narrow_enough"] is False
    assert callsite["blockers"] == [
        "generic_helper_identity_unresolved",
        "structural_envelope_overbroad",
        "request_payload_mapping_unresolved",
    ]
    assert receipt["summary"][
        "ready_for_guild_progression_helper_definition_inventory"
    ] is True
    assert receipt["summary"]["ready_for_bounded_progression_route_probe"] is False
    assert receipt["decision_boundary"]["planner_scoring_allowed"] is False


def test_source_hash_mismatch_blocks_review(tmp_path: Path) -> None:
    inventory, usage, recovery = _inputs(tmp_path)
    usage.write_text(usage.read_text() + " ", encoding="utf-8")
    with pytest.raises(ValueError, match="usage review SHA-256 mismatch"):
        _review(tmp_path, inventory, usage, recovery)


def test_inventory_overclaim_blocks_review(tmp_path: Path) -> None:
    inventory, usage, recovery = _inputs(tmp_path)
    payload = json.loads(inventory.read_text())
    payload["summary"]["ready_for_bounded_progression_route_probe"] = True
    _write(inventory, payload)
    with pytest.raises(ValueError, match="helper inventory summary mismatch"):
        _review(tmp_path, inventory, usage, recovery)


def test_aggregate_method_drift_blocks_review(tmp_path: Path) -> None:
    inventory, usage, recovery = _inputs(tmp_path)
    payload = json.loads(inventory.read_text())
    payload["cross_occurrence_evidence"]["method_candidates"] = ["GET"]
    _write(inventory, payload)
    with pytest.raises(ValueError, match="cross occurrence evidence mismatch"):
        _review(tmp_path, inventory, usage, recovery)


def test_forbidden_public_callee_blocks_review(tmp_path: Path) -> None:
    inventory, usage, recovery = _inputs(tmp_path)
    payload = json.loads(inventory.read_text())
    payload["occurrences"][0]["call_candidates"][0]["callee"] = "secret"
    _write(inventory, payload)
    with pytest.raises(ValueError, match="forbidden public fields"):
        _review(tmp_path, inventory, usage, recovery)
