from __future__ import annotations

import argparse
from pathlib import Path

from coa_workbench.collector.guild_progression_helper_definition_command import (
    inventory_guild_progression_helper_definition,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Inventory bounded helper-definition and alias candidates for "
            "/api/guilds/progression from the exact archived SPA asset."
        )
    )
    parser.add_argument(
        "--callsite-review",
        type=Path,
        default=Path("evidence/real-data/argentum-guild-progression-callsite-review.json"),
    )
    parser.add_argument(
        "--public-callsite",
        type=Path,
        default=Path("evidence/real-data/argentum-guild-progression-callsite.json"),
    )
    parser.add_argument(
        "--private-callsite",
        type=Path,
        default=Path(
            "data/extracted/report-discovery/argentum-guild-progression-callsite.private.json"
        ),
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
            "data/extracted/report-discovery/"
            "argentum-guild-progression-helper-definition.private.json"
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/exchange/out/argentum-guild-progression-helper-definition.json"),
    )
    parser.add_argument("--max-symbol-occurrences", type=int, default=500)
    parser.add_argument("--max-definition-candidates", type=int, default=50)
    parser.add_argument("--max-definition-span-chars", type=int, default=131072)
    parser.add_argument("--private-context-chars", type=int, default=4096)
    args = parser.parse_args()

    receipt = inventory_guild_progression_helper_definition(
        callsite_review_path=args.callsite_review,
        public_callsite_path=args.public_callsite,
        private_callsite_path=args.private_callsite,
        public_recovery_path=args.public_recovery,
        private_recovery_path=args.private_recovery,
        raw_root=args.raw_root,
        private_output_path=args.private_output,
        receipt_output_path=args.output,
        max_symbol_occurrences=args.max_symbol_occurrences,
        max_definition_candidates=args.max_definition_candidates,
        max_definition_span_chars=args.max_definition_span_chars,
        private_context_chars=args.private_context_chars,
    )
    summary = receipt["summary"]
    print(
        "guild progression helper-definition inventory: "
        f"definitions={summary['definition_candidate_count']} "
        f"aliases={summary['alias_candidate_count']} "
        f"review_ready="
        f"{summary['ready_for_guild_progression_helper_definition_review']}"
    )
    print(f"definition kinds: {summary['definition_kinds']}")
    print(f"binding scopes: {summary['binding_scopes']}")
    print(f"marker classes: {summary['marker_classes']}")
    print(f"definition scan truncated: {summary['definition_candidate_scan_truncated']}")
    print(f"private output: {args.private_output}")
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
