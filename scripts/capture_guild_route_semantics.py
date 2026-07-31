from __future__ import annotations

import argparse
from pathlib import Path

from coa_workbench.collector import RawArchive, load_source_registry
from coa_workbench.collector.guild_route_semantics_capture import (
    capture_guild_route_semantics,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Capture three bounded variants of the reviewed guild-search route. "
            "The output is a scalar-free review receipt and does not promote route "
            "semantics or enable a full guild crawl."
        )
    )
    parser.add_argument(
        "--full-crawl-contract",
        type=Path,
        default=Path("evidence/real-data/argentum-guild-full-crawl-contract.json"),
    )
    parser.add_argument(
        "--access-diagnostic",
        type=Path,
        default=Path("evidence/real-data/argentum-guild-search-access-spa-context.json"),
    )
    parser.add_argument(
        "--private-access-diagnostic",
        type=Path,
        default=Path(
            "data/extracted/report-discovery/argentum-guild-search-access-diagnostic.private.json"
        ),
    )
    parser.add_argument(
        "--private-output",
        type=Path,
        default=Path(
            "data/extracted/report-discovery/argentum-guild-route-semantics-capture.private.json"
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/exchange/out/argentum-guild-route-semantics-capture.json"),
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
    parser.add_argument("--timeout-seconds", type=float, default=60.0)
    parser.add_argument("--max-bytes", type=int, default=256 * 1024)
    args = parser.parse_args()

    registry = load_source_registry(args.registry)
    archive = RawArchive(
        args.raw_root,
        database_path=args.database,
        migrations_dir=args.migrations,
    )
    receipt = capture_guild_route_semantics(
        registry,
        archive,
        full_crawl_contract_path=args.full_crawl_contract,
        public_access_diagnostic_path=args.access_diagnostic,
        private_access_diagnostic_path=args.private_access_diagnostic,
        private_output_path=args.private_output,
        receipt_output_path=args.output,
        expected_guild_label=args.guild_label,
        curl_executable=args.curl_executable,
        timeout_seconds=args.timeout_seconds,
        max_bytes=args.max_bytes,
    )

    summary = receipt["summary"]
    boundary = receipt["decision_boundary"]
    print(
        "guild route semantics capture: "
        f"attempts={summary['attempt_count']} "
        f"completed={summary['completed_attempt_count']} "
        f"shape_consistent={summary['response_shape_consistent']} "
        f"review_ready={summary['ready_for_route_semantics_review']}"
    )
    print(f"private output: {args.private_output}")
    print(f"receipt output: {args.output}")
    print(
        "guild API route semantics verified: "
        f"{boundary['guild_api_route_semantics_verified']}"
    )
    print(f"ready for full guild crawl: {boundary['ready_for_full_guild_crawl']}")
    print(f"planner scoring allowed: {boundary['planner_scoring_allowed']}")
    return 0 if boundary["ready_for_route_semantics_review"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
