from __future__ import annotations

import argparse
from pathlib import Path

from coa_workbench.collector import RawArchive, load_source_registry
from coa_workbench.collector.guild_identity_route_discovery import (
    discover_guild_identity_route_candidates,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Capture the candidate guild UI page and inventory scalar-free guild API route "
            "shapes. This discovery does not verify guild identity or enable filtering."
        )
    )
    parser.add_argument(
        "--snapshot-review-receipt",
        type=Path,
        default=Path("evidence/real-data/argentum-guild-identity-snapshot-review.json"),
    )
    parser.add_argument(
        "--snapshot-private-review",
        type=Path,
        default=Path("data/extracted/report-discovery/argentum-guild-identity-review.private.json"),
    )
    parser.add_argument(
        "--private-output",
        type=Path,
        default=Path("data/extracted/report-discovery/argentum-guild-route-discovery.private.json"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/exchange/out/argentum-guild-route-discovery.json"),
    )
    parser.add_argument(
        "--registry",
        type=Path,
        default=Path("config/ascension_logs_sources.yaml"),
    )
    parser.add_argument("--raw-root", type=Path, default=Path("data/raw"))
    parser.add_argument(
        "--database",
        type=Path,
        default=Path("data/warehouse/coa.duckdb"),
    )
    parser.add_argument("--migrations", type=Path, default=Path("migrations"))
    parser.add_argument("--guild-label", default="Argentum")
    parser.add_argument("--timeout-seconds", type=float, default=30.0)
    args = parser.parse_args()

    registry = load_source_registry(args.registry)
    archive = RawArchive(
        args.raw_root,
        database_path=args.database,
        migrations_dir=args.migrations,
    )
    receipt = discover_guild_identity_route_candidates(
        registry,
        archive,
        public_snapshot_review_path=args.snapshot_review_receipt,
        private_snapshot_review_path=args.snapshot_private_review,
        private_output_path=args.private_output,
        receipt_output_path=args.output,
        expected_guild_label=args.guild_label,
        timeout_seconds=args.timeout_seconds,
    )

    summary = receipt["summary"]
    inventory = receipt["route_inventory"]
    failures = receipt["asset_failure_summary"]
    boundary = receipt["decision_boundary"]
    print(
        "guild identity route discovery: "
        f"page_completed={summary['page_capture_completed']} "
        f"assets_captured={summary['captured_asset_count']}/{summary['asset_count']} "
        f"api_routes={summary['api_route_candidate_count']} "
        f"guild_routes={inventory['guild_api_route_shape_count']}"
    )
    print(f"route candidate sources: {inventory['candidate_source_counts']}")
    print(f"asset failure classes: {failures['failure_class_counts']}")
    print(f"private output: {args.private_output}")
    print(f"receipt output: {args.output}")
    print(f"ready for guild API route review: {boundary['ready_for_guild_api_route_review']}")
    print("guild identity verified: false")
    print("ready for guild filtering: false")
    return 0 if boundary["ready_for_guild_api_route_review"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
