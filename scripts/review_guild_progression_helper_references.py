from __future__ import annotations

import argparse
from pathlib import Path

from coa_workbench.collector.guild_progression_helper_reference_review import (
    review_guild_progression_helper_references,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Review exact private helper-reference contexts for /api/guilds/progression "
            "without publishing raw symbols or enabling a route probe."
        )
    )
    parser.add_argument(
        "--inventory",
        type=Path,
        default=Path(
            "evidence/real-data/argentum-guild-progression-helper-reference.json"
        ),
    )
    parser.add_argument(
        "--private-inventory",
        type=Path,
        default=Path(
            "data/extracted/report-discovery/"
            "argentum-guild-progression-helper-reference.private.json"
        ),
    )
    parser.add_argument(
        "--definition-review",
        type=Path,
        default=Path(
            "evidence/real-data/argentum-guild-progression-helper-definition-review.json"
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "data/exchange/out/argentum-guild-progression-helper-reference-review.json"
        ),
    )
    args = parser.parse_args()

    receipt = review_guild_progression_helper_references(
        inventory_path=args.inventory,
        private_inventory_path=args.private_inventory,
        definition_review_path=args.definition_review,
        receipt_output_path=args.output,
    )
    summary = receipt["summary"]
    review = receipt["helper_reference_review"]
    print(
        "guild progression helper-reference review: "
        f"references={summary['reference_count']} "
        f"disposition={summary['reference_review_disposition']}"
    )
    print(f"route-context references: {summary['route_context_reference_count']}")
    print(f"direct transport contexts: {summary['direct_transport_context_count']}")
    print(f"request-shape contexts: {review['request_shape_context_count']}")
    print(f"blockers: {review['blockers']}")
    print(
        "ready for helper-owner inventory: "
        f"{summary['ready_for_guild_progression_helper_owner_inventory']}"
    )
    print(f"receipt output: {args.output}")
    print(
        "ready for bounded progression route probe: "
        f"{summary['ready_for_bounded_progression_route_probe']}"
    )
    print(f"guild API route semantics verified: {summary['guild_api_route_semantics_verified']}")
    print(f"ready for full guild crawl: {summary['ready_for_full_guild_crawl']}")
    print(f"planner scoring allowed: {summary['planner_scoring_allowed']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
