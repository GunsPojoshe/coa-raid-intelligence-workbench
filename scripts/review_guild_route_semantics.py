from __future__ import annotations

import argparse
from pathlib import Path

from coa_workbench.collector.guild_route_semantics_review import (
    review_guild_route_semantics,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Review the bounded guild-search route and response schema. "
            "This does not verify pagination, completeness or full-crawl readiness."
        )
    )
    parser.add_argument(
        "--capture",
        type=Path,
        default=Path("evidence/real-data/argentum-guild-route-semantics-capture.json"),
    )
    parser.add_argument(
        "--full-crawl-contract",
        type=Path,
        default=Path("evidence/real-data/argentum-guild-full-crawl-contract.json"),
    )
    parser.add_argument(
        "--access-diagnostic",
        type=Path,
        default=Path("evidence/real-data/argentum-guild-search-access-spa-context.json"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/exchange/out/argentum-guild-route-semantics-review.json"),
    )
    parser.add_argument("--guild-label", default="Argentum")
    args = parser.parse_args()

    receipt = review_guild_route_semantics(
        capture_path=args.capture,
        full_crawl_contract_path=args.full_crawl_contract,
        public_access_diagnostic_path=args.access_diagnostic,
        receipt_output_path=args.output,
        expected_guild_label=args.guild_label,
    )

    summary = receipt["summary"]
    boundary = receipt["decision_boundary"]
    print(
        "guild route-semantics review: "
        f"route_schema_reviewed={summary['route_shape_and_response_schema_reviewed']} "
        f"limit_accepted={summary['limit_parameter_accepted']} "
        f"limit_truncation_verified={summary['limit_truncation_semantics_verified']} "
        f"pagination_verified={summary['pagination_semantics_verified']}"
    )
    print(f"receipt output: {args.output}")
    print(
        "ready for bounded limit-semantics capture: "
        f"{summary['ready_for_bounded_limit_semantics_capture']}"
    )
    print(f"guild API route semantics verified: {summary['guild_api_route_semantics_verified']}")
    print(f"ready for full guild crawl: {boundary['ready_for_full_guild_crawl']}")
    print(f"planner scoring allowed: {boundary['planner_scoring_allowed']}")
    return 0 if summary["route_shape_and_response_schema_reviewed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
