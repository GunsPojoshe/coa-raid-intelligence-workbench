from __future__ import annotations

import argparse
from pathlib import Path

from coa_workbench.collector.guild_progression_callsite_inventory import (
    inventory_guild_progression_helper_callsite,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Recover bounded helper/call-site candidates for /api/guilds/progression "
            "from the exact archived SPA asset without network requests."
        )
    )
    parser.add_argument(
        "--usage-review",
        type=Path,
        default=Path("evidence/real-data/argentum-guild-progression-usage-review.json"),
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
            "data/extracted/report-discovery/argentum-guild-progression-callsite.private.json"
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/exchange/out/argentum-guild-progression-callsite.json"),
    )
    parser.add_argument("--max-occurrences", type=int, default=20)
    parser.add_argument("--max-call-depth", type=int, default=8)
    parser.add_argument("--private-context-chars", type=int, default=2048)
    args = parser.parse_args()

    receipt = inventory_guild_progression_helper_callsite(
        usage_review_path=args.usage_review,
        public_recovery_path=args.public_recovery,
        private_recovery_path=args.private_recovery,
        raw_root=args.raw_root,
        private_output_path=args.private_output,
        receipt_output_path=args.output,
        max_occurrences=args.max_occurrences,
        max_call_depth=args.max_call_depth,
        private_context_chars=args.private_context_chars,
    )
    evidence = receipt["cross_occurrence_evidence"]
    boundary = receipt["decision_boundary"]
    print(
        "guild progression helper/call-site inventory: "
        f"occurrences={evidence['occurrence_count']} "
        f"calls={evidence['call_candidate_count']} "
        f"functions={evidence['enclosing_function_candidate_count']}"
    )
    print(f"method candidates: {evidence['method_candidates']}")
    print(f"private output: {args.private_output}")
    print(f"receipt output: {args.output}")
    print(
        "ready for helper/call-site review: "
        f"{boundary['ready_for_guild_progression_helper_callsite_review']}"
    )
    print(
        "ready for bounded route probe: "
        f"{boundary['ready_for_bounded_progression_route_probe']}"
    )
    print(f"guild API route semantics verified: {boundary['guild_api_route_semantics_verified']}")
    print(f"ready for full guild crawl: {boundary['ready_for_full_guild_crawl']}")
    print(f"planner scoring allowed: {boundary['planner_scoring_allowed']}")
    return 0 if boundary["ready_for_guild_progression_helper_callsite_review"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
