from __future__ import annotations

import argparse
from pathlib import Path

from coa_workbench.collector.guild_progression_helper_reference_inventory import (
    inventory_guild_progression_helper_references,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Inventory bounded full-chain and terminal-symbol helper references for "
            "/api/guilds/progression from the exact archived SPA asset."
        )
    )
    parser.add_argument(
        "--definition-review",
        type=Path,
        default=Path("evidence/real-data/argentum-guild-progression-helper-definition-review.json"),
    )
    parser.add_argument(
        "--public-definition-inventory",
        type=Path,
        default=Path("evidence/real-data/argentum-guild-progression-helper-definition.json"),
    )
    parser.add_argument(
        "--private-definition-inventory",
        type=Path,
        default=Path(
            "data/extracted/report-discovery/"
            "argentum-guild-progression-helper-definition.private.json"
        ),
    )
    parser.add_argument("--raw-root", type=Path, default=Path("data/raw"))
    parser.add_argument(
        "--private-output",
        type=Path,
        default=Path(
            "data/extracted/report-discovery/"
            "argentum-guild-progression-helper-reference.private.json"
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/exchange/out/argentum-guild-progression-helper-reference.json"),
    )
    parser.add_argument("--max-symbol-occurrences", type=int, default=500)
    parser.add_argument("--max-reference-candidates", type=int, default=500)
    parser.add_argument("--private-context-chars", type=int, default=1024)
    args = parser.parse_args()

    receipt = inventory_guild_progression_helper_references(
        definition_review_path=args.definition_review,
        public_definition_inventory_path=args.public_definition_inventory,
        private_definition_inventory_path=args.private_definition_inventory,
        raw_root=args.raw_root,
        private_output_path=args.private_output,
        receipt_output_path=args.output,
        max_symbol_occurrences=args.max_symbol_occurrences,
        max_reference_candidates=args.max_reference_candidates,
        private_context_chars=args.private_context_chars,
    )
    summary = receipt["summary"]
    print(
        "guild progression helper-reference inventory: "
        f"references={summary['unique_reference_candidate_count']} "
        f"full_chain={summary['full_chain_occurrence_count_observed']} "
        f"terminal={summary['terminal_symbol_occurrence_count_observed']}"
    )
    print(f"reference kinds: {summary['reference_kinds']}")
    print(f"symbol scopes: {summary['symbol_scopes']}")
    print(f"transport markers: {summary['direct_transport_marker_classes']}")
    print(f"request-shape markers: {summary['request_shape_marker_classes']}")
    print(
        "ready for helper-reference review: "
        f"{summary['ready_for_guild_progression_helper_reference_review']}"
    )
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
