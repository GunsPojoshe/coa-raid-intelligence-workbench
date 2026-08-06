from __future__ import annotations

import hashlib
import json
from pathlib import Path

from coa_workbench.collector.guild_progression_callsite_review import (
    review_guild_progression_helper_callsite,
)


def _without_generated_at(payload: dict[str, object]) -> dict[str, object]:
    return {key: value for key, value in payload.items() if key != "generated_at"}


def test_versioned_argentum_callsite_reviews_as_probe_blocked(tmp_path: Path) -> None:
    project_root = Path(__file__).resolve().parents[2]
    inventory_path = (
        project_root / "evidence/real-data/argentum-guild-progression-callsite.json"
    )
    usage_review_path = (
        project_root / "evidence/real-data/argentum-guild-progression-usage-review.json"
    )
    recovery_path = (
        project_root / "evidence/real-data/argentum-guild-asset-profiled-recovery.json"
    )
    versioned_review_path = (
        project_root / "evidence/real-data/argentum-guild-progression-callsite-review.json"
    )

    receipt = review_guild_progression_helper_callsite(
        inventory_path=inventory_path,
        usage_review_path=usage_review_path,
        profiled_recovery_path=recovery_path,
        receipt_output_path=tmp_path / "review.json",
    )
    versioned = json.loads(versioned_review_path.read_text(encoding="utf-8"))

    inventory_body = inventory_path.read_bytes()
    canonical_lf_body = inventory_body.replace(b"\r\n", b"\n")
    assert hashlib.sha256(canonical_lf_body).hexdigest() == (
        "ad8a5addf9ac9dd566284e0bc395ac40100986d0f14f0a49e9519a6aef28d351"
    )
    assert _without_generated_at(receipt) == _without_generated_at(versioned)
    assert receipt["summary"]["integrity_check_count"] == 36
    assert receipt["summary"]["http_method_candidate"] == "POST"
    assert receipt["summary"]["helper_identity_resolved"] is False
    assert receipt["summary"]["request_payload_mapping_resolved"] is False
    assert receipt["summary"]["ready_for_bounded_progression_route_probe"] is False
    assert receipt["summary"][
        "ready_for_guild_progression_helper_definition_inventory"
    ] is True
    assert receipt["decision_boundary"]["guild_api_route_semantics_verified"] is False
    assert receipt["decision_boundary"]["ready_for_full_guild_crawl"] is False
    assert receipt["decision_boundary"]["planner_scoring_allowed"] is False
