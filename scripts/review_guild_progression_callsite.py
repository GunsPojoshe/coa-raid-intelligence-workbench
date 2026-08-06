from __future__ import annotations

import argparse
from pathlib import Path

from coa_workbench.collector.guild_progression_callsite_review import (
    review_guild_progression_helper_callsite,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Review the exact scalar-free helper/call-site candidate for "
            "/api/guilds/progression without inferring generic-helper semantics."
        )
    )
    parser.add_argument(
        "--inventory",
        type=Path,
        default=Path("evidence/real-data/argentum-guild-progression-callsite.json"),
    )
    parser.add_argument(
        "--usage-review",
        type=Path,
        default=Path("evidence/real-data/argentum-guild-progression-usage-review.json"),
    )
    parser.add_argument(
        "--profiled-recovery",
        type=Path,
        default=Path("evidence/real-data/argentum-guild-asset-profiled-recovery.json"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/exchange/out/argentum-guild-progression-callsite-review.json"),
    )
    args = parser.parse_args()

    receipt = review_guild_progression_helper_callsite(
        inventory_path=args.inventory,
        usage_review_path=args.usage_review,
        profiled_recovery_path=args.profiled_recovery,
        receipt_output_path=args.output,
    )
    summary = receipt["summary"]
    review = receipt["callsite_review"]
    print(
        "guild progression helper/call-site review: "
        f"reviewed={summary['guild_progression_helper_callsite_reviewed']} "
        f"method={summary['http_method_candidate']} "
        f"probe_ready={summary['ready_for_bounded_progression_route_probe']}"
    )
    print(f"call classes: {review['call_classes']}")
    print(f"blockers: {review['blockers']}")
    print(
        "ready for helper-definition inventory: "
        f"{summary['ready_for_guild_progression_helper_definition_inventory']}"
    )
    print(f"receipt output: {args.output}")
    print(f"guild API route semantics verified: {summary['guild_api_route_semantics_verified']}")
    print(f"ready for full guild crawl: {summary['ready_for_full_guild_crawl']}")
    print(f"planner scoring allowed: {summary['planner_scoring_allowed']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
