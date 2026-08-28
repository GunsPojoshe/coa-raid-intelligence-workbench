from __future__ import annotations

import argparse
from pathlib import Path

from coa_workbench.collector.guild_identity_search_schema_inventory import (
    inventory_guild_identity_search_schema,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Inventory the already archived guild-search object without network access or "
            "publishing scalar values. This does not verify guild identity."
        )
    )
    parser.add_argument(
        "--capture-review-receipt",
        type=Path,
        default=Path(
            "evidence/real-data/argentum-guild-search-capture-review-no-label-fields.json"
        ),
    )
    parser.add_argument(
        "--capture-review-private",
        type=Path,
        default=Path(
            "data/extracted/report-discovery/argentum-guild-search-capture-review.private.json"
        ),
    )
    parser.add_argument(
        "--access-diagnostic-receipt",
        type=Path,
        default=Path("evidence/real-data/argentum-guild-search-access-spa-context.json"),
    )
    parser.add_argument(
        "--access-diagnostic-private",
        type=Path,
        default=Path(
            "data/extracted/report-discovery/argentum-guild-search-access-diagnostic.private.json"
        ),
    )
    parser.add_argument(
        "--search-probe-private",
        type=Path,
        default=Path("data/extracted/report-discovery/argentum-guild-search-probe.private.json"),
    )
    parser.add_argument("--raw-root", type=Path, default=Path("data/raw"))
    parser.add_argument(
        "--private-output",
        type=Path,
        default=Path(
            "data/extracted/report-discovery/argentum-guild-search-schema-inventory.private.json"
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/exchange/out/argentum-guild-search-schema-inventory.json"),
    )
    parser.add_argument("--guild-label", default="Argentum")
    args = parser.parse_args()

    receipt = inventory_guild_identity_search_schema(
        public_capture_review_path=args.capture_review_receipt,
        private_capture_review_path=args.capture_review_private,
        public_access_diagnostic_path=args.access_diagnostic_receipt,
        private_access_diagnostic_path=args.access_diagnostic_private,
        private_search_probe_path=args.search_probe_private,
        raw_root=args.raw_root,
        private_output_path=args.private_output,
        receipt_output_path=args.output,
        expected_guild_label=args.guild_label,
    )
    summary = receipt["summary"]
    boundary = receipt["decision_boundary"]
    print(
        "guild search schema inventory: "
        f"guild_objects={summary['guild_object_count']} "
        f"field_entries={summary['distinct_field_entry_count']} "
        f"exact_label_matches={summary['exact_label_match_count']} "
        f"casefold_label_matches={summary['casefold_label_match_count']} "
        f"contains_label_matches={summary['contains_label_casefold_count']} "
        f"source_id_matches={summary['source_id_match_count']}"
    )
    print(f"private output: {args.private_output}")
    print(f"receipt output: {args.output}")
    print(
        "ready for guild search mapping review: "
        f"{boundary['ready_for_guild_search_mapping_review']}"
    )
    print("guild identity verified: false")
    print("ready for guild filtering: false")
    return 0 if boundary["ready_for_guild_search_mapping_review"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
