from __future__ import annotations

import argparse
from pathlib import Path

from coa_workbench.collector.guild_identity_search_mapping_review import (
    review_guild_identity_search_mapping,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Review the already inventoried guild-search field mapping without network "
            "access or publishing source scalar values."
        )
    )
    parser.add_argument(
        "--inventory-receipt",
        type=Path,
        default=Path("evidence/real-data/argentum-guild-search-schema-inventory.json"),
    )
    parser.add_argument(
        "--inventory-private",
        type=Path,
        default=Path(
            "data/extracted/report-discovery/argentum-guild-search-schema-inventory.private.json"
        ),
    )
    parser.add_argument(
        "--private-output",
        type=Path,
        default=Path(
            "data/extracted/report-discovery/argentum-guild-search-mapping-review.private.json"
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/exchange/out/argentum-guild-search-mapping-review.json"),
    )
    parser.add_argument("--guild-label", default="Argentum")
    args = parser.parse_args()

    receipt = review_guild_identity_search_mapping(
        public_inventory_path=args.inventory_receipt,
        private_inventory_path=args.inventory_private,
        private_output_path=args.private_output,
        receipt_output_path=args.output,
        expected_guild_label=args.guild_label,
    )
    summary = receipt["summary"]
    boundary = receipt["decision_boundary"]
    evidence = receipt["evidence_summary"]
    print(
        "guild search mapping review: "
        f"mapped_fields={summary['mapped_field_count']} "
        f"source_id_matches={evidence['guild_id_source_candidate_match_count']} "
        f"casefold_label_matches={evidence['guild_name_casefold_match_count']} "
        f"cross_endpoint_candidate={evidence['cross_endpoint_identity_candidate_observed']}"
    )
    print(f"private output: {args.private_output}")
    print(f"receipt output: {args.output}")
    print(
        "ready for guild identity decision review: "
        f"{boundary['ready_for_guild_identity_decision_review']}"
    )
    print("guild identity verified: false")
    print("ready for guild filtering: false")
    return 0 if boundary["ready_for_guild_identity_decision_review"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
