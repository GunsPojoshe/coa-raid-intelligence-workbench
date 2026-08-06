from __future__ import annotations

import argparse
from pathlib import Path

from coa_workbench.collector.guild_limit_semantics_review import (
    review_guild_limit_semantics,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Review scalar-free guild limit evidence. This promotes only limit "
            "truncation semantics and does not verify pagination, termination, "
            "completeness or full-crawl readiness."
        )
    )
    parser.add_argument(
        "--capture",
        type=Path,
        default=Path("evidence/real-data/argentum-guild-limit-semantics-capture.json"),
    )
    parser.add_argument(
        "--route-review",
        type=Path,
        default=Path("evidence/real-data/argentum-guild-route-semantics-review.json"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/exchange/out/argentum-guild-limit-semantics-review.json"),
    )
    args = parser.parse_args()

    receipt = review_guild_limit_semantics(
        capture_path=args.capture,
        route_review_path=args.route_review,
        receipt_output_path=args.output,
    )
    summary = receipt["summary"]
    boundary = receipt["decision_boundary"]
    print(
        "guild limit-semantics review: "
        f"limit_truncation_verified={summary['limit_truncation_semantics_verified']} "
        f"pagination_verified={summary['pagination_semantics_verified']} "
        "ready_for_pagination_capture="
        f"{summary['ready_for_bounded_pagination_semantics_capture']}"
    )
    print(f"receipt output: {args.output}")
    print(f"guild API route semantics verified: {summary['guild_api_route_semantics_verified']}")
    print(f"ready for full guild crawl: {boundary['ready_for_full_guild_crawl']}")
    print(f"planner scoring allowed: {boundary['planner_scoring_allowed']}")
    return 0 if summary["limit_truncation_semantics_verified"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
