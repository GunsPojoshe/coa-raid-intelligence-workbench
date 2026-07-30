from __future__ import annotations

import argparse
from pathlib import Path

from coa_workbench.collector import (
    RawArchive,
    capture_report_pagination_terminal_search,
    load_source_registry,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Find and verify the adjacent hasMore transition inside a reviewed public-report "
            "pagination bracket without crawling the full manifest."
        )
    )
    parser.add_argument(
        "--boundary-receipt",
        type=Path,
        default=Path("data/exchange/out/argentum-report-pagination-boundary-probe.json"),
    )
    parser.add_argument(
        "--boundary-private",
        type=Path,
        default=Path(
            "data/extracted/report-discovery/"
            "argentum-report-pagination-boundary-probe.private.json"
        ),
    )
    parser.add_argument("--guild-label", default="Argentum")
    parser.add_argument("--max-requests", type=int, default=16)
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
    parser.add_argument("--timeout-seconds", type=float, default=20.0)
    parser.add_argument("--retry-count", type=int, choices=(0, 1), default=1)
    parser.add_argument(
        "--private-output",
        type=Path,
        default=Path(
            "data/extracted/report-discovery/"
            "argentum-report-pagination-terminal-search.private.json"
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/exchange/out/argentum-report-pagination-terminal-search.json"),
    )
    args = parser.parse_args()

    registry = load_source_registry(args.registry)
    archive = RawArchive(
        args.raw_root,
        database_path=args.database,
        migrations_dir=args.migrations,
    )
    receipt = capture_report_pagination_terminal_search(
        registry,
        archive,
        boundary_receipt_path=args.boundary_receipt,
        boundary_private_path=args.boundary_private,
        private_output_path=args.private_output,
        receipt_output_path=args.output,
        expected_guild_label=args.guild_label,
        max_requests=args.max_requests,
        timeout_seconds=args.timeout_seconds,
        retry_count=args.retry_count,
    )

    summary = receipt["summary"]
    print(
        "pagination terminal search: "
        f"requests={summary['completed_request_count']} "
        f"terminal_page={summary['terminal_page']} "
        f"terminal_reports={summary['terminal_page_report_count']}"
    )
    print(f"private output: {args.private_output}")
    print(f"receipt output: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
