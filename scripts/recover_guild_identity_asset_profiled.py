from __future__ import annotations

import argparse
from pathlib import Path

from coa_workbench.collector import RawArchive, load_source_registry
from coa_workbench.collector.guild_identity_asset_profiled_recovery import (
    recover_guild_identity_asset_profiled,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Recover the guild SPA asset with the exact transport profile selected by "
            "the scalar-free diagnostic. This does not verify guild identity or enable "
            "filtering."
        )
    )
    parser.add_argument(
        "--transport-diagnostic-receipt",
        type=Path,
        default=Path(
            "data/exchange/out/argentum-guild-asset-transport-diagnostic.json"
        ),
    )
    parser.add_argument(
        "--transport-diagnostic-private",
        type=Path,
        default=Path(
            "data/extracted/report-discovery/argentum-guild-asset-transport-diagnostic.private.json"
        ),
    )
    parser.add_argument(
        "--asset-recovery-receipt",
        type=Path,
        default=Path(
            "evidence/real-data/argentum-guild-asset-recovery-tls-failure.json"
        ),
    )
    parser.add_argument(
        "--asset-recovery-private",
        type=Path,
        default=Path(
            "data/extracted/report-discovery/argentum-guild-asset-recovery.private.json"
        ),
    )
    parser.add_argument(
        "--route-discovery-receipt",
        type=Path,
        default=Path(
            "evidence/real-data/argentum-guild-route-discovery-timeout.json"
        ),
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
            "data/extracted/report-discovery/argentum-guild-asset-profiled-recovery.private.json"
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "data/exchange/out/argentum-guild-asset-profiled-recovery.json"
        ),
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
    receipt = recover_guild_identity_asset_profiled(
        registry,
        archive,
        public_diagnostic_path=args.transport_diagnostic_receipt,
        private_diagnostic_path=args.transport_diagnostic_private,
        public_recovery_path=args.asset_recovery_receipt,
        private_recovery_path=args.asset_recovery_private,
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
        "profiled guild asset recovery: "
        f"profile={transport['profile']} "
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
    print(
        "ready for guild API route review: "
        f"{boundary['ready_for_guild_api_route_review']}"
    )
    print("guild identity verified: false")
    print("ready for guild filtering: false")
    return 0 if boundary["ready_for_guild_api_route_review"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
