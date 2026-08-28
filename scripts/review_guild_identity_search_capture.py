from __future__ import annotations

import argparse
from pathlib import Path

from coa_workbench.collector.guild_identity_search_capture_review import (
    review_guild_identity_search_capture,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Review the already archived spa-fetch-context guild search response without "
            "network access. This does not verify guild identity or enable filtering."
        )
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
            "data/extracted/report-discovery/argentum-guild-search-capture-review.private.json"
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/exchange/out/argentum-guild-search-capture-review.json"),
    )
    parser.add_argument("--guild-label", default="Argentum")
    args = parser.parse_args()

    receipt = review_guild_identity_search_capture(
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
        "guild search capture review: "
        f"route_shape_candidate={summary['route_shape_candidate']} "
        f"exact_label_objects={summary['exact_label_object_count']} "
        f"source_id_matches={summary['source_id_match_object_count']} "
        f"one_to_one_candidate={summary['one_to_one_identity_candidate']}"
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
