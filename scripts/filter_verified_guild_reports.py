from __future__ import annotations

import argparse
from pathlib import Path

from coa_workbench.collector.verified_guild_report_filter import (
    filter_verified_guild_reports,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Filter the exhaustive private public-report manifest by the source guild ID "
            "stored in the verified private identity decision. The public receipt remains "
            "scalar-free and does not enable full guild crawl or planner scoring."
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
        "--public-identity-decision",
        type=Path,
        default=Path("evidence/real-data/argentum-guild-identity-decision.json"),
    )
    parser.add_argument(
        "--private-identity-decision",
        type=Path,
        default=Path(
            "data/extracted/report-discovery/argentum-guild-identity-decision.private.json"
        ),
    )
    parser.add_argument(
        "--private-output",
        type=Path,
        default=Path("data/extracted/report-discovery/argentum-guild-report-manifest.private.json"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/exchange/out/argentum-guild-report-manifest.json"),
    )
    parser.add_argument("--guild-label", default="Argentum")
    args = parser.parse_args()

    receipt = filter_verified_guild_reports(
        public_manifest_path=args.public_manifest,
        private_manifest_path=args.private_manifest,
        public_identity_decision_path=args.public_identity_decision,
        private_identity_decision_path=args.private_identity_decision,
        private_output_path=args.private_output,
        receipt_output_path=args.output,
        expected_guild_label=args.guild_label,
    )
    summary = receipt["summary"]
    boundary = receipt["decision_boundary"]
    print(
        "verified guild report filter: "
        f"source_reports={summary['source_report_count']} "
        f"selected_reports={summary['selected_report_count']} "
        f"unique_selected={summary['unique_selected_report_id_count']}"
    )
    print(f"private output: {args.private_output}")
    print(f"receipt output: {args.output}")
    print(f"guild filtering completed: {boundary['guild_filtering_completed']}")
    print("ready for full guild crawl: false")
    print("planner scoring allowed: false")
    return 0 if boundary["guild_filtering_completed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
