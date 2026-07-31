from __future__ import annotations

import argparse
from pathlib import Path

from coa_workbench.collector.guild_identity_decision import decide_guild_identity


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Explicitly promote the bound Argentum cross-endpoint identity after "
            "revalidating the public/private manifest, snapshot review and guild-search "
            "mapping chain. This enables deterministic guild filtering only; full crawl "
            "and planner scoring remain disabled."
        )
    )
    parser.add_argument(
        "--public-manifest",
        type=Path,
        default=Path("evidence/real-data/argentum-public-report-manifest.json"),
    )
    parser.add_argument(
        "--private-manifest",
        type=Path,
        default=Path(
            "data/extracted/report-discovery/argentum-public-report-manifest.private.json"
        ),
    )
    parser.add_argument(
        "--public-snapshot-review",
        type=Path,
        default=Path(
            "evidence/real-data/argentum-guild-identity-snapshot-review.json"
        ),
    )
    parser.add_argument(
        "--private-snapshot-review",
        type=Path,
        default=Path(
            "data/extracted/report-discovery/argentum-guild-identity-review.private.json"
        ),
    )
    parser.add_argument(
        "--public-mapping-review",
        type=Path,
        default=Path(
            "evidence/real-data/argentum-guild-search-mapping-review.json"
        ),
    )
    parser.add_argument(
        "--private-mapping-review",
        type=Path,
        default=Path(
            "data/extracted/report-discovery/argentum-guild-search-mapping-review.private.json"
        ),
    )
    parser.add_argument(
        "--private-output",
        type=Path,
        default=Path(
            "data/extracted/report-discovery/argentum-guild-identity-decision.private.json"
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/exchange/out/argentum-guild-identity-decision.json"),
    )
    parser.add_argument("--guild-label", default="Argentum")
    parser.add_argument(
        "--promote-identity",
        action="store_true",
        help=(
            "Record the operator's explicit decision to promote the fully bound "
            "cross-endpoint identity candidate."
        ),
    )
    args = parser.parse_args()

    if not args.promote_identity:
        parser.error("--promote-identity is required for an identity decision")

    receipt = decide_guild_identity(
        public_manifest_path=args.public_manifest,
        private_manifest_path=args.private_manifest,
        public_snapshot_review_path=args.public_snapshot_review,
        private_snapshot_review_path=args.private_snapshot_review,
        public_mapping_review_path=args.public_mapping_review,
        private_mapping_review_path=args.private_mapping_review,
        private_output_path=args.private_output,
        receipt_output_path=args.output,
        promote_identity=args.promote_identity,
        expected_guild_label=args.guild_label,
    )
    evidence = receipt["evidence_summary"]
    boundary = receipt["decision_boundary"]
    print(
        "guild identity decision: "
        f"snapshot_exact_matches={evidence['snapshot_exact_label_report_count']} "
        f"search_results={evidence['guild_search_result_count']} "
        f"source_id_equal={evidence['cross_endpoint_source_id_equal']} "
        f"identity_verified={boundary['guild_identity_verified']}"
    )
    print(f"private output: {args.private_output}")
    print(f"receipt output: {args.output}")
    print(f"ready for guild filtering: {boundary['ready_for_guild_filtering']}")
    print("ready for full guild crawl: false")
    print("planner scoring allowed: false")
    return 0 if boundary["guild_identity_verified"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
