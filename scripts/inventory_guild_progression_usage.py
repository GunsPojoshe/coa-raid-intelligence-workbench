from __future__ import annotations

import argparse
from pathlib import Path

from coa_workbench.collector.guild_progression_usage_inventory import (
    inventory_guild_progression_usage_context,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Inventory the archived SPA usage context for /api/guilds/progression. "
            "No network requests are performed and no route semantics are promoted."
        )
    )
    parser.add_argument(
        "--public-recovery",
        type=Path,
        default=Path("evidence/real-data/argentum-guild-asset-profiled-recovery.json"),
    )
    parser.add_argument(
        "--private-recovery",
        type=Path,
        default=Path(
            "data/extracted/report-discovery/argentum-guild-asset-profiled-recovery.private.json"
        ),
    )
    parser.add_argument("--raw-root", type=Path, default=Path("data/raw"))
    parser.add_argument(
        "--private-output",
        type=Path,
        default=Path(
            "data/extracted/report-discovery/argentum-guild-progression-usage-context.private.json"
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/exchange/out/argentum-guild-progression-usage-context.json"),
    )
    parser.add_argument("--context-chars", type=int, default=384)
    parser.add_argument("--max-occurrences", type=int, default=20)
    args = parser.parse_args()

    receipt = inventory_guild_progression_usage_context(
        public_recovery_path=args.public_recovery,
        private_recovery_path=args.private_recovery,
        raw_root=args.raw_root,
        private_output_path=args.private_output,
        receipt_output_path=args.output,
        context_chars=args.context_chars,
        max_occurrences=args.max_occurrences,
    )
    evidence = receipt["cross_occurrence_evidence"]
    boundary = receipt["decision_boundary"]
    print(
        "guild progression usage inventory: "
        f"occurrences={evidence['occurrence_count']} "
        f"methods={evidence['method_candidates']} "
        f"method_unambiguous={evidence['method_candidate_unambiguous']}"
    )
    print(f"private output: {args.private_output}")
    print(f"receipt output: {args.output}")
    print(f"ready for usage review: {boundary['ready_for_guild_progression_usage_review']}")
    print(f"ready for bounded route probe: {boundary['ready_for_bounded_progression_route_probe']}")
    print(f"guild API route semantics verified: {boundary['guild_api_route_semantics_verified']}")
    print(f"ready for full guild crawl: {boundary['ready_for_full_guild_crawl']}")
    print(f"planner scoring allowed: {boundary['planner_scoring_allowed']}")
    return 0 if boundary["ready_for_guild_progression_usage_review"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
