from __future__ import annotations

import argparse
from pathlib import Path

from coa_workbench.collector.guild_progression_helper_definition_review import (
    review_guild_progression_helper_definition,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Review the exact private helper-definition candidate for "
            "/api/guilds/progression without enabling a network probe."
        )
    )
    parser.add_argument(
        "--inventory",
        type=Path,
        default=Path("evidence/real-data/argentum-guild-progression-helper-definition.json"),
    )
    parser.add_argument(
        "--private-inventory",
        type=Path,
        default=Path(
            "data/extracted/report-discovery/"
            "argentum-guild-progression-helper-definition.private.json"
        ),
    )
    parser.add_argument(
        "--callsite-review",
        type=Path,
        default=Path("evidence/real-data/argentum-guild-progression-callsite-review.json"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "data/exchange/out/argentum-guild-progression-helper-definition-review.json"
        ),
    )
    args = parser.parse_args()

    receipt = review_guild_progression_helper_definition(
        inventory_path=args.inventory,
        private_inventory_path=args.private_inventory,
        callsite_review_path=args.callsite_review,
        receipt_output_path=args.output,
    )
    summary = receipt["summary"]
    review = receipt["helper_definition_review"]
    print(
        "guild progression helper-definition review: "
        f"reviewed={summary['guild_progression_helper_definition_reviewed']} "
        f"disposition={summary['definition_candidate_disposition']} "
        f"probe_ready={summary['ready_for_bounded_progression_route_probe']}"
    )
    print(f"blockers: {review['blockers']}")
    print(
        "ready for helper-reference inventory: "
        f"{summary['ready_for_guild_progression_helper_reference_inventory']}"
    )
    print(f"receipt output: {args.output}")
    print(f"guild API route semantics verified: {summary['guild_api_route_semantics_verified']}")
    print(f"ready for full guild crawl: {summary['ready_for_full_guild_crawl']}")
    print(f"planner scoring allowed: {summary['planner_scoring_allowed']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
