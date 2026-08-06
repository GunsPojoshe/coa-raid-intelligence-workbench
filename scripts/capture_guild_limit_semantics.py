from __future__ import annotations

import argparse
from pathlib import Path

from coa_workbench.collector import RawArchive, load_source_registry
from coa_workbench.collector.guild_limit_semantics_capture import (
    capture_guild_limit_semantics,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Capture a bounded multi-result guild-search limit comparison. "
            "The query remains private and the public receipt does not promote "
            "limit semantics or enable a full guild crawl."
        )
    )
    parser.add_argument(
        "--route-review",
        type=Path,
        default=Path("evidence/real-data/argentum-guild-route-semantics-review.json"),
    )
    parser.add_argument("--query", required=True)
    parser.add_argument("--low-limit", type=int, default=1)
    parser.add_argument("--high-limit", type=int, default=25)
    parser.add_argument(
        "--private-output",
        type=Path,
        default=Path(
            "data/extracted/report-discovery/argentum-guild-limit-semantics-capture.private.json"
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/exchange/out/argentum-guild-limit-semantics-capture.json"),
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
    receipt = capture_guild_limit_semantics(
        registry,
        archive,
        route_review_path=args.route_review,
        query=args.query,
        low_limit=args.low_limit,
        high_limit=args.high_limit,
        private_output_path=args.private_output,
        receipt_output_path=args.output,
        curl_executable=args.curl_executable,
        timeout_seconds=args.timeout_seconds,
        max_bytes=args.max_bytes,
    )

    summary = receipt["summary"]
    boundary = receipt["decision_boundary"]
    print(
        "guild limit semantics capture: "
        f"attempts={summary['attempt_count']} "
        f"completed={summary['completed_attempt_count']} "
        f"multi_result={summary['multi_result_observed']} "
        f"review_ready={summary['ready_for_limit_semantics_review']}"
    )
    print(f"private output: {args.private_output}")
    print(f"receipt output: {args.output}")
    print(f"limit truncation semantics verified: {boundary['limit_truncation_semantics_verified']}")
    print(f"ready for full guild crawl: {boundary['ready_for_full_guild_crawl']}")
    print(f"planner scoring allowed: {boundary['planner_scoring_allowed']}")
    return 0 if boundary["ready_for_limit_semantics_review"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
