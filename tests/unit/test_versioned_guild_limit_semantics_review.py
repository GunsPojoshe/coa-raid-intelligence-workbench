from __future__ import annotations

from pathlib import Path

from coa_workbench.collector.guild_limit_semantics_review import (
    review_guild_limit_semantics,
)


def test_versioned_argentum_limit_capture_reviews_on_platform_checkout(
    tmp_path: Path,
) -> None:
    project_root = Path(__file__).resolve().parents[2]
    capture_path = (
        project_root / "evidence/real-data/argentum-guild-limit-semantics-capture.json"
    )
    route_review_path = (
        project_root / "evidence/real-data/argentum-guild-route-semantics-review.json"
    )

    receipt = review_guild_limit_semantics(
        capture_path=capture_path,
        route_review_path=route_review_path,
        receipt_output_path=tmp_path / "argentum-guild-limit-semantics-review.json",
    )

    assert receipt["source_capture_sha256"] == (
        "690d7d93d5e9c592877a4fa049d2638b0a5a523430f9205777ce4fa06e624e58"
    )
    assert receipt["source_binding_review"]["semantic_document_identity_preserved"] is True
    assert receipt["summary"]["integrity_check_count"] == 30
    assert receipt["summary"]["limit_truncation_semantics_verified"] is True
    assert receipt["summary"]["pagination_semantics_verified"] is False
    assert receipt["decision_boundary"]["ready_for_full_guild_crawl"] is False
    assert receipt["decision_boundary"]["planner_scoring_allowed"] is False
