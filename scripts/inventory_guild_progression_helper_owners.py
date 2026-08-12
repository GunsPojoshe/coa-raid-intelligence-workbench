from __future__ import annotations

import argparse
from pathlib import Path

from coa_workbench.collector.guild_progression_helper_owner_inventory import (
    inventory_guild_progression_helper_owners,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Inventory bounded lexical helper-owner candidates for "
            "/api/guilds/progression from the exact archived SPA asset."
        )
    )
    parser.add_argument(
        "--reference-review",
        type=Path,
        default=Path("evidence/real-data/argentum-guild-progression-helper-reference-review.json"),
    )
    parser.add_argument(
        "--public-reference-inventory",
        type=Path,
        default=Path("evidence/real-data/argentum-guild-progression-helper-reference.json"),
    )
    parser.add_argument(
        "--private-reference-inventory",
        type=Path,
        default=Path(
            "data/extracted/report-discovery/"
            "argentum-guild-progression-helper-reference.private.json"
        ),
    )
    parser.add_argument("--raw-root", type=Path, default=Path("data/raw"))
    parser.add_argument(
        "--private-output",
        type=Path,
        default=Path(
            "data/extracted/report-discovery/argentum-guild-progression-helper-owner.private.json"
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/exchange/out/argentum-guild-progression-helper-owner.json"),
    )
    parser.add_argument("--max-owner-prefix-chars", type=int, default=512)
    parser.add_argument("--max-definition-container-chars", type=int, default=2048)
    args = parser.parse_args()

    receipt = inventory_guild_progression_helper_owners(
        reference_review_path=args.reference_review,
        public_reference_inventory_path=args.public_reference_inventory,
        private_reference_inventory_path=args.private_reference_inventory,
        raw_root=args.raw_root,
        private_output_path=args.private_output,
        receipt_output_path=args.output,
        max_owner_prefix_chars=args.max_owner_prefix_chars,
        max_definition_container_chars=args.max_definition_container_chars,
    )
    summary = receipt["summary"]
    print(
        "guild progression helper-owner inventory: "
        f"candidates={summary['owner_candidate_occurrence_count']} "
        f"groups={summary['unique_owner_group_count']} "
        "cross_definition_reference_groups="
        f"{summary['cross_definition_reference_owner_group_count']}"
    )
    print(f"owner candidate classes: {summary['owner_candidate_source_classes']}")
    print(f"definition owner candidates: {summary['definition_owner_candidate_occurrence_count']}")
    print(
        "references without owner candidates: "
        f"{summary['references_without_owner_candidate_count']}"
    )
    print(
        "ready for helper-owner review: "
        f"{summary['ready_for_guild_progression_helper_owner_review']}"
    )
    print(f"private output: {args.private_output}")
    print(f"receipt output: {args.output}")
    print(f"helper owner binding resolved: {summary['helper_owner_binding_resolved']}")
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
