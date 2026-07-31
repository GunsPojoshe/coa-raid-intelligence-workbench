from __future__ import annotations

import argparse
from pathlib import Path

from coa_workbench.collector.guild_identity_review import review_guild_identity_snapshot


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Review the private exhaustive public-report manifest for snapshot-internal guild "
            "identity consistency. This does not verify independent guild identity and never "
            "enables guild filtering or planner scoring."
        )
    )
    parser.add_argument(
        "--private-manifest",
        type=Path,
        default=Path(
            "data/extracted/report-discovery/argentum-public-report-manifest.private.json"
        ),
    )
    parser.add_argument(
        "--manifest-receipt",
        type=Path,
        default=Path("evidence/real-data/argentum-public-report-manifest.json"),
    )
    parser.add_argument(
        "--private-output",
        type=Path,
        default=Path(
            "data/extracted/report-discovery/argentum-guild-identity-review.private.json"
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/exchange/out/argentum-guild-identity-review.json"),
    )
    parser.add_argument("--guild-label", default="Argentum")
    args = parser.parse_args()

    receipt = review_guild_identity_snapshot(
        private_manifest_path=args.private_manifest,
        public_manifest_receipt_path=args.manifest_receipt,
        private_output_path=args.private_output,
        receipt_output_path=args.output,
        expected_guild_label=args.guild_label,
    )
    summary = receipt["summary"]
    boundary = receipt["decision_boundary"]
    print(
        "guild identity snapshot review: "
        f"exact_matches={summary['exact_label_report_count']} "
        f"distinct_ids={summary['distinct_exact_label_guild_id_count']} "
        f"conflicting_names={summary['candidate_guild_id_conflicting_non_empty_name_count']} "
        f"snapshot_consistent={boundary['snapshot_internal_identity_consistent']}"
    )
    print(f"private output: {args.private_output}")
    print(f"receipt output: {args.output}")
    print("guild identity verified: false")
    print("ready for guild filtering: false")
    return 0 if boundary["snapshot_internal_identity_consistent"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
