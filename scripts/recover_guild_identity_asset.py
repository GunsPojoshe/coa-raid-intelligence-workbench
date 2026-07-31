from __future__ import annotations

import argparse
from pathlib import Path

from coa_workbench.collector import RawArchive, load_source_registry
from coa_workbench.collector.guild_identity_asset_recovery import (
    recover_guild_identity_asset,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Recover one timed-out same-origin guild SPA asset through bounded curl transport. "
            "This does not verify guild identity or enable filtering."
        )
    )
    parser.add_argument(
        "--route-discovery-receipt",
        type=Path,
        default=Path("evidence/real-data/argentum-guild-route-discovery-timeout.json"),
    )
    parser.add_argument(
        "--route-discovery-private",
        type=Path,
        default=Path(
            "data/extracted/report-discovery/argentum-guild-route-discovery.private.json"
        ),
    )
    parser.add_argument(
        "--private-output",
        type=Path,
        default=Path(
            "data/extracted/report-discovery/argentum-guild-asset-recovery.private.json"
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/exchange/out/argentum-guild-asset-recovery.json"),
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
    parser.add_argument("--curl-executable")
    parser.add_argument("--timeout-seconds", type=float, default=300.0)
    parser.add_argument("--max-bytes", type=int, default=64 * 1024 * 1024)
    args = parser.parse_args()

    registry = load_source_registry(args.registry)
    archive = RawArchive(
        args.raw_root,
        database_path=args.database,
        migrations_dir=args.migrations,
    )
    receipt = recover_guild_identity_asset(
        registry,
        archive,
        public_route_discovery_path=args.route_discovery_receipt,
        private_route_discovery_path=args.route_discovery_private,
        private_output_path=args.private_output,
        receipt_output_path=args.output,
        expected_guild_label=args.guild_label,
        curl_executable=args.curl_executable,
        timeout_seconds=args.timeout_seconds,
        max_bytes=args.max_bytes,
    )

    summary = receipt["summary"]
    transport = receipt["transport"]
    inventory = receipt["route_inventory"]
    boundary = receipt["decision_boundary"]
    print(
        "guild asset recovery: "
        f"downloaded={summary['asset_download_completed']} "
        f"bytes={summary['asset_bytes']} "
        f"api_routes={summary['api_route_candidate_count']} "
        f"guild_routes={inventory['guild_api_route_shape_count']}"
    )
    print(
        "transport: "
        f"return_code={transport['return_code']} "
        f"http_status={transport['http_status']} "
        f"failure_class={transport['failure_class']}"
    )
    print(f"private output: {args.private_output}")
    print(f"receipt output: {args.output}")
    print(f"ready for guild API route review: {boundary['ready_for_guild_api_route_review']}")
    print("guild identity verified: false")
    print("ready for guild filtering: false")
    return 0 if boundary["ready_for_guild_api_route_review"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
