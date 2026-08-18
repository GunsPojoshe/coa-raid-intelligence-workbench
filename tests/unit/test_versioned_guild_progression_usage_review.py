from __future__ import annotations

import hashlib
from pathlib import Path

from coa_workbench.collector.guild_progression_usage_review import (
    review_guild_progression_usage_context,
)


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def test_versioned_argentum_progression_usage_reviews_as_probe_blocked(
    tmp_path: Path,
) -> None:
    project_root = Path(__file__).resolve().parents[2]
    inventory_path = (
        project_root / "evidence/real-data/argentum-guild-progression-usage-context.json"
    )
    recovery_path = (
        project_root / "evidence/real-data/argentum-guild-asset-profiled-recovery.json"
    )

    receipt = review_guild_progression_usage_context(
        inventory_path=inventory_path,
        profiled_recovery_path=recovery_path,
        receipt_output_path=tmp_path / "argentum-guild-progression-usage-review.json",
    )

    inventory_body = inventory_path.read_bytes()
    canonical_lf_body = inventory_body.replace(b"\r\n", b"\n")
    assert receipt["source_inventory_sha256"] == _sha256(inventory_body)
    assert _sha256(canonical_lf_body) == (
        "e19cc1a72175bd838b151b8438861af1aece14ba2a30f94da8f6989ce7be3d59"
    )
    assert receipt["summary"]["integrity_check_count"] == 30
    assert receipt["summary"]["guild_progression_usage_context_reviewed"] is True
    assert receipt["summary"]["method_candidate_unambiguous"] is False
    assert receipt["summary"]["ready_for_bounded_progression_route_probe"] is False
    assert receipt["decision_boundary"]["guild_api_route_semantics_verified"] is False
    assert receipt["decision_boundary"]["ready_for_full_guild_crawl"] is False
    assert receipt["decision_boundary"]["planner_scoring_allowed"] is False
