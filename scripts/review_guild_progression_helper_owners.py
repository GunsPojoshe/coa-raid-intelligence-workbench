from __future__ import annotations

import argparse
from pathlib import Path

from coa_workbench.collector.guild_progression_helper_owner_review import (
    review_guild_progression_helper_owners,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Review helper-owner relationships for /api/guilds/progression without "
            "publishing owner scalars or enabling a route probe."
        )
    )
    parser.add_argument(
        "--inventory",
        type=Path,
        default=Path("evidence/real-data/argentum-guild-progression-helper-owner.json"),
    )
    parser.add_argument(
        "--private-inventory",
        type=Path,
        default=Path(
            "data/extracted/report-discovery/argentum-guild-progression-helper-owner.private.json"
        ),
    )
    parser.add_argument(
        "--reference-review",
        type=Path,
        default=Path("evidence/real-data/argentum-guild-progression-helper-reference-review.json"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/exchange/out/argentum-guild-progression-helper-owner-review.json"),
    )
    args = parser.parse_args()

    receipt = review_guild_progression_helper_owners(
        inventory_path=args.inventory,
        private_inventory_path=args.private_inventory,
        reference_review_path=args.reference_review,
        receipt_output_path=args.output,
    )
    summary = receipt["summary"]
    review = receipt["owner_binding_review"]
    print(
        "guild progression helper-owner review: "
        f"candidates={summary['owner_candidate_count']} "
        f"groups={summary['owner_group_count']} "
        f"disposition={summary['owner_review_disposition']}"
    )
    print(f"full-chain owner group: {summary['full_chain_owner_group_index']}")
    print(f"definition owner group: {summary['definition_owner_group_index']}")
    print(
        f"full-chain/definition owner match: {summary['full_chain_definition_owner_group_match']}"
    )
    print(
        "definition-owner non-definition invocations: "
        f"{review['definition_owner_group_non_definition_invocation_count']}"
    )
    print(f"blockers: {review['blockers']}")
    print(f"helper owner binding resolved: {summary['helper_owner_binding_resolved']}")
    print(
        "ready for owner-relationship inventory: "
        f"{summary['ready_for_guild_progression_helper_owner_relationship_inventory']}"
    )
    print(f"receipt output: {args.output}")
    print(
        "ready for bounded progression route probe: "
        f"{summary['ready_for_bounded_progression_route_probe']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
