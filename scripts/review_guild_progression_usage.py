from __future__ import annotations

import argparse
from pathlib import Path

from coa_workbench.collector.guild_progression_usage_review import (
    review_guild_progression_usage_context,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Review scalar-free SPA usage evidence for /api/guilds/progression. "
            "The review does not guess HTTP method or promote route semantics."
        )
    )
    parser.add_argument(
        "--inventory",
        type=Path,
        default=Path("evidence/real-data/argentum-guild-progression-usage-context.json"),
    )
    parser.add_argument(
        "--profiled-recovery",
        type=Path,
        default=Path("evidence/real-data/argentum-guild-asset-profiled-recovery.json"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/exchange/out/argentum-guild-progression-usage-review.json"),
    )
    args = parser.parse_args()

    receipt = review_guild_progression_usage_context(
        inventory_path=args.inventory,
        profiled_recovery_path=args.profiled_recovery,
        receipt_output_path=args.output,
    )
    summary = receipt["summary"]
    usage = receipt["usage_review"]
    print(
        "guild progression usage review: "
        f"reviewed={summary['guild_progression_usage_context_reviewed']} "
        f"method_unambiguous={summary['method_candidate_unambiguous']} "
        f"probe_ready={summary['ready_for_bounded_progression_route_probe']}"
    )
    print(f"method candidates: {usage['method_candidates']}")
    print(f"blockers: {usage['blockers']}")
    print(f"receipt output: {args.output}")
    print(f"guild API route semantics verified: {summary['guild_api_route_semantics_verified']}")
    print(f"ready for full guild crawl: {summary['ready_for_full_guild_crawl']}")
    print(f"planner scoring allowed: {summary['planner_scoring_allowed']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
