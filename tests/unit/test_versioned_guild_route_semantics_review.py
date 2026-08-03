from __future__ import annotations

from pathlib import Path

from coa_workbench.collector.guild_route_semantics_review import (
    review_guild_route_semantics,
)


def test_versioned_argentum_capture_reviews_on_lf_checkout(tmp_path: Path) -> None:
    project_root = Path(__file__).resolve().parents[2]

    receipt = review_guild_route_semantics(
        capture_path=(
            project_root
            / "evidence/real-data/argentum-guild-route-semantics-capture.json"
        ),
        full_crawl_contract_path=(
            project_root / "evidence/real-data/argentum-guild-full-crawl-contract.json"
        ),
        public_access_diagnostic_path=(
            project_root
            / "evidence/real-data/argentum-guild-search-access-spa-context.json"
        ),
        receipt_output_path=tmp_path / "argentum-guild-route-semantics-review.json",
    )

    binding = receipt["source_binding_review"]
    summary = receipt["summary"]
    boundary = receipt["decision_boundary"]

    assert binding["contract_line_endings_normalized"] is True
    assert binding["access_line_endings_normalized"] is True
    assert summary["all_integrity_checks_passed"] is True
    assert summary["route_shape_and_response_schema_reviewed"] is True
    assert summary["ready_for_bounded_limit_semantics_capture"] is True
    assert summary["guild_api_route_semantics_verified"] is False
    assert boundary["ready_for_full_guild_crawl"] is False
    assert boundary["planner_scoring_allowed"] is False
